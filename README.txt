PlantCare AI
Created by Aradhy Mundhe

A student project for plant photo exploration, a 56-profile plant library, practical species care guidance, visual leaf-colour screening, and care reminders.

Highlights in this version:
- Camera capture and gallery image upload.
- Plant/object screening and possible BioCLIP-based plant matching when the model is available.
- Alternative matches and a confidence band (not a calibrated probability).
- Visual colour-pattern health screening with careful uncertainty wording.
- Species profile information for light, watering, soil, fertilizer, humidity, pests, diseases and safety.
- Home-page spoken introduction using the browser's speech synthesis; click Play to hear it.
- Care Confidence Passport, separating visible photo evidence from facts a photo cannot prove.
- No paid OpenAI or Gemini API key required.

Run locally:
1. Use Python 3.11 or 3.12 in a virtual environment.
2. Install dependencies with: pip install -r requirements.txt
3. Start the app with: streamlit run app.py

Important accuracy note:
A photo match is a suggestion, not a guaranteed identification. The model must be benchmarked on labelled photographs for all 56 supported species before claiming a specific accuracy. Similar species, camera quality, background, lighting, plant age and view angle can affect results. The visual health screen looks at broad colour patterns only; it cannot confirm a disease, measure soil moisture or nutrient levels, or determine roots' health. Check soil and leaves physically, and consult a local horticulture expert for persistent or severe problems.

The browser voice depends on device/browser speech support. Care reminders and My Plants are currently session-based and may not persist after the session ends.

See QA_REPORT.txt for what was checked and what still requires live deployment testing.
