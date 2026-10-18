"""Static wiring checks for the key inference pipeline; not image-accuracy tests."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")


class PipelineWiringTests(unittest.TestCase):
    def test_plant_gate_is_called_before_species_ranker(self):
        gate_call = APP.index("gate_is_plant, gate_score, gate_reason, gate_meta = vision_gate(image)")
        rank_call = APP.index("ai_rows, model_used, model_error = optional_vision_rank(image,")
        self.assertLess(gate_call, rank_call)

    def test_uncertain_vision_gate_does_not_continue_to_species_ranking(self):
        self.assertIn("return False, float(local_score), reason, meta", APP)
        self.assertIn("Plant presence could not be verified confidently", (ROOT / "plantcare_core.py").read_text(encoding="utf-8"))
        self.assertIn('"gate_uncertain": True', APP)

    def test_model_default_is_the_smaller_original_bioclip(self):
        self.assertIn('DEFAULT_BIOCLIP_MODEL_ID = "hf-hub:imageomics/bioclip"', APP)
        self.assertNotIn('for model_id in ("hf-hub:imageomics/bioclip-2", "hf-hub:imageomics/bioclip")', APP)

    def test_identification_ui_does_not_present_an_uncalibrated_percentage(self):
        self.assertNotIn("Confidence: {result['conf']}%", APP)
        self.assertIn("not a calibrated probability", APP)


if __name__ == "__main__":
    unittest.main(verbosity=2)
