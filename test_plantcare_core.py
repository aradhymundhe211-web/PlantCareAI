import json
import unittest
from pathlib import Path

from plantcare_core import answer_copilot_question, assess_plant_health, validate_plant_records


ROOT = Path(__file__).resolve().parent


class PlantLibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plants = json.loads((ROOT / "plant_data.json").read_text(encoding="utf-8"))

    def test_library_has_56_complete_unique_records(self):
        self.assertEqual(validate_plant_records(self.plants, expected_count=56), [])

    def test_tulsi_and_mint_are_separate_classes(self):
        names = {p["common_name"]: p["scientific_name"] for p in self.plants}
        self.assertEqual(names["Tulsi"], "Ocimum tenuiflorum")
        self.assertEqual(names["Mint"], "Mentha spicata")
        self.assertNotEqual(names["Tulsi"], names["Mint"])

    def test_model_prompt_hints_cover_all_56_library_classes(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        import re
        block = re.search(r"MODEL_HINTS = \{(.*?)\n\}", source, re.S)
        self.assertIsNotNone(block)
        hinted_names = set(re.findall(r'^\s*"([^"]+)":', block.group(1), re.M))
        library_names = {p["common_name"] for p in self.plants}
        self.assertEqual(hinted_names, library_names)

    def test_mango_and_marigold_are_present(self):
        names = {p["common_name"] for p in self.plants}
        self.assertIn("Mango", names)
        self.assertIn("Marigold", names)


class PlantHealthCopilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plants = {
            p["common_name"]: p
            for p in json.loads((ROOT / "plant_data.json").read_text(encoding="utf-8"))
        }

    def test_yellowing_and_wet_soil_suggests_check_not_diagnosis(self):
        result = assess_plant_health(
            self.plants["Tulsi"],
            ["Yellowing leaves"],
            soil_state="Wet / soggy",
            drainage_state="Poor",
        )
        self.assertTrue(result["possible_causes"])
        self.assertIn("not a confirmed diagnosis", result["assessment_type"].lower())
        self.assertTrue(any("drainage" in action.lower() or "water" in action.lower()
                            for action in result["action_plan"]))

    def test_wilting_and_dry_soil_gives_safe_check(self):
        result = assess_plant_health(
            self.plants["Mango"],
            ["Wilting"],
            soil_state="Dry",
        )
        self.assertTrue(any("water" in cause["possible_cause"].lower()
                            for cause in result["possible_causes"]))
        self.assertTrue(any("water" in action.lower() for action in result["action_plan"]))

    def test_no_symptoms_does_not_invent_a_disease(self):
        result = assess_plant_health(self.plants["Marigold"], [])
        self.assertIn("Insufficient evidence", result["possible_causes"][0]["possible_cause"])
        self.assertIn("cannot confirm", result["disclaimer"].lower())

    def test_notes_are_bounded(self):
        result = assess_plant_health(
            self.plants["Mint"], [], notes="x" * 2000
        )
        self.assertLessEqual(len(result["notes"]), 500)

    def test_copilot_answers_from_named_plant_profile(self):
        answer = answer_copilot_question("How much light does Mango need?", self.plants)
        self.assertIn("Mango", answer)
        self.assertIn("Light", answer)
        self.assertIn(self.plants["Mango"]["light"], answer)

    def test_copilot_does_not_guess_unnamed_plant(self):
        answer = answer_copilot_question("What is wrong with my plant?", self.plants)
        self.assertIn("could not identify a specific plant", answer)
        self.assertIn("do not use a paid AI API", answer)


if __name__ == "__main__":
    unittest.main()
