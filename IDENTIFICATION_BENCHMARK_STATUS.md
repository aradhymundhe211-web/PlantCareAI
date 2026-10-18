# PlantCare AI — 56-species identification status

**Purpose:** live-demo risk guide based on the latest available one-photo-per-class BioCLIP benchmark and reported live tests. This is not a guarantee of performance on new images.

## Benchmark summary

- **49 of 56 species** had one downloadable research-grade test photo.
- **44/49 top-1 correct (89.8%)**; **47/49 top-3 correct (95.9%)**.
- **44 classes** passed top-1 on their single sample; **3** missed top-1 but appeared in top 3; **2** missed top 3; **7** had no test photo.
- The user previously reported that the live site rejected real Marigold and Tulsi photos. Their one-photo benchmark passes do not cancel those live reports.
- The benchmark tests the species ranker, not the complete live UI, camera upload, plant/non-plant gates, or every feature. Do not advertise 100% accuracy.

## Per-species results

| # | Species | Current evidence |
|---:|---|---|
| 1 | Aloe Vera | Benchmark pass (1 photo) |
| 2 | Snake Plant | Not benchmarked — no usable photo |
| 3 | Money Plant | Benchmark pass (1 photo) |
| 4 | Spider Plant | Benchmark pass (1 photo) |
| 5 | Peace Lily | Benchmark pass (1 photo) |
| 6 | Areca Palm | Not benchmarked — no usable photo |
| 7 | Rubber Plant | Benchmark pass (1 photo) |
| 8 | ZZ Plant | Top-1 failed; correct within top 3 |
| 9 | Monstera | Benchmark pass (1 photo) |
| 10 | Heartleaf Philodendron | Benchmark pass (1 photo) |
| 11 | Fiddle Leaf Fig | Benchmark pass (1 photo) |
| 12 | Jade Plant | Benchmark pass (1 photo) |
| 13 | Lucky Bamboo | Benchmark pass (1 photo) |
| 14 | English Ivy | Benchmark pass (1 photo) |
| 15 | Boston Fern | Benchmark pass (1 photo) |
| 16 | Croton | Benchmark pass (1 photo) |
| 17 | Dracaena Marginata | Not benchmarked — no usable photo |
| 18 | Calathea Orbifolia | Benchmark pass (1 photo) |
| 19 | Prayer Plant | Top-1 failed; correct within top 3 |
| 20 | Dieffenbachia | Benchmark pass (1 photo) |
| 21 | Aglaonema | Failed top-1 and top-3 |
| 22 | Anthurium | Benchmark pass (1 photo) |
| 23 | Syngonium | Benchmark pass (1 photo) |
| 24 | Peperomia | Benchmark pass (1 photo) |
| 25 | Tradescantia Zebrina | Benchmark pass (1 photo) |
| 26 | Dwarf Schefflera | Not benchmarked — no usable photo |
| 27 | Bird of Paradise | Benchmark pass (1 photo) |
| 28 | Rose | Benchmark pass (1 photo) |
| 29 | Hibiscus | Not benchmarked — no usable photo |
| 30 | Jasmine | Benchmark pass (1 photo) |
| 31 | Marigold | Benchmark pass (1 photo); user reported live false rejection |
| 32 | Bougainvillea | Benchmark pass (1 photo) |
| 33 | Chrysanthemum | Benchmark pass (1 photo) |
| 34 | Sunflower | Benchmark pass (1 photo) |
| 35 | Lotus | Benchmark pass (1 photo) |
| 36 | Tulsi | Benchmark pass (1 photo); user reported live false rejection |
| 37 | Mint | Benchmark pass (1 photo) |
| 38 | Curry Leaf | Not benchmarked — no usable photo |
| 39 | Lemongrass | Benchmark pass (1 photo) |
| 40 | Tomato | Benchmark pass (1 photo) |
| 41 | Chilli | Benchmark pass (1 photo) |
| 42 | Brinjal | Benchmark pass (1 photo) |
| 43 | Okra | Benchmark pass (1 photo) |
| 44 | Spinach | Failed top-1 and top-3 |
| 45 | Cucumber | Benchmark pass (1 photo) |
| 46 | Mango | Top-1 failed; correct within top 3 |
| 47 | Guava | Benchmark pass (1 photo) |
| 48 | Papaya | Benchmark pass (1 photo) |
| 49 | Lemon | Not benchmarked — no usable photo |
| 50 | Neem | Benchmark pass (1 photo) |
| 51 | Pomegranate | Benchmark pass (1 photo) |
| 52 | Banana | Benchmark pass (1 photo) |
| 53 | Moringa | Benchmark pass (1 photo) |
| 54 | Amla | Benchmark pass (1 photo) |
| 55 | Coconut | Benchmark pass (1 photo) |
| 56 | Bamboo | Benchmark pass (1 photo) |

## Live demo recommendations

**First candidates to test before the presentation:** Aloe Vera, Money Plant, Spider Plant, Rubber Plant, Jade Plant, Monstera, and Peace Lily. Their single benchmark images ranked correctly, but each must still be checked on the live deployment using the exact photo you will present.

**Do not use as a “guaranteed” demo:** Marigold or Tulsi until retested live, because false rejection was reported. Avoid Aglaonema and Spinach because their benchmark samples failed even top 3. ZZ Plant, Prayer Plant, and Mango are risky because the benchmark's top-ranked result was wrong.

## How to close the gaps

1. Gather at least 5–10 varied, independently sourced photos per class (whole plant, leaf close-up, varied backgrounds/lighting), with a held-out set not used to tune prompts.
2. Tune prompts or use a validated 56-class fine-tuned model against the error cases; rerun the full benchmark after every change.
3. Measure non-plant rejection separately using cars, objects, screenshots, and blurry photos.
4. Test the deployed Streamlit website with the exact gallery/camera inputs and all seven pages after each deployment.

**Accuracy wording:** these results support only a preliminary benchmark claim. They do not establish 100% accuracy, and one correct photo is not proof that a species reliably works in the wild.
