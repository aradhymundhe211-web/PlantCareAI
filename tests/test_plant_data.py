from __future__ import annotations

import ast
import json
from pathlib import Path

from plantcare_core import REQUIRED_PLANT_FIELDS, validate_plant_records
from benchmark_56 import load_hints, prompts_for

ROOT = Path(__file__).resolve().parents[1]


def load_records():
    return json.loads((ROOT / "plant_data.json").read_text(encoding="utf-8"))


def load_model_hints():
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "MODEL_HINTS"
            for target in node.targets
        ):
            # Preserve key order and detect duplicate keys before dict evaluation.
            pairs = []
            for key, value in zip(node.value.keys, node.value.values):
                if key is None:
                    raise AssertionError("MODEL_HINTS may not use dictionary unpacking")
                pairs.append((ast.literal_eval(key), ast.literal_eval(value)))
            return pairs
    raise AssertionError("MODEL_HINTS assignment was not found")


def test_library_has_56_complete_unique_records():
    records = load_records()
    assert validate_plant_records(records, expected_count=56) == []
    assert len({p["common_name"].casefold() for p in records}) == 56
    assert len({p["scientific_name"].casefold() for p in records}) == 56
    for plant in records:
        for field in REQUIRED_PLANT_FIELDS:
            assert str(plant.get(field, "")).strip(), (plant["common_name"], field)

    assert len({p["identification"] for p in records}) == 56
    assert len({p["leaf"] for p in records}) >= 50
    assert len({p["growth"] for p in records}) >= 30


def test_every_species_has_one_nonempty_model_hint():
    records = load_records()
    pairs = load_model_hints()
    keys = [key for key, _ in pairs]
    assert len(keys) == len(set(keys)), "Duplicate MODEL_HINTS keys found"
    hints = dict(pairs)
    expected = {p["common_name"] for p in records}
    assert set(hints) == expected, {
        "missing": sorted(expected - set(hints)),
        "extra": sorted(set(hints) - expected),
    }
    assert all(isinstance(hints[name], str) and len(hints[name].strip()) >= 20 for name in expected)


def test_identification_code_has_no_local_colour_species_fallback():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "return []" in source[source.index("def identify_locally"):source.index("def visual_health_screen")]
    assert "optional_vision_rank(image" in source
    assert "species_unavailable" in source


def test_confusable_species_have_diagnostic_prompt_coverage():
    records = {p["common_name"]: p for p in load_records()}
    hints = load_hints()
    required_terms = {
        "ZZ Plant": ("Zamioculcas zamiifolia", "not bamboo canes"),
        "Aglaonema": ("Chinese evergreen", "Dieffenbachia"),
        "Mango": ("Mangifera indica", "not pinnate neem leaflets"),
        "Prayer Plant": ("herringbone vein pattern", "red-pink veins"),
    }
    for name, terms in required_terms.items():
        prompts = " ".join(prompts_for(records[name], hints[name])).casefold()
        for term in terms:
            assert term.casefold() in prompts, (name, term)


def test_source_compiles_without_importing_streamlit_or_loading_model():
    compile((ROOT / "app.py").read_text(encoding="utf-8"), "app.py", "exec")
    compile((ROOT / "plantcare_core.py").read_text(encoding="utf-8"), "plantcare_core.py", "exec")


def test_benchmark_prompt_builder_covers_all_56_species():
    records = load_records()
    hints = load_hints()
    assert set(hints) == {p["common_name"] for p in records}
    for plant in records:
        prompts = prompts_for(plant, hints[plant["common_name"]])
        assert len(prompts) >= 6
        assert all(isinstance(prompt, str) and prompt.strip() for prompt in prompts)


def test_species_ranker_uses_three_views_and_uncertainty_is_not_called_accepted():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    views_start = source.index("def _analysis_views(")
    rank_start = source.index("def bioclip_rank(", views_start)
    view_code = source[views_start:rank_start]
    assert "return views[:3]" in view_code
    assert 'POSSIBLE PLANT MATCH — CONFIRMATION NEEDED' in source
    assert 'POSSIBLE PLANT MATCH — CHECK THE ALTERNATIVES' in source
    assert 'PLANT PHOTO ACCEPTED' not in source
