import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from plantnet_client import identify_with_plantnet

ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "results": [
                {
                    "score": 0.82,
                    "species": {"scientificNameWithoutAuthor": "Mangifera indica"},
                },
                {
                    "score": 0.08,
                    "species": {"scientificNameWithoutAuthor": "Ocimum tenuiflorum"},
                },
            ]
        }


class PlantNetClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plants = json.loads((ROOT / "plant_data.json").read_text(encoding="utf-8"))

    def image_bytes(self):
        image = Image.new("RGB", (240, 240), (40, 130, 40))
        stream = io.BytesIO()
        image.save(stream, format="PNG")
        return stream.getvalue()

    def test_maps_only_exact_supported_scientific_names(self):
        with patch("plantnet_client.requests.post", return_value=FakeResponse()):
            result = identify_with_plantnet(self.image_bytes(), self.plants, "test-key")
        self.assertTrue(result["ok"])
        self.assertEqual(result["rows"][0][0]["common_name"], "Mango")
        self.assertAlmostEqual(result["rows"][0][1], 0.82)

    def test_missing_api_key_does_not_make_network_call(self):
        with patch("plantnet_client.requests.post") as post:
            result = identify_with_plantnet(self.image_bytes(), self.plants, "")
        post.assert_not_called()
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
