PLANTCARE AI — audited repair build
Created by Aradhy Mundhe

WHAT THIS BUILD DOES
- Includes 56 plant profiles in plant_data.json.
- Supports camera capture and gallery image upload through the same analysis path.
- Uses BioCLIP 2 with an original BioCLIP fallback for zero-shot image/text ranking against the 56 profile classes.
- Applies non-plant safeguards where the relevant local model weights are available.
- If the vision model is unavailable, it does not guess a species from image colour or manually selected clues.
- Includes a visible-colour screening panel and a guided symptom-and-condition assessment. These are cautious screening aids, not a disease diagnosis.
- Adds a chat-style local Copilot that retrieves plant-care facts from the bundled profiles and uses simple rules for common symptom questions. It does not require a paid AI inference API.
- Includes the plant library, search, My Plants, reminders and session-scoped journal.

IMPORTANT ACCURACY BOUNDARY
Having 56 profiles does not mean the model has been trained or validated to identify all 56 accurately. The image model uses zero-shot similarity, not a custom-trained classifier. The displayed category is a relative ranking signal, not a calibrated probability. No labelled held-out dataset for the 56 species was supplied, so species accuracy is not certified. The health panel is based on colour patterns; it cannot confirm disease, detect pests reliably, or measure soil/root/nutrient conditions. The Copilot is profile-grounded and rule-based, not a general language model.

NO PAID AI API
The identification and Copilot features do not call a paid AI inference API. Model weights are downloaded from the model host at runtime, so first startup requires network access and enough disk/RAM. Public reference photos may be retrieved from iNaturalist/Wikipedia. This is not fully offline and does not promise offline startup.

DEPLOY TO STREAMLIT COMMUNITY CLOUD
1. Extract this ZIP.
2. Upload the CONTENTS of PlantCareAI-main to the root of your GitHub repository, not the outer folder itself. Preserve .streamlit/config.toml.
3. Commit and push the changes.
4. In Streamlit Community Cloud, open the app and wait for the build to finish.
5. Inspect Manage app > Logs if the app fails. Model weight downloads can be large and may exceed free hosting memory/storage or startup limits.
6. Test clear plant photos, the same photo from camera and gallery, a car photo, a non-supported plant, and a blurry image. If the model does not load, the app should report identification unavailable instead of guessing.

RUN LOCALLY
Use Python 3.11.11 (see .python-version), install requirements, then run:
  python -m pip install -r requirements.txt
  streamlit run app.py

TESTS
Run from the project root:
  python -m py_compile app.py plantcare_core.py test_plantcare_core.py
  python -m unittest discover -s . -v

The lightweight tests validate profile structure and rule-based Copilot behaviour. They do not test live model inference or certify image accuracy.
