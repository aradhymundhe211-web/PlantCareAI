import json
import os

class PlantCareCore:
    def __init__(self, data_path="plant_data.json"):
        self.data_path = data_path
        self.plant_database = self.load_plant_data()

    def load_plant_data(self):
        """Loads the 56-species plant database safely."""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading plant data: {e}")
                return {}
        return {}

    def identify_plant(self, prediction_label, confidence=1.0):
        """
        Normalizes prediction labels from the vision model and maps them 
        accurately to the 56 species database.
        """
        if not prediction_label:
            return self._get_fallback("Unknown Plant", confidence)

        # 1. Clean the string: remove underscores, strip whitespace, title case
        raw_label = str(prediction_label).strip()
        clean_label = raw_label.replace("_", " ").title()

        # 2. Direct lookup in database
        if clean_label in self.plant_database:
            return self._format_result(clean_label, self.plant_database[clean_label], confidence)

        # 3. Case-insensitive fallback check across all keys
        for key, info in self.plant_database.items():
            if key.lower() == raw_label.lower() or key.lower() == clean_label.lower():
                return self._format_result(key, info, confidence)

        # 4. Partial/Substring match if exact match fails
        for key, info in self.plant_database.items():
            if key.lower() in raw_label.lower() or raw_label.lower() in key.lower():
                return self._format_result(key, info, confidence)

        # 5. Safe fallback if species isn't resolved
        return self._get_fallback(clean_label, confidence)

    def _format_result(self, name, info, confidence):
        result = info.copy() if isinstance(info, dict) else {}
        result["matched_name"] = name
        result["confidence"] = confidence
        return result

    def _get_fallback(self, label, confidence):
        return {
            "matched_name": label,
            "scientific_name": "Scientific name not mapped",
            "water": "Check soil dryness before watering thoroughly.",
            "light": "Provide bright, indirect sunlight.",
            "humidity": "Average indoor room humidity.",
            "description": "Plant identified, but detailed care instructions are currently unavailable for this specific label.",
            "confidence": confidence
        }
