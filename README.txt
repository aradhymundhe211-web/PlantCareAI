PLANTCARE AI — COMPETITION BUILD V13 FINAL CONSOLIDATED
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
- BioCLIP is used for biology-focused species matching when model weights are available.
- Camera and gallery images go through the same EXIF/orientation normalization and multi-view analysis.
- The model checks the original image plus center/upper/focused views so a plant does not need to fill the entire frame.
- The uploaded filename is never used to choose a plant; identification is image-based.
- A separate BioCLIP plant/object screen is used only as a strong final non-plant rejection check, preventing the old conservative gate from rejecting genuine plants before identification.
- Species-specific prompts and reference photos are used to improve close matches across the 56-plant library.
- If BioCLIP cannot load, the app does not invent a species from color alone; it falls back to a clearly labelled local shortlist when meaningful botanical clues are supplied.
- The app does not claim 100% accuracy; visually similar species can require confirmation.

PlantCare analysis
- After identification, the app performs a visual foliage-health screen for green, yellowing, brown/damaged and dark areas.
- It provides a visual water-stress check, disease/stress inspection guidance, pest-inspection guidance, species light guidance and growth-tracking guidance.
- It also shows the species-specific watering, light, humidity, soil, fertilizer, pest and disease information from the plant library.
- A single photograph cannot directly measure soil moisture, fertilizer concentration, growth rate or sunlight exposure, and it cannot confirm a pathogen. The app therefore labels these as checks/guidance instead of presenting guesses as measurements.
- For visible damage, the app recommends close inspection rather than automatically telling the user to apply pesticides or other treatments.

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
