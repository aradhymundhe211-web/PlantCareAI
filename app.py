from __future__ import annotations

import json
import io
import math
import re
import os
import sys
from pathlib import Path
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
import uuid
from typing import Dict, List, Tuple

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from plantcare_core import assess_plant_health, answer_copilot_question, validate_plant_records, decide_vision_gate

import numpy as np
import requests
import streamlit as st
from PIL import Image, ImageOps, ImageFilter, ImageDraw


APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "plant_data.json"
INDIA_TZ = ZoneInfo("Asia/Kolkata")

def india_now_naive() -> datetime:
    """Return Indian local time as a naive datetime for legacy reminder storage."""
    return datetime.now(INDIA_TZ).replace(tzinfo=None)

def time_from_12h(hour_12: int, minute: int, period: str) -> time:
    """Convert an explicit 12-hour clock selection into Python's 24-hour time."""
    hour_24 = hour_12 % 12
    if period.upper() == "PM":
        hour_24 += 12
    return time(hour_24, minute)

st.set_page_config(
    page_title="PlantCare AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Design system — intentionally light, green and mobile-friendly.
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    :root{--g:#168044;--gd:#075b35;--gm:#edf6df;--ink:#092f24;--muted:#405e50;--line:#d7e5c5;--bg:#fbfaed;--white:#fffef7;--lime:#dff39c}
    .stApp{background:linear-gradient(180deg,#f5f8e9 0,#fffdf1 48%);color:var(--ink);font-size:1.15rem}
    .stMarkdown p,.stMarkdown li{font-size:1.04rem;line-height:1.68}
    .stMarkdown h1{font-size:2.55rem!important;letter-spacing:-.025em}
    .stMarkdown h2{font-size:2rem!important}
    .stMarkdown h3{font-size:1.4rem!important}
    label,[data-testid="stWidgetLabel"] p{font-size:1rem!important;font-weight:700!important}
    .stCaption,[data-testid="stCaptionContainer"]{font-size:.9rem!important}
    [data-testid="stHeader"]{background:rgba(255,255,255,.94)}
    [data-testid="stSidebar"]{background:linear-gradient(180deg,#003c2d 0%,#002f24 100%)!important;border-right:1px solid #164f3c!important}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] div,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] *{color:#f5fff7!important}
    [data-testid="stSidebar"] button{background:transparent!important;border:1px solid transparent!important;color:#f5fff7!important;border-radius:12px!important;min-height:46px!important}
    [data-testid="stSidebar"] button:hover{background:#0a6345!important;border-color:#31825e!important}
    [data-testid="stSidebar"] button[kind="primary"]{background:#0b754b!important;color:#fff!important}
    [data-testid="stSidebar"] *{color:var(--ink)}
    .pc-brand{display:flex;align-items:center;gap:12px;padding:6px 4px 22px}
    .pc-logo{width:58px;height:58px;border-radius:19px;background:linear-gradient(145deg,#e8f7b9,#f8ffe8);border:1px solid #c6e49a;display:flex;align-items:center;justify-content:center;font-size:[...]
    .pc-brand-title{font-size:1.38rem;font-weight:950;line-height:1.05;letter-spacing:-.02em}.pc-brand-sub{font-size:.88rem;color:var(--muted);margin-top:6px}
    .pc-nav-title{font-size:.73rem;font-weight:800;letter-spacing:.08em;color:#6a7d71;text-transform:uppercase;margin:4px 0 8px}
    .pc-hero{color:#fff;border-radius:28px;padding:34px 36px;margin-bottom:22px;background:radial-gradient(circle at 92% 10%,rgba(255,255,255,.35),transparent 25%),linear-gradient(135deg,#0b6a38,#[...]
    .pc-hero h1{margin:0;color:#fff;font-size:clamp(2rem,4vw,3.25rem);line-height:1;letter-spacing:-.035em}.pc-hero p{margin:15px 0 0;color:rgba(255,255,255,.97);max-width:850px;line-height:1.65;f[...]
    .pc-pills{display:flex;flex-wrap:wrap;gap:9px;margin-top:18px}.pc-pill{border:1px solid rgba(255,255,255,.32);background:rgba(255,255,255,.16);border-radius:999px;padding:8px 13px;color:#fff;f[...]
    .pc-card{background:#fff;border:1px solid var(--line);border-radius:22px;padding:21px;box-shadow:0 10px 28px rgba(22,55,35,.055);height:100%}.pc-card h3{margin:0 0 10px;color:var(--ink);font-s[...]
    .pc-stat{background:#fff;border:1px solid var(--line);border-radius:18px;padding:18px 20px;box-shadow:0 8px 22px rgba(22,55,35,.05)}.pc-stat-num{font-size:1.9rem;font-weight:950;color:var(--gd[...]
    .pc-title{font-size:1.72rem;font-weight:950;color:var(--ink);margin:30px 0 15px}.pc-result{background:linear-gradient(180deg,#f5fcf7,#fff);border:1px solid #c9e5d1;border-radius:24px;padding:2[...]
    .pc-info{background:#f5fbf7;border:1px solid var(--line);border-radius:16px;padding:14px 16px;line-height:1.5}.pc-warning{background:#fff8e8;border:1px solid #f0dd9b;color:#6e5513;border-radiu[...]
    .pc-footer{text-align:center;color:#7b8c82;font-size:.78rem;padding:35px 0 15px}
    .pc-page-byline{display:flex;align-items:center;justify-content:flex-end;gap:7px;color:#527063;font-size:.78rem;font-weight:850;margin:0 2px 12px}.pc-page-byline strong{color:#0b6b39}.pc-safet[...]
    .stButton>button{border-radius:15px!important;min-height:50px!important;border:1px solid #cfe2d5!important;font-size:1.02rem!important;font-weight:850!important;background:#fff!important;color[...]
    .stButton>button:hover{border-color:#7ab58d!important;color:#0b6b39!important}
    .stButton>button[kind="primary"]{background:linear-gradient(135deg,#168d4d,#0b6b39)!important;color:#fff!important;border:0!important;box-shadow:0 8px 18px rgba(22,141,77,.18)}
    [data-testid="stFileUploader"]{background:#fff;border:1px dashed #b7d4bf;border-radius:18px;padding:4px}
    [data-baseweb="select"]>div{background:#fff!important;border-radius:12px!important;border:1px solid #cfe2d5!important;box-shadow:none!important}[data-baseweb="select"] *{color:#173225!importan[...]
    [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"]{background:#fff!important;color:#173225!important;border:1px solid #cfe2d5!important}
    [role="option"]{background:#fff!important;color:#173225!important}
    [role="option"][aria-selected="true"], [role="option"]:hover{background:#eaf8ef!important;color:#0b6b39!important}
    input, textarea{background:#fff!important;color:#173225!important;border-color:#cfe2d5!important;color-scheme:light!important}
    [data-testid="stFileUploaderDropzone"]{background:#fff!important;border:1px dashed #9bc9aa!important}
    [data-testid="stFileUploaderDropzone"] button{background:#fff!important;color:#0b6b39!important;border:1px solid #9bc9aa!important}
    [data-testid="stCameraInput"]{background:#fff!important;border:1px solid #cfe2d5!important;border-radius:18px!important;padding:10px!important}
    [data-testid="stCameraInput"], [data-testid="stCameraInput"] section, [data-testid="stCameraInput"]>div{background:#fff!important;color:#173225!important;border:1px solid #cfe2d5!important;bor[...]
    [data-testid="stCameraInput"] button, [data-testid="stCameraInput"] button *{background:#138a4b!important;color:#fff!important;border:0!important;border-radius:12px!important}
    [data-testid="stCameraInput"] input{background:#fff!important;color:#173225!important}
    [data-testid="stTabs"] button{background:#fff!important;color:#173225!important;border-radius:12px 12px 0 0!important}
    /* Accessibility pass: consistently readable text, controls and tabs */
    .stApp, .stApp p, .stApp li, .stApp label,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stWidgetLabel"] p,
    [data-testid="stCaptionContainer"],
    [data-testid="stFileUploaderDropzone"] span {font-size:1.08rem!important;line-height:1.55!important}
    .stApp h1{font-size:clamp(2.15rem,3vw,3.1rem)!important}
    .stApp h2{font-size:clamp(1.75rem,2.4vw,2.35rem)!important}
    .stApp h3{font-size:clamp(1.35rem,1.7vw,1.7rem)!important}
    [data-testid="stTabs"] button{font-size:1.12rem!important;font-weight:800!important;padding:14px 20px!important;min-height:54px!important}
    .stButton>button{font-size:1.08rem!important;min-height:52px!important;padding:.7rem 1.1rem!important}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] button{font-size:1.02rem!important;line-height:1.4!important}
    .pc-card{padding:24px!important;border-radius:20px!important}
    .pc-card h3{font-size:1.35rem!important}
    .pc-card p{font-size:1.08rem!important;line-height:1.65!important}
    .pc-home-stat .label,.pc-mini span,.pc-safety,.pc-upload-sub{font-size:1rem!important;line-height:1.5!important}
    .pc-title{font-size:1.9rem!important}
    @media(max-width:900px){.pc-home-hero{padding:24px!important;min-height:240px!important}.pc-home-hero h1{font-size:2.25rem!important}.pc-pills{gap:8px}.pc-pill{font-size:.95rem!important}}

    [data-testid="stTabs"] button[aria-selected="true"]{color:#0b6b39!important;border-bottom-color:#138a4b!important}
    div[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:14px}

    .pc-upload-card{background:#fff;border:1px solid #cfe2d5;border-radius:16px;padding:14px 16px;margin-bottom:8px}.pc-upload-title{font-weight:900;color:#0b6b39}.pc-upload-sub{font-size:.82rem;[...]
    .pc-score{display:flex;align-items:center;gap:14px;background:linear-gradient(135deg,#f0fbf4,#fff);border:1px solid #cce5d3;border-radius:18px;padding:15px 17px}.pc-score-ring{width:58px;height:5[...]
    @media(max-width:900px){.pc-hero{padding:25px 22px}.pc-hero h1{font-size:2.2rem}}



    /* Accessibility pass: larger text, navigation, tabs, and card spacing */
    html, body, [class*="css"], .stApp { font-size: 19px !important; }
    .stMarkdown p, .stMarkdown li, .stText, .stWrite, [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li { font-size: 1.12rem !important; line-height: 1.72 !important; }
    .stCaption, [data-testid="stCaptionContainer"], small { font-size: 1rem !important; line-height: 1.55 !important; }
    .stMarkdown h1, h1 { font-size: 2.8rem !important; line-height: 1.12 !important; }
    .stMarkdown h2, h2 { font-size: 2.25rem !important; line-height: 1.18 !important; }
    .stMarkdown h3, h3 { font-size: 1.65rem !important; line-height: 1.25 !important; }
    label, [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] { font-size: 1.12rem !important; line-height: 1.4 !important; font-weight: 750 !important; }
    input, textarea, [data-baseweb="select"], [data-baseweb="input"] { font-size: 1.12rem !important; min-height: 48px !important; }
    [data-testid="stTabs"] [role="tablist"] { gap: 10px !important; }
    [data-testid="stTabs"] button, [data-baseweb="tab"] { font-size: 1.14rem !important; font-weight: 800 !important; min-height: 54px !important; padding: 13px 20px !important; }
    .stButton > button, [data-testid="stDownloadButton"] button, [data-testid="stFormSubmitButton"] button { font-size: 1.12rem !important; min-height: 54px !important; padding: 12px 18px !import[...]
    [data-testid="stSidebar"] { min-width: 250px !important; }
    [data-testid="stSidebar"] .stButton > button { font-size: 1.08rem !important; min-height: 52px !important; padding: 12px 15px !important; }
    [data-testid="stSidebar"] .pc-brand-title { font-size: 1.5rem !important; }
    [data-testid="stSidebar"] .pc-brand-sub { font-size: 1rem !important; }
    .pc-card, .pc-mini, .pc-stat, .pc-result, .pc-featured { padding: 24px !important; }
    .pc-card h3, .pc-featured-body h3 { font-size: 1.45rem !important; line-height: 1.3 !important; }
    .pc-card p, .pc-featured-body p { font-size: 1.1rem !important; line-height: 1.65 !important; }
    .pc-title { font-size: 1.95rem !important; line-height: 1.25 !important; }
    .pc-stat-num { font-size: 2.25rem !important; }
    .pc-stat-label, .pc-mini span, .pc-home-stat .label { font-size: 1.04rem !important; line-height: 1.45 !important; }
    .pc-mini b { font-size: 1.4rem !important; }
    .pc-pill, .pc-badge, .pc-check { font-size: 1rem !important; padding: 9px 14px !important; }
    .pc-page-byline { font-size: .98rem !important; }
    .pc-home-hero .eyebrow { font-size: 1.04rem !important; }
    .pc-home-hero .tagline { font-size: 1.35rem !important; }
    .pc-home-hero .copy { font-size: 1.22rem !important; }
    .pc-hero { padding: 30px !important; border-radius: 24px !important; }
    .pc-hero p { font-size: 1.18rem !important; line-height: 1.7 !important; }
    .pc-card, .pc-mini, .pc-stat, .pc-result, .pc-featured {
      border-radius: 19px !important;
      padding: 23px !important;
      border-color: var(--pc-border) !important;
    }
    .pc-card h3, .pc-featured-body h3 { font-size: 1.42rem !important; line-height: 1.35 !important; }
    .pc-card p, .pc-featured-body p { font-size: 1.08rem !important; line-height: 1.65 !important; }
    .pc-result-name { font-size: clamp(1.9rem, 3vw, 2.6rem) !important; }
    .pc-scientific, .pc-library-count, .pc-safety, .pc-upload-sub,
    .pc-analyze-box span, .pc-photo-placeholder span { font-size: 1rem !important; line-height: 1.55 !important; }
    .stExpander details summary, [data-testid="stExpander"] summary {
      min-height: 54px !important;
      font-size: 1.12rem !important;
      min-height: 54px !important;
      font-weight: 800 !important;
    }
    [data-testid="stMetric"] label, [data-testid="stMetricValue"],
    [data-testid="stMetricDelta"] { font-size: 1.08rem !important; }
    [data-testid="stFileUploaderDropzone"] { min-height: 130px !important; }
    [data-testid="stFileUploaderDropzone"] * { font-size: 1.05rem !important; }
    [data-testid="stDataFrame"] * { font-size: 1rem !important; }
    .pc-footer { font-size: .95rem !important; line-height: 1.5 !important; }
    @media (max-width: 900px) {
      [data-testid="stMain"] .block-container { padding: 1.1rem 1rem 2rem !important; }
      .stMarkdown p, .stMarkdown li, [data-testid="stMarkdownContainer"] p,
      [data-testid="stMarkdownContainer"] li { font-size: 1.06rem !important; }
      .stMarkdown h1, h1 { font-size: 2.25rem !important; }
      .stMarkdown h2, h2 { font-size: 1.9rem !important; }
      .stMarkdown h3, h3 { font-size: 1.45rem !important; }
      [data-testid="stTabs"] button[role="tab"], [data-baseweb="tab"] {
        min-height: 50px !important; padding: 10px 12px !important; font-size: 1rem !important;
      }
      .pc-card, .pc-mini, .pc-stat, .pc-result { padding: 17px !important; }
      .pc-home-hero { min-height: 245px !important; }
    }


    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('\n<style>\n:root{--pc-forest:#003d2d;--pc-deep:#002e23;--pc-green:#137b43;--pc-lime:#d9edaa;--pc-cream:#f8f7e9;--pc-border:#d8e5c4}\n[data-testid="stSidebar"]{min-width:245px!importa[...]

# -----------------------------------------------------------------------------
# Data
# -----------------------------------------------------------------------------
@st.cache_data

def load_plants() -> List[dict]:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

PLANTS = load_plants()
PLANT_DATA_ERRORS = validate_plant_records(PLANTS, expected_count=56)
if PLANT_DATA_ERRORS:
    # Keep the application from presenting a broken library as valid.
    raise ValueError("Plant library validation failed: " + " ".join(PLANT_DATA_ERRORS))
PLANT_BY_NAME = {p["common_name"]: p for p in PLANTS}

def load_my_plants() -> List[str]:
    # Session-scoped by design: this avoids different online visitors sharing
    # one server-side JSON file.
    return []

def save_my_plants(items: List[str]) -> None:
    # Kept as a no-op compatibility helper for the local UI.
    return None

if "my_plants" not in st.session_state:
    st.session_state.my_plants = load_my_plants()
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "reminders" not in st.session_state:
    st.session_state.reminders = []
if "notified_reminder_ids" not in st.session_state:
    st.session_state.notified_reminder_ids = set()
if "health_copilot_assessment" not in st.session_state:
    st.session_state.health_copilot_assessment = None
if "plant_journal" not in st.session_state:
    # Session-scoped by design; no claim of cross-session persistence.
    st.session_state.plant_journal = []

@st.fragment(run_every="10s")
def render_due_reminder_alerts():
    """Refresh due reminders while My Plants is open; attempt browser audio/voice."""
    now_local = india_now_naive()
    due = []
    for reminder in st.session_state.get("reminders", []):
        try:
            due_time = datetime.fromisoformat(reminder["when"])
        except (KeyError, TypeError, ValueError):
            continue
        if not reminder.get("done") and due_time <= now_local:
            due.append(reminder)
    if not due:
        return
    st.warning("⏰ Care reminder due: " + " · ".join(f"{r.get('task', 'Care task')} for {r.get('plant', 'your plant')}" for r in due))
    fresh = [r for r in due if r.get("id") not in st.session_state.notified_reminder_ids]
    if fresh:
        for reminder in fresh:
            st.session_state.notified_reminder_ids.add(reminder.get("id"))
        announcements = [f"Care reminder. {r.get('task', 'Care task')} for {r.get('plant', 'your plant')}." for r in fresh]
        payload = json.dumps(announcements).replace("<", "\\u003c")
        # Browser autoplay rules vary. The visible due alert remains the fallback.
        st.components.v1.html(f'''<div style="font:16px sans-serif;color:#075b35">🔔 Reminder alert attempted. If your browser blocks automatic audio, click “Speak due reminders”.</div>
<scri[...]
