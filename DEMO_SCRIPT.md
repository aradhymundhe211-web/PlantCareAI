# PlantCare AI — Live Demonstration Script

## Before the presentation (5–10 minutes)
- Open the deployed website and wait for it to finish loading.
- Test one clear, well-lit photo of a supported plant (a whole plant with visible leaves is preferable).
- Test one non-plant photo, such as a car, to demonstrate the rejection safeguard.
- Confirm each page opens: Identify Plant, Visual Health Monitoring, plant library/profile, My Plants/reminders, Plant Health Copilot, and About.
- Keep backup plant photos locally available. If the live model fails or gives an uncertain result, explain it honestly and move to another prepared photo. Do not claim an incorrect result is correct.
- Use photos you have permission to show, and avoid relying on internet access for the images during the demo.

## Spoken script (about 4 minutes)

### 1. Introduction (30 seconds)
“Good morning. Today I’m presenting PlantCare AI, a plant-care assistant designed to help people identify supported plants, learn their growing requirements, and make more informed care decisions. The idea is to make useful plant information easier to access through one simple website.”

### 2. Identify Plant (60 seconds)
“I’ll start with Identify Plant. I’m uploading a clear plant photo. The vision model compares the image with descriptions of the 56 plants in our reference library and returns a likely match with supporting plant information. I can review the suggested match and its alternatives instead of treating every result as certain.”

[Upload the prepared plant photo. Wait for the result, then show the common name, scientific name, and care profile.]

“Image-based identification can be affected by lighting, focus, plant age, and similar-looking species, so the result should be visually checked. This is a supported-species matcher, not a guarantee that every plant in the world can be identified.”

### 3. Non-plant check (30 seconds)
“Next, I’ll use a non-plant image to show the screening safeguards. The system is designed to reject clear non-plant images and to avoid presenting an uncertain match as a confirmed identification.”

[Upload the prepared non-plant photo. Describe the actual result shown on screen. If it is not rejected, do not claim that the test passed; note it as a case for improvement.]

### 4. Visual Health Monitoring (40 seconds)
“Visual Health Monitoring provides a preliminary visual screen for possible leaf or image concerns. It is a screening aid, not a laboratory test or a confirmed plant-disease diagnosis. I would combine its output with physical checks of soil moisture, drainage, light, and the plant’s recent care history.”

[Show the feature using a prepared image and read the actual on-screen result.]

### 5. Plant profiles and care planning (45 seconds)
“The plant profiles bring together identification clues, scientific names, light, watering, soil, and other general care guidance. In My Plants, I can keep track of plants and create care reminders, such as watering or checking soil moisture.”

[Open a plant profile, then demonstrate adding a plant or creating a reminder if the controls are available.]

“Please note that in this version, saved plants, reminders, and journal entries are session-based, so they may not persist after a refresh or a new session.”

### 6. Plant Health Copilot (40 seconds)
“Plant Health Copilot helps organise observations such as yellow leaves, soil that stays wet, or visible pests into possible causes and practical next steps. Its current guidance is profile-grounded and rule-based. It does not confirm a disease or replace an experienced horticulturist.”

[Select a plant and a couple of symptoms, complete the form, and show the possible causes and action plan.]

### 7. Closing (20 seconds)
“To summarise, PlantCare AI combines plant matching, reference care information, visual screening, reminders, and guided troubleshooting in one place. Our next priority is continued testing with diverse, labelled real-world photos, measuring both correct plant identification and incorrect non-plant acceptance, and improving reliability based on those results. Thank you.”

## If a feature fails during the live demo
Say: “This test has exposed a limitation in the current version. We’re recording it as a test case rather than hiding the result. The next step is to reproduce it, test a fix, and verify that the fix improves the benchmark without breaking other cases.”

## Accuracy wording
The preliminary benchmark recorded 89.8% top-1 and 95.9% top-3 accuracy on 49 photos covering 49 supported classes. It was a small, preliminary sample and does not establish real-world accuracy across all 56 classes, all camera conditions, or non-plant rejection. Do not describe the system as 100% accurate.
