# MISSION 100 — Study Command Centre

This Streamlit deployment has been repurposed from PlantCareAI to Mission 100. The original PlantCareAI source is preserved on the Git branch `backup/plantcareai-before-mission100-2026-10-20`.

## Features
- Class 10 study task board and exam timetable
- Arithmetic Progressions mastery tracker
- Subject syllabus tracker
- 25-minute focus sessions
- XP, long-term goals and weekly reflection
- JSON progress backup and restore

## Streamlit setup
Main file: `app.py`

In the Streamlit app's **Settings → Secrets**, add your own credentials (do not commit them to GitHub):

```toml
[access]
password = "replace-with-a-long-unique-password"
device_keys = ["unique-secret-key-for-your-device"]
```

The app will remain locked until valid secrets are configured. Use a long unique password and a different private device key for each device you intend to authorize. Never share these credentials.

## Privacy and data notes
- The app's password/device-key gate is an extra access layer; also restrict sharing/access in the hosting provider if that option is available.
- A secret URL alone is not access control.
- Local JSON progress files may be reset by host restarts or redeploys. Download progress backups regularly.
- The dashboard organizes preparation but cannot guarantee exam marks.

## Recovery
To restore the previous PlantCareAI entry point, open the repository's branch `backup/plantcareai-before-mission100-2026-10-20` and restore the previous `app.py`, `requirements.txt`, and any other files needed from that branch.

## Local run
Install requirements with `pip install -r requirements.txt`, then run `streamlit run app.py`.
