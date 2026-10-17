"""Small, dependency-light PlantCare AI helpers.

These helpers deliberately avoid claiming a confirmed disease from a single image.
"""
from __future__ import annotations

from typing import Any, Iterable


REQUIRED_PLANT_FIELDS = (
    "common_name",
    "scientific_name",
    "family",
    "category",
    "identification",
    "leaf",
    "flower",
    "growth",
    "light",
    "water",
    "soil",
)


def validate_plant_records(records: Iterable[dict[str, Any]], expected_count: int = 56) -> list[str]:
    """Return validation errors for the plant library; an empty list means valid."""
    rows = list(records)
    errors: list[str] = []
    if len(rows) != expected_count:
        errors.append(f"Expected {expected_count} plant records, found {len(rows)}.")
    names: list[str] = []
    scientific: list[str] = []
    for index, plant in enumerate(rows):
        missing = [field for field in REQUIRED_PLANT_FIELDS if not str(plant.get(field, "")).strip()]
        if missing:
            errors.append(f"Record {index} is missing required fields: {', '.join(missing)}.")
        common = str(plant.get("common_name", "")).strip().casefold()
        sci = str(plant.get("scientific_name", "")).strip().casefold()
        if common:
            names.append(common)
        if sci:
            scientific.append(sci)
    if len(names) != len(set(names)):
        errors.append("Duplicate common names found.")
    if len(scientific) != len(set(scientific)):
        errors.append("Duplicate scientific names found.")
    return errors


def assess_plant_health(
    plant: dict[str, Any],
    symptoms: Iterable[str],
    soil_state: str = "Not checked",
    light_state: str = "Not sure",
    drainage_state: str = "Not sure",
    recent_change: str = "None known",
    notes: str = "",
) -> dict[str, Any]:
    """Generate cautious rule-based checks, not a plant disease diagnosis."""
    selected = {str(s).strip().casefold() for s in symptoms if str(s).strip()}
    soil = soil_state.casefold()
    light = light_state.casefold()
    drainage = drainage_state.casefold()
    change = recent_change.casefold()
    causes: list[dict[str, str]] = []
    actions: list[str] = []

    def add(title: str, evidence: str, next_step: str) -> None:
        if not any(item["possible_cause"] == title for item in causes):
            causes.append({"possible_cause": title, "why_consider_it": evidence, "safe_check": next_step})

    if "yellowing leaves" in selected:
        if "wet" in soil or "poor" in drainage or "waterlogged" in soil:
            add("Excess moisture or root-zone stress", "Yellowing together with wet soil or poor drainage can be consistent with root stress.", "Check moisture below the surface and ensure the pot drains freely before watering again.")
        if "dry" in soil:
            add("Water stress", "Yellowing and dry soil can occur when a plant is not receiving enough water, but other causes remain possible.", "Check moisture at root depth and water according to this species' profile.")
        add("Light, nutrition, pests, or natural leaf ageing", "Yellow leaves have several possible causes and are not specific to one disease.", "Inspect both sides of leaves and compare older versus new growth; do not fertilize solely because of colour.")

    if "brown or crispy edges" in selected:
        if "direct" in light or "strong" in light:
            add("Possible light scorch", "Crispy edges after strong direct light can be consistent with scorch in sensitive species.", "Check the plant's light profile and move it gradually if exposure is excessive.")
        if "dry" in soil:
            add("Dryness or low humidity", "Dry soil can contribute to crispy tissue in some plants.", "Check root-zone moisture and species-appropriate humidity; avoid a sudden watering change.")
        add("Salt buildup, root stress, or physical damage", "Brown edges are nonspecific and can have several environmental causes.", "Check drainage and recent fertilizer use; avoid adding fertilizer until the cause is clearer.")

    if "wilting" in selected:
        if "wet" in soil or "poor" in drainage or "waterlogged" in soil:
            add("Root stress despite wet soil", "Wilting with wet soil can occur when roots are stressed and cannot take up water effectively.", "Do not automatically add more water; check drainage and inspect roots only if repotting is already appropriate.")
        elif "dry" in soil:
            add("Insufficient water", "Wilting with dry soil is consistent with water stress.", "Water thoroughly if the species profile permits, then let excess water drain.")
        else:
            add("Water-balance or root problem", "Wilting alone cannot distinguish underwatering, overwatering, heat stress, or root damage.", "Check soil moisture first, then inspect light, temperature and drainage.")

    if "spots or powder on leaves" in selected:
        add("Possible pest or leaf-surface issue", "Spots or powder can have fungal, pest, mineral, or physical causes; the description alone is not diagnostic.", "Photograph the affected area closely, inspect leaf undersides, and isolate the plant if a contagious issue is plausible.")
    if "sticky residue or webbing" in selected:
        add("Possible insect or mite activity", "Sticky residue or fine webbing can be associated with sap-feeding pests, but inspect closely to confirm.", "Inspect leaf undersides, stems and new growth; avoid applying treatments until the pest is identified.")
    if "slow or stunted growth" in selected:
        add("Growing-condition or root constraint", "Growth may slow with seasonal dormancy, inadequate light, root restriction, water stress, or nutrition issues.", "Review light, watering, temperature and pot drainage before changing fertilizer.")
    if "soft or foul-smelling soil" in selected:
        add("Possible waterlogging or root decay", "Persistently soggy, foul-smelling soil warrants checking drainage and root health.", "Pause routine watering until moisture is checked; seek experienced horticultural advice if roots are soft or decaying.")

    if soil == "wet / soggy":
        actions.append("Check drainage and moisture below the surface before the next watering; do not water just because the calendar says so.")
    elif soil == "dry":
        actions.append(f"Check the species-specific watering guidance for {plant.get('common_name', 'this plant')} and water only if appropriate.")
    else:
        actions.append("Check soil moisture with a finger or suitable meter; a photograph cannot measure it.")

    if drainage == "poor":
        actions.append("Ensure excess water can leave the pot and that the container is not standing in trapped water.")
    if light == "strong direct sun":
        actions.append("Compare the current exposure with the plant profile; if it is too intense, adjust light gradually rather than moving abruptly.")
    elif light == "low light":
        actions.append("Compare the location with the species' light requirement and improve light gradually if needed.")
    if change != "none known":
        actions.append(f"Review the recent change ({recent_change}) as a possible contributor; change one factor at a time where practical.")
    actions.append("Take a dated follow-up photo from a similar angle in 3–7 days and record whether symptoms spread.")
    actions.append("Avoid pesticides or fertilizer based only on a photo or symptom label.")

    if not causes:
        causes.append({
            "possible_cause": "Insufficient evidence for a ranked cause",
            "why_consider_it": "No specific symptom was selected, or the reported evidence is too limited.",
            "safe_check": "Record visible symptoms and inspect soil, drainage, light, leaf undersides and recent care changes.",
        })

    if notes.strip():
        notes_summary = notes.strip()[:500]
    else:
        notes_summary = ""
    return {
        "plant": str(plant.get("common_name", "Unknown plant")),
        "scientific_name": str(plant.get("scientific_name", "")),
        "assessment_type": "Rule-based screening; not a confirmed diagnosis",
        "possible_causes": causes[:4],
        "action_plan": actions,
        "notes": notes_summary,
        "disclaimer": "A text/image screening cannot confirm a pathogen, measure soil moisture or nutrient levels, or replace a qualified horticulturist's assessment.",
    }
