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


def decide_vision_gate(
    *,
    quality_ok: bool,
    general_object_rejected: bool,
    bio_plant_score: float,
    bio_object_score: float,
    document_score: float,
) -> tuple[bool, str, str]:
    """Conservative policy for image screening before species ranking.

    Clear non-plant or document evidence is rejected. Ambiguous BioCLIP evidence
    is allowed to proceed to species ranking so unusual plants are not rejected
    merely because the safety gate is uncertain.
    """
    if not quality_ok:
        return False, "Photo is too small, dark, or blurred to assess reliably", "quality"
    if general_object_rejected:
        return False, "General vision screening recognized a non-plant object", "nonplant"

    plant_score = float(bio_plant_score)
    object_score = float(bio_object_score)
    document = float(document_score)
    margin = plant_score - object_score

    if document >= 0.84 and margin < 4.0:
        return False, "The image appears to be a text-heavy document or screenshot", "nonplant"
    if object_score >= 24.0 and margin <= -1.0:
        return False, "The image is much more consistent with a non-plant object than a living plant", "nonplant"
    if plant_score >= 18.0 and margin >= 1.5:
        return True, "Plant evidence is strong enough to continue", "accepted"
    return True, "Plant presence is uncertain; continuing to species matching", "uncertain"


def assess_plant_health(
    plant: dict[str, Any],
    symptoms: Iterable[str],
    soil_state: str = "Not checked",
    light_state: str = "Not sure",
    drainage_state: str = "Not sure",
    recent_change: str = "None known",
    notes: str = "",
    watering_frequency: str = "Not sure",
    pot_drainage: str = "Not sure",
    symptom_location: str = "Not sure",
    symptom_duration: str = "Not sure",
    plant_location: str = "Not sure",
    pest_seen: str = "Not checked",
) -> dict[str, Any]:
    """Generate cautious rule-based checks, not a plant disease diagnosis."""
    selected = {str(s).strip().casefold() for s in symptoms if str(s).strip()}
    soil = soil_state.casefold()
    light = light_state.casefold()
    drainage = drainage_state.casefold()
    change = recent_change.casefold()
    frequency = watering_frequency.casefold()
    pot_drainage_l = pot_drainage.casefold()
    symptom_loc = symptom_location.casefold()
    duration = symptom_duration.casefold()
    plant_loc = plant_location.casefold()
    pest_state = pest_seen.casefold()
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

    if "holes or chewed leaves" in selected:
        add("Possible chewing pests", "Irregular holes, missing leaf edges or fresh frass can be consistent with caterpillars, beetles or other chewing organisms.", "Inspect leaves at dusk and both leaf surfaces; photograph the pest or damage before choosing a treatment.")
    if "curled or distorted new leaves" in selected:
        add("Possible sap-feeding pests or environmental stress", "Distorted new growth can occur with aphids, mites, heat, water stress or chemical exposure.", "Inspect new growth and leaf undersides with good light; check for tiny insects before applying any product.")
    if "leaf drop" in selected:
        add("Recent environmental or root stress", "Leaf drop may follow abrupt light, temperature, watering or location changes and is not disease-specific.", "Compare recent care changes and check soil moisture and drainage before changing several conditions at once.")
    if "leggy growth" in selected:
        add("Insufficient light or normal growth habit", "Long, weak growth and widely spaced leaves can be associated with inadequate light, although species habits vary.", "Compare the current location with the plant's light profile and improve exposure gradually if needed.")
    if "mold on soil surface" in selected:
        add("Persistently moist surface or low airflow", "Surface mold can appear where organic material stays damp; it does not alone prove root disease.", "Let the surface dry as appropriate for this species, improve airflow, and check drainage without allowing a moisture-sensitive plant to desiccate.")
    if "black or soft stem tissue" in selected:
        add("Possible tissue decay or injury", "Soft, darkening tissue is a concerning sign but a photo or symptom label cannot identify the cause.", "Keep the plant separate from others, avoid wetting affected tissue, and seek local horticultural advice if the area is spreading.")

    if pest_state == "yes, visible":
        actions.append("Photograph the suspected pest close-up and inspect leaf undersides, stem joints and new growth; identify it before selecting a treatment.")
    elif pest_state == "not checked":
        actions.append("Inspect leaf undersides, stem joints and new growth for insects, eggs, sticky residue or fine webbing.")

    if pot_drainage_l == "no drainage holes":
        actions.append("A pot without drainage holes can trap water. If feasible, use a pot with drainage or an inner nursery pot; do not leave roots standing in water.")
    if frequency == "daily":
        actions.append("Daily watering can be too frequent for many plants. Check root-zone moisture and the species profile rather than watering by schedule alone.")
    elif frequency == "less than weekly":
        actions.append("Infrequent watering is not automatically wrong; compare actual root-zone moisture and this species' needs before changing frequency.")
    if symptom_loc == "mostly older/lower leaves":
        actions.append("Because symptoms are concentrated on older/lower leaves, check whether only a few oldest leaves are naturally ageing or whether the pattern is spreading.")
    elif symptom_loc == "mostly new/upper growth":
        actions.append("Because symptoms affect new growth, inspect it closely for pests, distortion and recent exposure changes.")
    if plant_loc == "indoors":
        actions.append("For an indoor plant, check distance from windows, air-conditioning/heater drafts and whether the pot sits in a water-filled cachepot.")
    elif plant_loc == "outdoors":
        actions.append("For an outdoor plant, note recent heat, heavy rain, wind, shade changes and possible spray drift from nearby gardening.")
    if duration == "spreading quickly (1–3 days)":
        actions.append("Rapidly spreading symptoms deserve prompt inspection; isolate the plant if a contagious pest or leaf issue is plausible and get local expert advice.")

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

    # Practical triage: flag when prompt local inspection is sensible, without
    # asserting that a specific disease is present.
    urgent_signs = (
        "black or soft stem tissue" in selected
        or "soft or foul-smelling soil" in selected
        or duration == "spreading quickly (1–3 days)"
    )
    priority = (
        "Prompt inspection recommended"
        if urgent_signs
        else "Routine observation and care checks"
    )
    if urgent_signs:
        actions.insert(0, "Priority: inspect the affected area today. If symptoms are spreading, keep the plant separate from nearby plants where practical and seek local horticultural advice; this flag does not identify a disease.")

    if notes.strip():
        notes_summary = notes.strip()[:500]
    else:
        notes_summary = ""
    return {
        "plant": str(plant.get("common_name", "Unknown plant")),
        "scientific_name": str(plant.get("scientific_name", "")),
        "assessment_type": "Rule-based screening; not a confirmed diagnosis",
        "priority": priority,
        "possible_causes": causes[:4],
        "action_plan": actions,
        "notes": notes_summary,
        "observations": {"soil_moisture": soil_state, "watering_frequency": watering_frequency, "pot_drainage": pot_drainage, "light": light_state, "plant_location": plant_location, "symptom_location": symptom_location, "symptom_duration": symptom_duration, "pest_seen": pest_seen, "recent_change": recent_change},
        "disclaimer": "A text/image screening cannot confirm a pathogen, measure soil moisture or nutrient levels, or replace a qualified horticulturist's assessment.",
    }


