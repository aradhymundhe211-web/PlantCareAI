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
- Local BioCLIP fallback works without an API key; optional optional external API is used first when configured

Optional higher-recall plant identification (recommended for deployment)
1. Create an account and obtain a private API key at https://my.plantnet.org/ . Check current quota and terms before sharing the app publicly.
2. In Streamlit Community Cloud, open your app settings and add this under the Secrets section:
    = "paste-your-private-key-here"
3. Do not put the key in app.py, plantnet_client.py, a public GitHub file, or a screenshot. Keep it in Streamlit Secrets.
4. Commit/push the code and reboot the Streamlit app. When configured, Pl@ntNet is tried first. Results are mapped to the 56-plant library only by exact scientific-name match; otherwise the local classifier is used as a fallback.
5. The documented free allowance is up to 500 identification requests per day, subject to account quota and terms. Each identification sends the selected image to Pl@ntNet.

Run locally
1. Install a compatible Python version and the packages listed in requirements.txt.
2. Run: streamlit run app.py
3. Open the local URL printed by Streamlit.

Deployment notes
- Upload the contents of this folder to the repository root while preserving .streamlit/config.toml inside the .streamlit folder.
- Streamlit Community Cloud must finish rebuilding after a commit before testing the hosted app.
- The Home page introduces PlantCare AI in text and offers a user-triggered spoken introduction. Browser autoplay restrictions mean the voice does not automatically play without a click.
- Reminders are currently session-scoped and are not guaranteed to survive a new session or browser reset.

Accuracy and safety
- When configured, Pl@ntNet is tried first and results are mapped to the 56-plant library only by exact scientific-name match; BioCLIP remains the local fallback. This does not guarantee every image will be identified correctly.
- Use clear, well-lit photos. Compare alternatives and the plant profile before acting on the result.
- Visual fallback checks were widened to better admit flower-heavy photos and foliage under varied lighting. Non-plant screening is retained, but it is not infallible.
- Visible leaf colours can flag patterns, but they do not confirm a disease or measure soil moisture, fertilizer/nutrient levels, or root health.

Plant Health Copilot uses transparent rules, not a trained disease detector. Its possible causes are screening prompts, not confirmed diagnoses. Journal entries are session-scoped and may disappear after a refresh or new session.

Run the lightweight project checks from the repository root with: `python -m unittest discover -s tests -v`.

See QA_REPORT.txt for checks performed and limitations that remain.


Identification notes (2026-10-17): The app uses BioCLIP 2 with original BioCLIP fallback and multi-view image ranking across the 56 configured library classes. The model weights are downloaded from Hugging Face at runtime and require internet access on first load. The app is not fully offline and no model guarantees perfect identification. If model loading fails, the UI should show identification temporarily unavailable rather than claiming no plant was detected.
