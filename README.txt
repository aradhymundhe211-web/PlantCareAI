PLANTCARE AI
Created by Aradhy Mundhe

PlantCare AI is a student project for exploring 56 plant profiles, suggesting possible matches from a plant photo, providing general care guidance, and organising session-based care reminders.

Key features
- Camera capture and gallery upload for plant photos
- Plant-identification shortlist with non-plant screening and uncertainty messages
- Plant library and searchable care profiles
- Visual leaf-colour screening (not a confirmed disease diagnosis)
- PlantCare Care Confidence Passport: separates visible image clues from information a photo cannot establish
- Browser-based spoken introduction on the Home page
- My Plants and reminders with an explicit 12-hour AM/PM time selector

Run locally
1. Install a compatible Python version and the packages listed in requirements.txt.
2. Run: streamlit run app.py
3. Open the local URL printed by Streamlit.

Deployment notes
- Upload the contents of this folder to the repository root while preserving .streamlit/config.toml inside the .streamlit folder.
- Streamlit Community Cloud must finish rebuilding after a commit before testing the hosted app.
- Browser speech uses voices installed on the visitor's device. Pronunciation and voice quality can vary by browser/OS.
- Reminders are currently session-scoped and are not guaranteed to survive a new session or browser reset.

Accuracy and safety
- The app returns possible matches from its 56-plant library, not a guarantee that every image will be identified correctly.
- Use clear, well-lit photos. Compare alternatives and the plant profile before acting on the result.
- Visible leaf colours can flag patterns, but they do not confirm a disease or measure soil moisture, fertilizer/nutrient levels, or root health.

See QA_REPORT.txt for the checks performed and limitations that remain.
