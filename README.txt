PLANTCARE AI
Created by Aradhy Mundhe

PlantCare AI is a student project for exploring 56 plant profiles, suggesting possible matches from a plant photo, providing general care guidance, and organising session-based care reminders.

Key features
- Camera capture and gallery upload for plant photos
- Plant identification with non-plant screening, alternative matches, and uncertainty messages
- Plant Look-Alike Showdown: compare the leading candidate species using their stored leaf, flower, growth and identification descriptions
- Plant Health Copilot: symptom-and-condition checklist with possible causes, safe next steps, and a session-scoped observation journal
- Plant library and searchable care profiles
- Visual leaf-colour screening (not a confirmed disease diagnosis)
- Single-photo care guidance and plant-profile information
- My Plants and reminders with an explicit 12-hour AM/PM time selector
- No paid AI API key required

Run locally
1. Install a compatible Python version and the packages listed in requirements.txt.
2. Run: streamlit run app.py
3. Open the local URL printed by Streamlit.

Deployment notes
- Upload the contents of this folder to the repository root while preserving .streamlit/config.toml inside the .streamlit folder.
- Streamlit Community Cloud must finish rebuilding after a commit before testing the hosted app.
- The spoken Home-page introduction has been removed. Written creator credits remain.
- Reminders are currently session-scoped and are not guaranteed to survive a new session or browser reset.

Accuracy and safety
- The app returns possible matches from its 56-plant library, not a guarantee that every image will be identified correctly.
- Use clear, well-lit photos. Compare alternatives and the plant profile before acting on the result.
- Visual fallback checks were widened to better admit flower-heavy photos and foliage under varied lighting. Non-plant screening is retained, but it is not infallible.
- Visible leaf colours can flag patterns, but they do not confirm a disease or measure soil moisture, fertilizer/nutrient levels, or root health.

Plant Health Copilot uses transparent rules, not a trained disease detector. Its possible causes are screening prompts, not confirmed diagnoses. Journal entries are session-scoped and may disappear after a refresh or new session.

Run the lightweight project checks from the repository root with: `python -m unittest discover -s tests -v`.

See QA_REPORT.txt for checks performed and limitations that remain.
