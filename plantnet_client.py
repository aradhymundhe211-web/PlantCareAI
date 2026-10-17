"""Optional Pl@ntNet API adapter for PlantCare AI.

Uses the existing requests and Pillow dependencies. The API key must be supplied
server-side through Streamlit secrets or the PLANTNET_API_KEY environment variable.
"""
from __future__ import annotations

import io
from typing import Any

import requests
from PIL import Image, ImageOps

API_URL = "https://my-api.plantnet.org/v2/identify/all"


def _norm_taxon(value: str) -> str:
    """Normalize a scientific name for conservative exact matching."""
    return " ".join(str(value or "").strip().casefold().replace("×", "x").split())


def identify_with_plantnet(image_bytes: bytes, plants: list[dict[str, Any]], api_key: str, timeout: int = 25) -> dict[str, Any]:
    """Identify a photo and map API results only to exact supported scientific names.

    Returns {ok, rows, message, top_external, raw_top_score}. Raises no HTTP errors
    to the UI: transport/API failures are represented as a readable message.
    """
    if not api_key.strip():
        return {"ok": False, "rows": [], "message": "Pl@ntNet API key is not configured.", "top_external": "", "raw_top_score": 0.0}
    try:
        with Image.open(io.BytesIO(image_bytes)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((1280, 1280))
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=90, optimize=True)
            buffer.seek(0)
        response = requests.post(
            API_URL,
            params={"api-key": api_key.strip(), "lang": "en", "nb-results": 10},
            data=[("organs", "auto")],
            files=[("images", ("plant.jpg", buffer.getvalue(), "image/jpeg"))],
            timeout=timeout,
        )
        if response.status_code == 404:
            return {"ok": True, "rows": [], "message": "Pl@ntNet did not return a plant species for this image.", "top_external": "", "raw_top_score": 0.0, "no_plant": True}
        if response.status_code == 429:
            return {"ok": False, "rows": [], "message": "Pl@ntNet daily quota/rate limit was reached. Local fallback will be used.", "top_external": "", "raw_top_score": 0.0}
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results") or []
        top_external = ""
        raw_top_score = 0.0
        if results:
            top_species = results[0].get("species") or {}
            top_external = top_species.get("scientificNameWithoutAuthor") or top_species.get("scientificName") or ""
            raw_top_score = float(results[0].get("score") or 0.0)
        by_taxon = {_norm_taxon(p.get("scientific_name", "")): p for p in plants}
        rows: list[tuple[dict[str, Any], float]] = []
        seen: set[str] = set()
        for result in results:
            species = result.get("species") or {}
            scientific = species.get("scientificNameWithoutAuthor") or species.get("scientificName") or ""
            plant = by_taxon.get(_norm_taxon(scientific))
            if plant is None:
                continue
            key = _norm_taxon(plant.get("scientific_name", ""))
            if key in seen:
                continue
            seen.add(key)
            rows.append((plant, max(0.0, min(1.0, float(result.get("score") or 0.0)))))
        rows.sort(key=lambda item: item[1], reverse=True)
        # Do not force a 56-class label when Pl@ntNet's leading result is an
        # unsupported species and the best supported match is much weaker.
        if rows and raw_top_score > 0 and rows[0][1] < raw_top_score * 0.50:
            rows = []
        return {"ok": True, "rows": rows, "message": "Pl@ntNet API identification completed.", "top_external": top_external, "raw_top_score": raw_top_score, "no_plant": False}
    except requests.Timeout:
        return {"ok": False, "rows": [], "message": "Pl@ntNet timed out. Local fallback will be used.", "top_external": "", "raw_top_score": 0.0}
    except requests.RequestException as exc:
        return {"ok": False, "rows": [], "message": f"Pl@ntNet request failed ({type(exc).__name__}). Local fallback will be used.", "top_external": "", "raw_top_score": 0.0}
    except (ValueError, OSError, TypeError) as exc:
        return {"ok": False, "rows": [], "message": f"Pl@ntNet response/image processing failed ({type(exc).__name__}). Local fallback will be used.", "top_external": "", "raw_top_score": 0.0}
