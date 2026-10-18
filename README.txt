PlantCare AI — deployment and usage guide

Purpose
- Streamlit website for 56 plant profiles, photo-based species suggestions, visual colour-pattern screening, care checklists, and a profile-grounded Plant Health Copilot.
- Both camera photos and gallery uploads use the same image normalization and validation pipeline.
- No paid AI inference API key is required.

Model selection
- Official model pages: https://huggingface.co/imageomics/bioclip and https://huggingface.co/imageomics/bioclip-2. See THIRD_PARTY_NOTICES.txt for licence pointers.
- Default: original BioCLIP (`hf-hub:imageomics/bioclip`) through OpenCLIP. Its model repository is about 602 MB overall; the main checkpoint is roughly 599 MB.
- BioCLIP 2 is available as an opt-in on hosts with enough memory/disk, using `PLANTCARE_MODEL_ID=hf-hub:imageomics/bioclip-2`. Its main checkpoint is about 1.71 GB and the repository totals about 3.42 GB because it contains alternative checkpoint formats.
- Do not enable BioCLIP 2 on a constrained free host without testing clean startup, peak memory, inference latency, and image-level accuracy. To opt in, define `PLANTCARE_MODEL_ID` as `hf-hub:imageomics/bioclip-2` in the server environment or Streamlit secrets. Model weights download at runtime; they are not bundled in this ZIP.
- Model choice is explicit and no silent fallback to a larger checkpoint occurs. If model loading fails, the app reports identification unavailable rather than inventing a species.

Environment
- Python target: 3.12 (`.python-version`).
- `requirements.txt` pins CPU-only PyTorch and matching torchvision to avoid attempting to install CUDA packages on a CPU-only hosting service.
- The first model use requires internet access and enough disk/cache space. Every visitor does not download the entire model; inference happens on the Streamlit server.

Run locally
1. Create/activate a Python 3.12 virtual environment.
2. Install dependencies: `python -m pip install -r requirements.txt`
3. Run tests: `python -m unittest discover -s . -v`
4. Start the app: `streamlit run app.py`

Identification pipeline
1. Image quality screening.
2. General ImageNet object screening when its torchvision weights are available.
3. BioCLIP plant-versus-object and plant-versus-document checks.
4. Only images that pass positive plant-presence evidence proceed to 56-species zero-shot ranking.
5. An uncertain or unavailable check does not receive a species name.

Important limits
- Gate thresholds are initial hand-set screening thresholds, not statistically calibrated probabilities. Test and tune them using independent real plant photos and non-plant photos before claiming accuracy.
- BioCLIP ranks the supported candidate species; it is not a guarantee that the true species is among the 56 labels or that the top-ranked class is correct.
- No independent labelled test set covering all 56 species is included. Do not claim a validated accuracy percentage until such a test has been run.
- Visual health screening detects rough colour patterns only. It does not segment leaves, diagnose a disease, reliably detect pests, or measure soil moisture/nutrients.
- The Copilot retrieves advice from bundled plant profiles and transparent rules. It is not a general-purpose generative language model or a laboratory diagnosis.
- Free hosting has finite memory, CPU, disk, bandwidth, startup time, and availability. Unlimited uptime or inference cannot be promised.

After deploying
- Watch Streamlit logs for dependency, model-download, and memory failures.
- Test a clear plant photo, leaf close-up, flower, the Fortuner/car image, dashboard screenshots, unrelated objects, a blurry photo, and the Copilot.
- If a real plant is rejected, test the model-gate scores against a separate set of labelled plant photos before loosening thresholds.
