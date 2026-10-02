PLANTCARE AI — COMPETITION BUILD V8
Made by Aradhy Mundhe

Local Windows launch
1. First time: run install_windows.bat
2. Then double-click START_PLANTCARE_AI.bat
3. The launcher starts Streamlit and opens Chrome.

School / public sharing
A localhost URL works only on the computer running the app. For a school
computer or another phone, deploy this folder to a public Streamlit host such
as Streamlit Community Cloud and share the generated streamlit.app URL.

Identification
- Generic CLIP is used as an optional plant/non-plant gate.
- BioCLIP is used for species matching when model weights are available.
- If model downloads fail, the app falls back to an offline-safe visual
  shortlist and clearly labels that limitation.
- Warm-lit plant photos such as mango/tulsi are deliberately not rejected by
  the local fallback gate.
- Species-specific prompt descriptions are generated for every plant, with extra hints for common confusions such as Tulsi vs Mint and Mango vs flowering plants.
- The uploaded filename is never used to choose a plant; identification is image-based.
- The generic CLIP gate is conservative and rejects an image only when it strongly favors a non-plant, reducing false rejection of real plants.

Plant library reference images
- Reference photos are resolved from Wikipedia/Wikimedia with redirect-aware lookup and search fallback.
- Images are downloaded and validated server-side before Streamlit displays them, reducing broken external-image/hotlink failures.
- If a remote photo is temporarily unavailable, every plant still gets a clean offline botanical reference card instead of an error.
- The library always remains usable.

My Plants
- Add a plant directly from the My Plants page without opening a profile first.
- Add reminders for watering, fertilizer, pesticide, weedicide, sunlight,
  rotating the plant, soil checks, pest inspection, misting/humidity, pruning,
  repotting or a custom task.
- Choose date, time and one-time/daily/weekly/every-30-days repeat.
- Mark reminders done or delete them.
- Reminders are session-scoped for the current browser session; they do not
  send OS notifications while the app is closed.

No OpenAI/Gemini API key is required.
