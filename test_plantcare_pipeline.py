"""Static wiring checks for the inference pipeline; not image-accuracy tests."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")


class PipelineWiringTests(unittest.TestCase):
    def test_general_screen_and_bioclip_screen_run_before_species_ranker(self):
        general_gate = APP.index("gate_is_plant, gate_score, gate_reason, gate_meta = vision_gate(image)")
        bio_gate = APP.index("accepted, bio_reason, bio_category = decide_vision_gate(")
        rank_call = APP.index("ai_rows, model_used, model_error = optional_vision_rank(image,")
        self.assertLess(general_gate, bio_gate)
        self.assertLess(bio_gate, rank_call)

    def test_uncertain_bioclip_screen_is_allowed_to_continue_to_species_ranker(self):
        core = (ROOT / "plantcare_core.py").read_text(encoding="utf-8")
        self.assertIn('return True, "Plant presence is uncertain; continuing to species matching", "uncertain"', core)
        self.assertIn("except Exception:", APP)
        self.assertIn("let species matching attempt a result", APP)

    def test_bioclip2_is_tried_before_original_bioclip_fallback(self):
        self.assertIn('for model_id in ("hf-hub:imageomics/bioclip-2", "hf-hub:imageomics/bioclip")', APP)

    def test_identification_ui_does_not_present_an_uncalibrated_percentage(self):
        self.assertNotIn("Confidence: {result['conf']}%", APP)
        self.assertIn("not a calibrated probability", APP)


if __name__ == "__main__":
    unittest.main(verbosity=2)
