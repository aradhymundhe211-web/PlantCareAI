"""Policy-level tests for the image validation decision (not model benchmarks)."""
import unittest
from plantcare_core import decide_vision_gate


def decide(**overrides):
    values = {
        "quality_ok": True,
        "general_object_rejected": False,
        "bio_plant_score": 25.0,
        "bio_object_score": 20.0,
        "document_score": 0.20,
    }
    values.update(overrides)
    return decide_vision_gate(**values)


class VisionGatePolicyTests(unittest.TestCase):
    def test_positive_botanical_evidence_can_pass_to_species_ranker(self):
        accepted, _, category = decide()
        self.assertTrue(accepted)
        self.assertEqual(category, "accepted")

    def test_strong_general_object_evidence_rejects_before_ranking(self):
        accepted, _, category = decide(general_object_rejected=True)
        self.assertFalse(accepted)
        self.assertEqual(category, "nonplant")

    def test_screenshot_like_context_rejects_before_ranking(self):
        accepted, reason, category = decide(
            bio_plant_score=24.0,
            bio_object_score=23.0,
            document_score=0.84,
        )
        self.assertFalse(accepted)
        self.assertEqual(category, "nonplant")
        self.assertTrue("screenshot" in reason.lower() or "document" in reason.lower())

    def test_uncertain_plant_presence_is_deferred_to_species_ranker(self):
        accepted, _, category = decide(
            bio_plant_score=21.0,
            bio_object_score=20.3,
            document_score=0.20,
        )
        self.assertTrue(accepted)
        self.assertEqual(category, "uncertain")

    def test_low_quality_image_is_not_passed_to_species_ranker(self):
        accepted, _, category = decide(quality_ok=False)
        self.assertFalse(accepted)
        self.assertEqual(category, "quality")

    def test_document_like_score_with_no_clear_plant_margin_rejects(self):
        accepted, _, category = decide(
            bio_plant_score=25.0,
            bio_object_score=23.0,
            document_score=0.84,
        )
        self.assertFalse(accepted)
        self.assertEqual(category, "nonplant")


if __name__ == "__main__":
    unittest.main(verbosity=2)
