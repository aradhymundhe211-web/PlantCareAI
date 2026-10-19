# PlantCare AI — identification benchmark status

**Updated:** 2026-10-19  
**Repository:** aradhymundhe211-web/PlantCareAI  
**Purpose:** Report measured model performance and demo risks. This is not a guarantee for new photos or the live UI.

## Latest held-out photo benchmark

- Workflow: [Real-photo benchmark for 56 plant classes](https://github.com/aradhymundhe211-web/PlantCareAI/actions/runs/39142757633)
- Model: `hf-hub:imageomics/bioclip` (original BioCLIP; zero-shot image/text ranking)
- Images evaluated: **552/552**
- Classes represented: **56/56**
- Overall top-1 accuracy: **81.2%**
- Overall top-3 accuracy: **90.9%**
- Calathea Orbifolia had only 2 usable photos; each other class had 10.
- This benchmark evaluates the species ranker, not plant-presence rejection, the browser upload flow, live Streamlit startup, or every page.
- Do not claim 100% accuracy. A 56-profile database is not a custom-trained 56-class model.

## Per-class results

| Species | Photos | Top-1 | Top-3 |
|---|---:|---:|---:|
| Aloe Vera | 10 | 100% | 100% |
| Snake Plant | 10 | 10% | 30% |
| Money Plant | 10 | 100% | 100% |
| Spider Plant | 10 | 80% | 100% |
| Peace Lily | 10 | 90% | 90% |
| Areca Palm | 10 | 90% | 100% |
| Rubber Plant | 10 | 100% | 100% |
| ZZ Plant | 10 | 30% | 60% |
| Monstera | 10 | 90% | 100% |
| Heartleaf Philodendron | 10 | 90% | 100% |
| Fiddle Leaf Fig | 10 | 90% | 100% |
| Jade Plant | 10 | 90% | 100% |
| Lucky Bamboo | 10 | 70% | 80% |
| English Ivy | 10 | 90% | 100% |
| Boston Fern | 10 | 100% | 100% |
| Croton | 10 | 90% | 100% |
| Dracaena Marginata | 10 | 30% | 70% |
| Calathea Orbifolia | 2 | 50% | 100% |
| Prayer Plant | 10 | 90% | 100% |
| Dieffenbachia | 10 | 80% | 90% |
| Aglaonema | 10 | 30% | 70% |
| Anthurium | 10 | 100% | 100% |
| Syngonium | 10 | 70% | 80% |
| Peperomia | 10 | 80% | 80% |
| Tradescantia Zebrina | 10 | 100% | 100% |
| Dwarf Schefflera | 10 | 100% | 100% |
| Bird of Paradise | 10 | 100% | 100% |
| Rose | 10 | 80% | 100% |
| Hibiscus | 10 | 100% | 100% |
| Jasmine | 10 | 80% | 90% |
| Marigold | 10 | 90% | 100% |
| Bougainvillea | 10 | 80% | 90% |
| Chrysanthemum | 10 | 70% | 90% |
| Sunflower | 10 | 100% | 100% |
| Lotus | 10 | 90% | 100% |
| Tulsi | 10 | 70% | 80% |
| Mint | 10 | 100% | 100% |
| Curry Leaf | 10 | 70% | 80% |
| Lemongrass | 10 | 100% | 100% |
| Tomato | 10 | 90% | 100% |
| Chilli | 10 | 80% | 90% |
| Brinjal | 10 | 80% | 100% |
| Okra | 10 | 80% | 90% |
| Spinach | 10 | 20% | 30% |
| Cucumber | 10 | 100% | 100% |
| Mango | 10 | 40% | 80% |
| Guava | 10 | 90% | 100% |
| Papaya | 10 | 90% | 100% |
| Lemon | 10 | 30% | 50% |
| Neem | 10 | 100% | 100% |
| Pomegranate | 10 | 100% | 100% |
| Banana | 10 | 100% | 100% |
| Moringa | 10 | 90% | 90% |
| Amla | 10 | 80% | 100% |
| Coconut | 10 | 80% | 90% |
| Bamboo | 10 | 100% | 100% |

## Highest-risk classes in this sample

- Snake Plant: 10% top-1 / 30% top-3
- Spinach: 20% / 30%
- ZZ Plant: 30% / 60%
- Dracaena Marginata: 30% / 70%
- Aglaonema: 30% / 70%
- Lemon: 30% / 50%
- Mango: 40% / 80%

These estimates come from only 10 photos per class (2 for Calathea Orbifolia) and are not precise guarantees. They do show the model still confuses some visually similar plants.

## Live false-rejection reports still outstanding

The user previously reported the live website rejected real Marigold and Tulsi images as “No plant detected.” Those exact images have **not** been retested on the deployed site after the latest merge. Their benchmark results do not prove the complete live pipeline will accept them.

The Fortuner Legender negative test also remains outstanding on the live deployment. The benchmark does not certify non-plant rejection.

## Demo safety

Before presenting:
1. Wait for Streamlit Community Cloud to deploy the latest main commit and check logs.
2. Test the exact image planned for the demo on the live website.
3. Retest the original Marigold and Tulsi images and the Fortuner Legender car image.
4. If any real plant is rejected, do not claim it was fixed without retesting. If identification is ambiguous, show alternatives and visually compare traits.
5. Do not describe the result as a confirmed species or a calibrated probability.

## Next steps for a genuine accuracy improvement

1. Gather more independently sourced, labelled images per species, including leaf-only, whole-plant, flower, background and lighting variations.
2. Keep a held-out test set separate from prompt/model tuning.
3. Compare prompt-based BioCLIP with a properly trained and validated 56-class classifier if enough data is available.
4. Measure plant false-rejection and non-plant false-accept rates separately.
5. Re-run the full benchmark after each change and manually verify the live deployment.

**Current conclusion:** automated source tests pass, but species accuracy remains imperfect and live end-to-end verification is outstanding. Do not advertise 100% accuracy.
