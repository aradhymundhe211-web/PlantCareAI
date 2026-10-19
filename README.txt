PLANTCARE AI — current repository notes

WHAT THIS BUILD DOES
- Includes 56 plant profiles in plant_data.json.
- Supports camera capture and gallery upload through the same image-analysis pipeline.
- Uses the original BioCLIP model (hf-hub:imageomics/bioclip) with prompt-based, multi-view ranking across the 56 supported profiles. This is zero-shot similarity ranking, not a custom-trained 56-class classifier.
- Applies conservative plant-presence and document-like-image checks. These checks reduce some false results but can still make mistakes.
- If the vision model cannot load, the app reports identification unavailable instead of inventing a species.
- Includes approximate visible-colour screening and a guided symptom assessment. These are screening aids, not a trained disease detector or confirmed diagnosis.
- Includes a local, profile-grounded, rule-based Plant Health Copilot. It does not use a general-purpose language model or a paid inference API.
- Includes Plant Library, Search, My Plants, reminders, and a session-scoped journal.

CURRENT VALIDATION — 2026-10-19
- Latest GitHub Actions run passed Python compilation and the automated test suite.
- The latest held-out real-photo benchmark evaluated 552 images across all 56 classes (Calathea Orbifolia had only 2 usable images; other classes had 10 each).
- Benchmark top-1 accuracy: 81.2%; top-3 accuracy: 90.9%.
- Weak classes in this sample include Snake Plant (10% top-1), Spinach (20%), ZZ Plant (30%), Dracaena Marginata (30%), Aglaonema (30%), Lemon (30%), and Mango (40%).
- These results are preliminary and do not certify performance on arbitrary user photos. The benchmark tests species ranking, not the complete deployed UI or plant/non-plant rejection.
- The live Streamlit app could not be exercised by the available browser inspection in this audit. The previously reported live false rejection of Marigold and Tulsi has not been confirmed fixed by a new live test.
- My Plants, reminders, and journal entries are session-scoped and are not guaranteed to persist after a refresh or app restart.

IMPORTANT ACCURACY BOUNDARY
Do not claim 100% accuracy. A library of 56 profiles does not mean the model has been trained or validated to identify every plant correctly. The displayed result is a relative match, not a calibrated probability. The health panel analyses rough colour patterns; it cannot confirm disease, reliably detect pests, or measure soil moisture, root health, nutrients, or exact sunlight exposure.

DEPENDENCIES
requirements.txt pins Streamlit, Pillow, NumPy, PyTorch, torchvision, open_clip_torch, and requests. Model weights are downloaded from the model host at runtime, so first startup requires network access and enough memory/storage. The app is not guaranteed to work offline.

RUN LOCALLY
Use the Python version specified by .python-version, then run:
  python -m pip install -r requirements.txt
  streamlit run app.py

RUN TESTS
From the project root:
  python -m py_compile app.py plantcare_core.py benchmark_56.py
  python -m pytest -q

DEPLOYMENT CHECKLIST
1. Wait for Streamlit Community Cloud to finish deploying the latest main commit.
2. Inspect Manage app > Logs for dependency, model-download, memory, or startup errors.
3. Open all seven pages and exercise the controls.
4. Test clear plant photos, the same photo via gallery and camera, a car photo, a dashboard screenshot, an unrelated object, and a blurry/dark photo.
5. Specifically retest the real Marigold and Tulsi photos previously reported as falsely rejected.
6. Test Copilot, Library search/category/sorting, Search suggestions/quick views, and My Plants reminder create/complete/delete actions.
7. Verify the live deployment separately; passing unit tests does not prove end-to-end website behavior.
