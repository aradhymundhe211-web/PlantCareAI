import unittest
from plantcare_core import decide_vision_gate
import re

class RegressionMockTests(unittest.TestCase):
    def test_fortuner_nonplant_rejection_via_general_object_gate(self):
        # Simulate a strong general-object gate rejection (e.g., vehicle image)
        accepted, reason, category = decide_vision_gate(
            quality_ok=True,
            general_object_rejected=True,
            bio_plant_score=5.0,
            bio_object_score=40.0,
            context_plant_score=5.0,
            context_text_score=5.0,
            document_score=0.10,
        )
        self.assertFalse(accepted)
        self.assertEqual(category, "nonplant")

    def test_tulsi_mint_margin_uncertain_behaviour(self):
        # Simulate a small margin between plant and object evidence -> uncertain
        accepted, reason, category = decide_vision_gate(
            quality_ok=True,
            general_object_rejected=False,
            bio_plant_score=19.0,
            bio_object_score=18.0,
            context_plant_score=20.0,
            context_text_score=18.0,
            document_score=0.10,
            minimum_bio_plant_score=18.0,
            minimum_bio_margin=1.5,
        )
        # Margin = 1.0 < 1.5 so should be uncertain
        self.assertFalse(accepted)
        self.assertEqual(category, "uncertain")

    def test_document_like_rejection(self):
        # Simulate screenshot/document evidence
        accepted, reason, category = decide_vision_gate(
            quality_ok=True,
            general_object_rejected=False,
            bio_plant_score=24.0,
            bio_object_score=23.0,
            context_plant_score=22.0,
            context_text_score=34.0,
            document_score=0.84,
        )
        self.assertFalse(accepted)
        self.assertEqual(category, "nonplant")

if __name__ == '__main__':
    unittest.main()
