PlantCare AI — Updated Interface Package
Made by Aradhy Mundhe

This package contains the Streamlit app, plant data, requirements, model notes, and theme configuration.

Interface updates in this revision:
- Kept the white + botanical green foundation for a clear nature-inspired interface.
- Added a restrained lime/pista accent to the logo and hero highlights rather than turning the whole page yellow.
- Created a custom leaf emblem for the sidebar brand.
- Increased general typography, card text, navigation button sizing, and section heading sizes for readability.
- Simplified the Home tab and removed the entire “Smart care tools” and “PlantCare AI toolkit” sections as requested.
- Reworked Home into a focused welcome hero, three main destinations, and a four-step plant-care journey.
- Added friendly, relevant plant-care emojis consistently across the Home experience.

Run locally with: streamlit run app.py

The app uses Python and Streamlit. Model availability and identification quality depend on the deployment environment and image quality; no photo-based identification should be treated as guaranteed.


Competition-readiness fixes (16 October 2026):
- Search selection now opens the selected plant profile even if the search field retains an earlier partial query.
- General-object screening uses more conservative rejection thresholds to reduce false rejection of real plants photographed with pots/background objects.
- If the optional general ImageNet screening model cannot load, the app no longer automatically labels the image as non-plant; BioCLIP and conservative checks still run.

Important: image identification is probabilistic and must be tested with the actual competition photos and deployed environment. This package has passed static Python syntax and plant-data checks, but that does not prove the cloud model downloads or every camera/gallery image will work in all environments.
