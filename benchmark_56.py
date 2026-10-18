#!/usr/bin/env python3
"""Held-out real-photo benchmark for the 56 PlantCare AI species.

Run locally (not on Streamlit Community Cloud):
    python benchmark_56.py --per-class 2

Downloads research-grade iNaturalist observation photos by exact scientific taxon,
runs the same BioCLIP prompt/prototype ranking approach as app.py, and writes
benchmark_results.csv plus per-class top-1/top-3 metrics. This is a species-ranker
benchmark, not a test of Streamlit UI or the app's non-plant rejection gates.
The results depend on the downloaded sample and are not a universal accuracy claim.
"""
from __future__ import annotations

import argparse
import ast
import csv
import io
import json
import re
import time
from pathlib import Path

import numpy as np
import requests
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "plant_data.json"
APP_PATH = ROOT / "app.py"
CACHE = ROOT / ".plantcare_benchmark_cache"
API = "https://api.inaturalist.org/v1"
HEADERS = {"User-Agent": "PlantCareAI-56-species-benchmark/1.0 (educational project)"}


def load_hints():
    tree = ast.parse(APP_PATH.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "MODEL_HINTS" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError("MODEL_HINTS was not found in app.py")


def request_json(url, params=None):
    response = requests.get(url, params=params, headers=HEADERS, timeout=25)
    response.raise_for_status()
    return response.json()


def exact_taxon(scientific_name):
    data = request_json(f"{API}/taxa", {"q": scientific_name, "per_page": 30, "order_by": "observations_count"})
    for taxon in data.get("results", []):
        if str(taxon.get("name", "")).casefold() == scientific_name.casefold():
            return taxon
    return None


def medium_url(url):
    return re.sub(r"/(?:square|small|thumb|large|original)\.", "/medium.", url)


def image_bytes(url):
    CACHE.mkdir(parents=True, exist_ok=True)
    filename = CACHE / (str(abs(hash(url))) + ".jpg")
    if filename.exists():
        raw = filename.read_bytes()
    else:
        response = requests.get(medium_url(url), headers=HEADERS, timeout=25)
        response.raise_for_status()
        raw = response.content
        filename.write_bytes(raw)
    try:
        with Image.open(io.BytesIO(raw)) as im:
            im.verify()
        return raw
    except Exception:
        return None


def collect_samples(plant, count):
    taxon = exact_taxon(plant["scientific_name"])
    if not taxon:
        return [], "Exact iNaturalist taxon not found"
    data = request_json(
        f"{API}/observations",
        {
            "taxon_id": taxon["id"],
            "quality_grade": "research",
            "photos": "true",
            "per_page": min(200, max(30, count * 12)),
            "order_by": "observed_on",
            "order": "desc",
        },
    )
    samples, seen = [], set()
    for obs in data.get("results", []):
        obs_id = obs.get("id")
        if obs_id in seen:
            continue
        photos = obs.get("photos") or []
        if not photos:
            continue
        url = photos[0].get("url")
        if not url:
            continue
        seen.add(obs_id)
        try:
            raw = image_bytes(url)
            if raw:
                samples.append((obs_id, raw, url))
        except Exception:
            pass
        if len(samples) >= count:
            break
        time.sleep(0.05)
    return samples, "" if samples else "No downloadable research-grade photos found"


def focus_crop(img):
    im = ImageOps.exif_transpose(img).convert("RGB")
    small = im.copy()
    small.thumbnail((640, 640))
    a = np.asarray(small, dtype=np.float32) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(axis=2), a.min(axis=2)
    sat = np.divide(mx - mn, mx, out=np.zeros_like(mx), where=mx > 1e-6)
    mask = (((g > r * .96) & (g > b * 1.04) & (g > .14) & (sat > .10)) |
            ((r > .35) & (g > .30) & (b < .40) & (r > b * 1.12) & (sat > .16)) |
            ((r > .40) & (r > g * 1.18) & (r > b * 1.18) & (sat > .18)))
    ys, xs = np.where(mask)
    if len(xs) < max(80, int(mask.size * .006)):
        return None
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    pad = int(max(x1 - x0, y1 - y0) * .20) + 8
    x0, y0 = max(0, int(x0) - pad), max(0, int(y0) - pad)
    x1, y1 = min(small.width, int(x1) + pad), min(small.height, int(y1) + pad)
    if (x1 - x0) * (y1 - y0) < small.width * small.height * .04:
        return None
    return im.crop((int(x0 / small.width * im.width), int(y0 / small.height * im.height),
                    int(x1 / small.width * im.width), int(y1 / small.height * im.height)))


def analysis_views(img):
    im = ImageOps.exif_transpose(img).convert("RGB")
    im.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    views = [im]
    focus = focus_crop(im)
    if focus is not None:
        views.append(focus)
    w, h = im.size
    side = int(min(w, h) * .78)
    if side >= 160:
        left, top = max(0, (w - side) // 2), max(0, (h - side) // 2)
        views.append(im.crop((left, top, left + side, top + side)))
    if h > 220:
        views.append(im.crop((0, 0, w, int(h * .82))))
    return views[:3]


def prompts_for(plant, hint):
    common, scientific = plant["common_name"], plant["scientific_name"]
    prompts = [
        f"a real photograph of the whole living {common} plant, {scientific}",
        f"a botanical photograph showing the identifying leaves of {common}, {scientific}",
        f"a close-up photograph of the foliage and leaf arrangement of {common}, {scientific}",
        f"a field photograph of {scientific} growing naturally",
    ]
    if hint:
        prompts.extend([
            f"a real plant photo of {common}; visible traits: {hint}",
            f"identification photograph of {scientific}; {hint}",
        ])
    else:
        traits = ", ".join(str(plant.get(k, "")).strip() for k in ("leaf", "flower", "growth") if str(plant.get(k, "")).strip())
        prompts.append(f"a botanical identification photo of {common}; visible traits: {traits}")
    if common == "Tulsi":
        prompts.extend([
            "holy basil Ocimum tenuiflorum plant, opposite ovate leaves with toothed margins and slender basil flower spikes",
            "Tulsi holy basil growing in an Indian home garden, branching herb with green or purple stems and small opposite leaves",
            "close-up of holy basil Ocimum tenuiflorum foliage and flowering spikes, not mint",
            "Ocimum tenuiflorum botanical field photograph, basil leaf shape and upright flowering spikes",
        ])
    elif common == "Mint":
        prompts.extend([
            "spearmint Mentha spicata plant, opposite textured serrated leaves on spreading square stems",
            "close-up of spearmint foliage, wrinkled veined leaves and creeping or spreading herb growth, not holy basil",
            "Mentha spicata botanical field photograph with narrow terminal flower spikes",
            "mint herb growing in a garden, paired serrated leaves on a spreading stem",
        ])
    return list(dict.fromkeys(prompts))


def load_model():
    import open_clip
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    errors = []
    for model_id in ("hf-hub:imageomics/bioclip-2", "hf-hub:imageomics/bioclip"):
        try:
            model, _, preprocess = open_clip.create_model_and_transforms(model_id)
            tokenizer = open_clip.get_tokenizer(model_id)
            return device, model.to(device).eval(), preprocess, tokenizer, model_id
        except Exception as exc:
            errors.append(f"{model_id}: {type(exc).__name__}: {exc}")
    raise RuntimeError("Could not load BioCLIP 2 or BioCLIP. " + " | ".join(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-class", type=int, default=2, help="Independent real photos per species (default: 2)")
    parser.add_argument("--output", default="benchmark_results.csv", help="CSV output path")
    args = parser.parse_args()
    if args.per_class < 1:
        parser.error("--per-class must be at least 1")

    plants = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    hints = load_hints()
    if len(plants) != 56 or {p["common_name"] for p in plants} != set(hints):
        raise RuntimeError("Expected exactly 56 plant records with one matching model hint each.")

    print(f"Collecting up to {args.per_class} real research-grade photos for each of {len(plants)} species…")
    dataset, coverage = [], []
    for index, plant in enumerate(plants, 1):
        try:
            samples, issue = collect_samples(plant, args.per_class)
        except Exception as exc:
            samples, issue = [], f"{type(exc).__name__}: {exc}"
        coverage.append((plant["common_name"], len(samples), issue))
        dataset.extend((plant, obs_id, raw, url) for obs_id, raw, url in samples)
        print(f"[{index:02d}/56] {plant['common_name']}: {len(samples)}/{args.per_class}" + (f" — {issue}" if issue else ""))

    if not dataset:
        raise RuntimeError("No real photos were downloaded; check network access and iNaturalist availability.")
    print(f"Downloaded {len(dataset)} images. Loading BioCLIP (first run downloads model weights)…")

    import torch
    device, model, preprocess, tokenizer, model_id = load_model()
    print(f"Model: {model_id}; device: {device}. Encoding prompts…")
    prompt_rows = [prompts_for(p, hints[p["common_name"]]) for p in plants]
    prompt_features, prototypes = [], []
    with torch.no_grad():
        for prompts in prompt_rows:
            features = model.encode_text(tokenizer(prompts).to(device))
            features = features / features.norm(dim=-1, keepdim=True)
            proto = features.mean(dim=0, keepdim=True)
            proto = proto / proto.norm(dim=-1, keepdim=True)
            prompt_features.append(features)
            prototypes.append(proto)
    prototypes = torch.cat(prototypes, dim=0)
    prototypes = prototypes / prototypes.norm(dim=-1, keepdim=True)

    rows = []
    index_by_name = {p["common_name"]: i for i, p in enumerate(plants)}
    for number, (truth, obs_id, raw, url) in enumerate(dataset, 1):
        try:
            with Image.open(io.BytesIO(raw)) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
            view_logits = []
            with torch.no_grad():
                for view in analysis_views(image):
                    x = preprocess(view).unsqueeze(0).to(device)
                    feat = model.encode_image(x)
                    feat = feat / feat.norm(dim=-1, keepdim=True)
                    proto_scores = (100.0 * feat @ prototypes.T).squeeze(0)
                    prompt_scores = torch.stack([
                        (100.0 * feat @ features.T).max(dim=1).values.squeeze(0)
                        for features in prompt_features
                    ])
                    view_logits.append(.70 * proto_scores + .30 * prompt_scores)
                stacked = torch.stack(view_logits)
                logits = .75 * stacked.mean(dim=0) + .25 * stacked.max(dim=0).values
                probs = torch.softmax(logits, dim=0).cpu().numpy()
            order = np.argsort(-probs)
            top1, top3 = plants[int(order[0])]["common_name"], [plants[int(i)]["common_name"] for i in order[:3]]
            rows.append({
                "true_species": truth["common_name"],
                "scientific_name": truth["scientific_name"],
                "observation_id": obs_id,
                "top1_prediction": top1,
                "top1_correct": int(top1 == truth["common_name"]),
                "top3_predictions": " | ".join(top3),
                "top3_correct": int(truth["common_name"] in top3),
                "top1_relative_score": float(probs[int(order[0])]),
                "photo_url": url,
                "error": "",
            })
        except Exception as exc:
            rows.append({
                "true_species": truth["common_name"],
                "scientific_name": truth["scientific_name"],
                "observation_id": obs_id,
                "top1_prediction": "",
                "top1_correct": 0,
                "top3_predictions": "",
                "top3_correct": 0,
                "top1_relative_score": "",
                "photo_url": url,
                "error": f"{type(exc).__name__}: {exc}",
            })
        print(f"[{number:03d}/{len(dataset)}] {truth['common_name']} → {rows[-1]['top1_prediction'] or 'ERROR'}")

    fields = list(rows[0].keys())
    with open(args.output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    by_class = []
    for plant in plants:
        own = [r for r in rows if r["true_species"] == plant["common_name"]]
        if own:
            by_class.append((plant["common_name"], len(own),
                             sum(r["top1_correct"] for r in own) / len(own),
                             sum(r["top3_correct"] for r in own) / len(own)))
    evaluated = [r for r in rows if not r["error"]]
    if evaluated:
        print("\n=== Held-out photo benchmark summary ===")
        print(f"Model: {model_id}")
        print(f"Photos evaluated: {len(evaluated)}/{len(rows)}; classes with photos: {len(by_class)}/56")
        print(f"Overall top-1 accuracy: {sum(r['top1_correct'] for r in evaluated)/len(evaluated):.1%}")
        print(f"Overall top-3 accuracy: {sum(r['top3_correct'] for r in evaluated)/len(evaluated):.1%}")
        print("\nPer-class: species | photos | top-1 | top-3")
        for name, count, top1, top3 in by_class:
            print(f"{name} | {count} | {top1:.0%} | {top3:.0%}")
    missing = [name for name, count, _ in coverage if count < args.per_class]
    if missing:
        print("\nClasses with incomplete photo coverage:", ", ".join(missing))
    print(f"\nFull results saved to: {args.output}")
    print("Scores are relative model rankings, not calibrated probabilities. This test does not certify non-plant rejection or live Streamlit behavior.")


if __name__ == "__main__":
    main()