def answer_copilot_question(question: str, plants: Iterable[dict[str, Any]]) -> str:
    """Answer common care questions using only the supplied plant library.

    This is deterministic retrieval, not a generative model or a disease diagnosis.
    It deliberately asks for clarification when it cannot ground an answer.
    """
    q = str(question or "").strip().casefold()
    rows = list(plants.values()) if isinstance(plants, dict) else list(plants)
    if not q:
        return "Ask a plant-care question, such as ‘How often should I water Tulsi?’ or ‘What light does a Mango tree need?’"

    # Match an explicit common or scientific name only; do not infer a species.
    named = []
    for plant in rows:
        common = str(plant.get("common_name", "")).strip()
        scientific = str(plant.get("scientific_name", "")).strip()
        if common and common.casefold() in q:
            named.append((len(common), plant))
        elif scientific and scientific.casefold() in q:
            named.append((len(scientific), plant))
    plant = max(named, key=lambda item: item[0])[1] if named else None

    if any(term in q for term in ("yellow", "wilting", "wilt", "brown leaves", "spots", "disease", "sick", "dying", "pest", "insect", "mold", "mould")):
        base = (
            "I can help you narrow this down, but symptoms alone do not confirm a disease. "
            "Check the soil moisture at root depth, drainage, recent changes in light or temperature, "
            "and both sides of the leaves for pests. Avoid adding pesticide or fertilizer based only on a photo. "
            "If you tell me the plant name, symptoms, soil condition and how quickly the problem is spreading, "
            "I can give a more relevant checklist."
        )
        if plant:
            base += f"\n\nFor {plant.get('common_name')} ({plant.get('scientific_name')}), the library lists: watering — {plant.get('water', 'not recorded')}; light — {plant.get('light', 'not recorded')}; soil — {plant.get('soil', 'not recorded')}."
            diseases = str(plant.get("diseases", "")).strip()
            pests = str(plant.get("pests", "")).strip()
            if diseases:
                base += f"\n\nProblems to monitor in the profile: {diseases}"
            if pests:
                base += f"\nPests to inspect for: {pests}"
        return base

    if not plant:
        examples = ", ".join(str(p.get("common_name", "")) for p in rows[:8])
        return (
            "I can answer from the verified plant profiles bundled with this app, but I could not identify a specific plant in your question. "
            f"Please include one of the supported plant names (for example: {examples}) and ask about watering, light, soil, temperature, humidity, fertilizer, pruning, propagation, pests, toxicity or pet safety. "
            "I do not use a paid AI API, and I will not invent details that are missing from the profile."
        )

    fields = [
        (("water", "watering", "water"), "water", "Watering"),
        (("light", "sun", "sunlight", "bright"), "light", "Light"),
        (("soil", "potting", "mix", "drainage"), "soil", "Soil"),
        (("fertilizer", "fertiliser", "feed", "nutrient"), "fertilizer", "Fertilizer"),
        (("temperature", "cold", "heat", "weather"), "temperature", "Temperature"),
        (("humidity", "humid"), "humidity", "Humidity"),
        (("pest", "insect", "bug"), "pests", "Pests to monitor"),
        (("disease", "fungus", "fungal", "rot", "mildew"), "diseases", "Problems to monitor"),
        (("toxic", "poison", "eat", "edible"), "toxicity", "Toxicity caution"),
        (("pet", "cat", "dog", "animal"), "pet_safety", "Pet safety"),
        (("prun", "trim", "cut back"), "pruning", "Pruning"),
        (("propagat", "cutting", "multiply", "grow another"), "propagation", "Propagation"),
        (("identify", "recognize", "recognise", "look like", "leaf", "flower"), "identification", "Identification clues"),
    ]
    chosen = [(key, label) for terms, key, label in fields if any(term in q for term in terms)]
    if not chosen:
        chosen = [("water", "Watering"), ("light", "Light"), ("soil", "Soil")]
    answer = [f"For {plant.get('common_name')} ({plant.get('scientific_name')}), here is what the PlantCare AI reference profile says:"]
    for key, label in chosen[:3]:
        value = str(plant.get(key, "")).strip()
        if value:
            answer.append(f"**{label}:** {value}")
    answer.append("These are general profile notes, not a diagnosis. Check the plant's actual conditions and seek local horticultural advice if it is rapidly deteriorating.")
    return "\n\n".join(answer)
