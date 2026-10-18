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
    .pc-logo{width:58px;height:58px;border-radius:19px;background:linear-gradient(145deg,#e8f7b9,#f8ffe8);border:1px solid #c6e49a;display:flex;align-items:center;justify-content:center;font-size:30px;box-shadow:0 8px 20px rgba(10,106,57,.14)}
    .pc-brand-title{font-size:1.38rem;font-weight:950;line-height:1.05;letter-spacing:-.02em}.pc-brand-sub{font-size:.88rem;color:var(--muted);margin-top:6px}
    .pc-nav-title{font-size:.73rem;font-weight:800;letter-spacing:.08em;color:#6a7d71;text-transform:uppercase;margin:4px 0 8px}
    .pc-hero{color:#fff;border-radius:28px;padding:34px 36px;margin-bottom:22px;background:radial-gradient(circle at 92% 10%,rgba(255,255,255,.35),transparent 25%),linear-gradient(135deg,#0b6a38,#15914f 55%,#62bf7e);box-shadow:0 18px 45px rgba(20,120,64,.16)}
    .pc-hero h1{margin:0;color:#fff;font-size:clamp(2rem,4vw,3.25rem);line-height:1;letter-spacing:-.035em}.pc-hero p{margin:15px 0 0;color:rgba(255,255,255,.97);max-width:850px;line-height:1.65;font-size:1.16rem}
    .pc-pills{display:flex;flex-wrap:wrap;gap:9px;margin-top:18px}.pc-pill{border:1px solid rgba(255,255,255,.32);background:rgba(255,255,255,.16);border-radius:999px;padding:8px 13px;color:#fff;font-size:.92rem;font-weight:850}
    .pc-card{background:#fff;border:1px solid var(--line);border-radius:22px;padding:21px;box-shadow:0 10px 28px rgba(22,55,35,.055);height:100%}.pc-card h3{margin:0 0 10px;color:var(--ink);font-size:1.22rem}.pc-card p{margin:0;color:var(--muted);line-height:1.65;font-size:1.02rem}
    .pc-stat{background:#fff;border:1px solid var(--line);border-radius:18px;padding:18px 20px;box-shadow:0 8px 22px rgba(22,55,35,.05)}.pc-stat-num{font-size:1.9rem;font-weight:950;color:var(--gd)}.pc-stat-label{font-size:.92rem;color:var(--muted);margin-top:7px}
    .pc-title{font-size:1.72rem;font-weight:950;color:var(--ink);margin:30px 0 15px}.pc-result{background:linear-gradient(180deg,#f5fcf7,#fff);border:1px solid #c9e5d1;border-radius:24px;padding:23px;box-shadow:0 10px 28px rgba(22,55,35,.06)}.pc-result-name{font-size:clamp(1.7rem,3vw,2.35rem);font-weight:950;color:var(--gd);margin:0}.pc-scientific{color:var(--muted);font-size:.93rem;margin-top:5px}.pc-badge{display:inline-block;background:var(--gm);color:#116335;border:1px solid #cde8d4;border-radius:999px;padding:6px 10px;font-size:.82rem;font-weight:850;margin-top:10px}
    .pc-info{background:#f5fbf7;border:1px solid var(--line);border-radius:16px;padding:14px 16px;line-height:1.5}.pc-warning{background:#fff8e8;border:1px solid #f0dd9b;color:#6e5513;border-radius:16px;padding:14px 16px}.pc-error{background:#fff1f1;border:1px solid #f1c5c5;color:#8a2020;border-radius:16px;padding:14px 16px}
    .pc-footer{text-align:center;color:#7b8c82;font-size:.78rem;padding:35px 0 15px}
    .pc-page-byline{display:flex;align-items:center;justify-content:flex-end;gap:7px;color:#527063;font-size:.78rem;font-weight:850;margin:0 2px 12px}.pc-page-byline strong{color:#0b6b39}.pc-safety{background:#f3fbf6;border:1px solid #cce5d3;border-radius:16px;padding:12px 15px;margin:10px 0;color:#315f43;font-size:.84rem;line-height:1.5}.pc-home-grid{margin-top:8px}.pc-mini{background:#fff;border:1px solid var(--line);border-radius:18px;padding:16px 18px;box-shadow:0 8px 22px rgba(22,55,35,.045)}.pc-mini b{display:block;color:#0b6b39;font-size:1.28rem}.pc-mini span{display:block;color:#526b5d;font-size:.94rem;margin-top:6px}
    .stButton>button{border-radius:15px!important;min-height:50px!important;border:1px solid #cfe2d5!important;font-size:1.02rem!important;font-weight:850!important;background:#fff!important;color:#173225!important;padding:.55rem 1rem!important}
    .stButton>button:hover{border-color:#7ab58d!important;color:#0b6b39!important}
    .stButton>button[kind="primary"]{background:linear-gradient(135deg,#168d4d,#0b6b39)!important;color:#fff!important;border:0!important;box-shadow:0 8px 18px rgba(22,141,77,.18)}
    [data-testid="stFileUploader"]{background:#fff;border:1px dashed #b7d4bf;border-radius:18px;padding:4px}
    [data-baseweb="select"]>div{background:#fff!important;border-radius:12px!important;border:1px solid #cfe2d5!important;box-shadow:none!important}[data-baseweb="select"] *{color:#173225!important}[data-baseweb="select"] svg{fill:#0b6b39!important}
    [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"]{background:#fff!important;color:#173225!important;border:1px solid #cfe2d5!important}
    [role="option"]{background:#fff!important;color:#173225!important}
    [role="option"][aria-selected="true"], [role="option"]:hover{background:#eaf8ef!important;color:#0b6b39!important}
    input, textarea{background:#fff!important;color:#173225!important;border-color:#cfe2d5!important;color-scheme:light!important}
    [data-testid="stFileUploaderDropzone"]{background:#fff!important;border:1px dashed #9bc9aa!important}
    [data-testid="stFileUploaderDropzone"] button{background:#fff!important;color:#0b6b39!important;border:1px solid #9bc9aa!important}
    [data-testid="stCameraInput"]{background:#fff!important;border:1px solid #cfe2d5!important;border-radius:18px!important;padding:10px!important}
    [data-testid="stCameraInput"], [data-testid="stCameraInput"] section, [data-testid="stCameraInput"]>div{background:#fff!important;color:#173225!important;border:1px solid #cfe2d5!important;border-radius:18px!important}
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

    .pc-upload-card{background:#fff;border:1px solid #cfe2d5;border-radius:16px;padding:14px 16px;margin-bottom:8px}.pc-upload-title{font-weight:900;color:#0b6b39}.pc-upload-sub{font-size:.82rem;color:#64766b;margin-top:3px}.pc-selected-label{background:#eaf8ef;color:#116335;border:1px solid #cde8d4;border-radius:12px;padding:9px 12px;font-weight:800;margin:12px 0}.pc-analyze-box{background:#f3fbf6;border:1px solid #cce5d3;border-radius:16px;padding:14px 16px;margin:12px 0}.pc-analyze-box span{color:#64766b;font-size:.84rem}.pc-photo-placeholder{height:230px;border-radius:18px;background:#eff9f2;border:1px dashed #b7d4bf;display:flex;align-items:center;justify-content:center;text-align:center;flex-direction:column;color:#0b6b39;font-size:1.15rem}.pc-photo-placeholder span{color:#64766b;font-size:.8rem;margin-top:4px}
.pc-score{display:flex;align-items:center;gap:14px;background:linear-gradient(135deg,#f0fbf4,#fff);border:1px solid #cce5d3;border-radius:18px;padding:15px 17px}.pc-score-ring{width:58px;height:58px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#138a4b;color:#fff;font-weight:950;font-size:1.05rem;box-shadow:0 8px 18px rgba(19,138,75,.18)}.pc-score-copy{flex:1}.pc-score-title{font-weight:900;color:#0b6b39}.pc-score-sub{font-size:.82rem;color:#64766b;margin-top:3px}.pc-library-count{font-size:.82rem;color:#64766b;font-weight:800;margin:8px 0 16px}.pc-featured{border-radius:22px;overflow:hidden;border:1px solid var(--line);background:#fff;box-shadow:0 10px 28px rgba(22,55,35,.05);padding-bottom:12px}.pc-featured-body{padding:6px 17px 10px}.pc-featured-body h3{margin:0;color:var(--ink)}.pc-featured-body p{margin:5px 0 0;color:var(--muted);font-size:.86rem}.pc-reject{background:linear-gradient(135deg,#fff5f5,#fff);border:1px solid #efcaca;border-radius:20px;padding:18px 20px}.pc-reject-title{font-size:1.15rem;font-weight:950;color:#8a2020}.pc-checklist{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.pc-check{background:#f5fbf7;border:1px solid #d5e9da;border-radius:999px;padding:6px 10px;font-size:.78rem;font-weight:800;color:#315f43}
    @media(max-width:900px){.pc-hero{padding:25px 22px}.pc-hero h1{font-size:2.2rem}}

    /* Reference-inspired PlantCare AI visual refresh */
    .stApp{background:linear-gradient(180deg,#f4f8e9 0%,#fffdf3 45%,#f6f9e8 100%)!important;color:#073b2b!important;font-size:1.12rem!important}
    .stMarkdown p,.stMarkdown li{font-size:1.08rem!important;line-height:1.62!important}
    .stMarkdown h1{font-size:2.7rem!important;font-weight:900!important}
    .stMarkdown h2{font-size:2.05rem!important;font-weight:900!important}
    .stMarkdown h3{font-size:1.38rem!important;font-weight:850!important}
    [data-testid="stSidebar"]{background:linear-gradient(180deg,#003c2c 0%,#002e23 100%)!important;border-right:0!important}
    [data-testid="stSidebar"] *{color:#f4fff7!important}
    [data-testid="stSidebar"] .pc-brand-title{font-size:1.3rem!important;color:#fff!important}
    [data-testid="stSidebar"] .pc-brand-sub{color:#d4eee0!important}
    [data-testid="stSidebar"] .pc-nav-title{color:#a8d4bc!important}
    [data-testid="stSidebar"] .pc-page-byline{color:#c7e7d4!important}
    [data-testid="stSidebar"] .pc-page-byline strong{color:#fff!important}
    [data-testid="stSidebar"] .pc-card{background:rgba(255,255,255,.08)!important;border-color:rgba(210,244,222,.24)!important}
    [data-testid="stSidebar"] .pc-card div{color:#f4fff7!important}
    [data-testid="stSidebar"] .stButton>button{background:transparent!important;color:#eafff0!important;border:1px solid transparent!important;border-radius:12px!important;min-height:44px!important;font-size:1rem!important;box-shadow:none!important;text-align:left!important}
    [data-testid="stSidebar"] .stButton>button:hover{background:rgba(255,255,255,.12)!important;border-color:rgba(255,255,255,.18)!important;color:#fff!important}
    [data-testid="stSidebar"] .stButton>button[kind="primary"]{background:linear-gradient(135deg,#138c50,#0a6d3c)!important;border-color:#3aa86c!important;color:#fff!important;box-shadow:0 7px 18px rgba(0,0,0,.18)!important}
    .pc-hero{border-radius:24px!important;box-shadow:0 18px 38px rgba(4,70,40,.16)!important}
    .pc-card,.pc-stat,.pc-mini,.pc-featured{border-radius:18px!important;border-color:#dce7c9!important;background:rgba(255,255,249,.94)!important;box-shadow:0 7px 22px rgba(17,65,38,.06)!important}
    .pc-title{font-size:1.8rem!important;color:#063e2b!important}
    .pc-pills .pc-pill{font-size:.94rem!important}
    .pc-stat-num{font-size:2rem!important}
    .stButton>button{font-size:1.06rem!important;min-height:48px!important}
    label,[data-testid="stWidgetLabel"] p{font-size:1.04rem!important}
    input,textarea,[data-baseweb="select"]{font-size:1.02rem!important}
    .pc-home-stat{height:100%;text-align:center;background:rgba(255,255,248,.96);border:1px solid #dce7c9;border-radius:17px;padding:17px 10px;box-shadow:0 6px 18px rgba(14,75,43,.06)}
    .pc-home-stat .symbol{font-size:2rem;line-height:1.1;margin-bottom:7px}
    .pc-home-stat .value{font-size:1.75rem;font-weight:950;color:#086b3d;line-height:1.2}
    .pc-home-stat .label{font-size:.95rem;color:#174634;font-weight:750;margin-top:4px}
    .pc-home-hero{position:relative;overflow:hidden;color:#fff;border-radius:25px;padding:32px 34px;margin-bottom:22px;min-height:260px;background:linear-gradient(90deg,rgba(0,54,36,.96) 0%,rgba(0,84,49,.84) 43%,rgba(0,70,39,.18) 100%),url('https://images.unsplash.com/photo-1497250681960-ef046c08a56e?auto=format&fit=crop&w=1800&q=85') center 48%/cover no-repeat;box-shadow:0 18px 40px rgba(9,70,39,.18)}
    .pc-home-hero h1{font-size:clamp(2.6rem,4.4vw,3.8rem)!important;line-height:1.02!important;margin:0!important;color:#fff!important;letter-spacing:-.035em}
    .pc-home-hero .tagline{font-size:1.22rem;font-weight:700;color:#e4f5ba;margin-top:7px}
    .pc-home-hero .copy{font-size:1.13rem;max-width:660px;color:#fff;margin-top:14px;line-height:1.55}
    .pc-home-hero .eyebrow{font-size:.92rem;font-weight:900;letter-spacing:.12em;text-transform:uppercase;color:#d8f0a8}
    .pc-home-hero .mark{display:flex;align-items:center;gap:16px;margin-bottom:7px}
    .pc-home-hero .leaf-icon{width:70px;height:70px;display:flex;align-items:center;justify-content:center;border-radius:22px;background:linear-gradient(145deg,#f2facb,#fff);font-size:2.6rem;box-shadow:0 6px 18px #002e2370}
    .pc-home-hero .pc-pills{margin-top:18px}
    .pc-home-hero .pc-pill{background:rgba(255,255,255,.17);border-color:rgba(255,255,255,.4)}
    .pc-journey .pc-mini{min-height:140px}
    @media(max-width:900px){.pc-home-hero{padding:24px 20px;min-height:230px}.pc-home-hero h1{font-size:2.5rem!important}.stMarkdown p,.stMarkdown li{font-size:1.02rem!important}}



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
    .stButton > button, [data-testid="stDownloadButton"] button, [data-testid="stFormSubmitButton"] button { font-size: 1.12rem !important; min-height: 54px !important; padding: 12px 18px !important; line-height: 1.3 !important; }
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
    .pc-result-name { font-size: clamp(1.9rem, 3vw, 2.55rem) !important; }
    .pc-scientific, .pc-library-count, .pc-safety, .pc-upload-sub, .pc-analyze-box span { font-size: 1rem !important; line-height: 1.55 !important; }
    .stExpander details summary { font-size: 1.12rem !important; min-height: 54px !important; }
    [data-testid="stDataFrame"] * { font-size: 1rem !important; }
    @media (max-width: 900px) {
      html, body, [class*="css"], .stApp { font-size: 18px !important; }
      .stMarkdown p, .stMarkdown li { font-size: 1.06rem !important; }
      .stMarkdown h1, h1 { font-size: 2.25rem !important; }
      .stMarkdown h2, h2 { font-size: 1.9rem !important; }
      .stMarkdown h3, h3 { font-size: 1.45rem !important; }
      [data-testid="stTabs"] button, [data-baseweb="tab"] { padding: 11px 12px !important; font-size: 1rem !important; }
      .pc-card, .pc-mini, .pc-stat, .pc-result { padding: 18px !important; }
    }



    /* Final readability and reference-layout pass: larger type, stronger contrast,
       spacious controls, and consistent plant-card geometry. */
    :root {
      --pc-forest: #003b2b;
      --pc-deep: #002f23;
      --pc-green: #137b43;
      --pc-leaf: #dcefb7;
      --pc-cream: #fbfaed;
      --pc-ink: #082f25;
      --pc-muted: #35594a;
      --pc-border: #d5e4c8;
    }
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
      color: var(--pc-ink) !important;
      font-size: 20px !important;
    }
    [data-testid="stMain"] .block-container {
      max-width: 1600px !important;
      padding-top: 2rem !important;
      padding-bottom: 2.5rem !important;
      padding-left: clamp(1.25rem, 3vw, 3rem) !important;
      padding-right: clamp(1.25rem, 3vw, 3rem) !important;
    }
    .stMarkdown p, .stMarkdown li,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stText"] {
      font-size: 1.15rem !important;
      line-height: 1.7 !important;
      color: var(--pc-ink);
    }
    .stMarkdown h1, [data-testid="stMarkdownContainer"] h1, h1 {
      font-size: clamp(2.45rem, 3.2vw, 3.35rem) !important;
      line-height: 1.12 !important;
      font-weight: 900 !important;
      letter-spacing: -.025em !important;
    }
    .stMarkdown h2, [data-testid="stMarkdownContainer"] h2, h2 {
      font-size: clamp(1.9rem, 2.2vw, 2.35rem) !important;
      line-height: 1.2 !important;
      font-weight: 900 !important;
    }
    .stMarkdown h3, [data-testid="stMarkdownContainer"] h3, h3 {
      font-size: clamp(1.45rem, 1.7vw, 1.75rem) !important;
      line-height: 1.3 !important;
      font-weight: 850 !important;
    }
    .stCaption, [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] *, small {
      font-size: 1rem !important;
      line-height: 1.55 !important;
      color: var(--pc-muted) !important;
    }
    label, [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] label {
      font-size: 1.12rem !important;
      line-height: 1.45 !important;
      font-weight: 800 !important;
      color: var(--pc-ink) !important;
    }
    input, textarea, [data-baseweb="input"] input,
    [data-baseweb="select"] *, [data-baseweb="textarea"] textarea {
      font-size: 1.1rem !important;
      line-height: 1.45 !important;
    }
    input, textarea, [data-baseweb="input"] > div,
    [data-baseweb="select"] > div {
      min-height: 50px !important;
    }
    .stButton > button,
    [data-testid="stDownloadButton"] button,
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stFileUploader"] button,
    [data-testid="stCameraInput"] button {
      min-height: 54px !important;
      padding: 12px 19px !important;
      font-size: 1.08rem !important;
      line-height: 1.35 !important;
      font-weight: 800 !important;
      border-radius: 14px !important;
    }
    [data-testid="stTabs"] [role="tablist"] {
      gap: 10px !important;
      border-bottom: 1px solid var(--pc-border) !important;
      align-items: stretch !important;
    }
    [data-testid="stTabs"] button[role="tab"],
    [data-baseweb="tab"] {
      min-height: 58px !important;
      padding: 14px 22px !important;
      font-size: 1.12rem !important;
      font-weight: 850 !important;
      border-radius: 14px 14px 0 0 !important;
      white-space: normal !important;
    }
    [data-testid="stTabs"] button[role="tab"] p {
      font-size: 1.1rem !important;
      font-weight: 850 !important;
    }
    [data-testid="stSidebar"] {
      min-width: 245px !important;
      background: linear-gradient(180deg, var(--pc-forest) 0%, var(--pc-deep) 100%) !important;
      border-right: 0 !important;
    }
    [data-testid="stSidebar"] * {
      color: #f4fff7 !important;
    }
    [data-testid="stSidebar"] .pc-brand-title {
      font-size: 1.48rem !important;
      line-height: 1.25 !important;
    }
    [data-testid="stSidebar"] .pc-brand-sub {
      font-size: 1rem !important;
      line-height: 1.45 !important;
    }
    [data-testid="stSidebar"] .pc-nav-title {
      font-size: .86rem !important;
      letter-spacing: .1em !important;
    }
    [data-testid="stSidebar"] .stButton > button {
      width: 100% !important;
      min-height: 52px !important;
      padding: 12px 14px !important;
      font-size: 1.05rem !important;
      text-align: left !important;
      border-radius: 13px !important;
    }
    .pc-home-hero {
      min-height: 285px !important;
      padding: clamp(26px, 3vw, 42px) !important;
      border-radius: 25px !important;
      background-position: center 48% !important;
    }
    .pc-home-hero h1 {
      font-size: clamp(2.7rem, 4.3vw, 4rem) !important;
      line-height: 1.05 !important;
    }
    .pc-home-hero .eyebrow { font-size: 1rem !important; }
    .pc-home-hero .tagline { font-size: 1.35rem !important; line-height: 1.45 !important; }
    .pc-home-hero .copy { font-size: 1.2rem !important; line-height: 1.65 !important; }
    .pc-hero { padding: 30px !important; border-radius: 24px !important; }
    .pc-hero p { font-size: 1.18rem !important; line-height: 1.7 !important; }
    .pc-card, .pc-mini, .pc-stat, .pc-result, .pc-featured {
      border-radius: 19px !important;
      padding: 23px !important;
      border-color: var(--pc-border) !important;
    }
    .pc-card h3, .pc-featured-body h3 { font-size: 1.42rem !important; line-height: 1.35 !important; }
    .pc-card p, .pc-featured-body p { font-size: 1.08rem !important; line-height: 1.65 !important; }
    .pc-title { font-size: 1.9rem !important; line-height: 1.3 !important; margin-top: 28px !important; }
    .pc-stat-num { font-size: 2.25rem !important; line-height: 1.15 !important; }
    .pc-stat-label, .pc-home-stat .label, .pc-mini span { font-size: 1.02rem !important; line-height: 1.5 !important; }
    .pc-mini b { font-size: 1.35rem !important; }
    .pc-pill, .pc-badge, .pc-check { font-size: .98rem !important; line-height: 1.35 !important; padding: 9px 13px !important; }
    .pc-result-name { font-size: clamp(1.9rem, 3vw, 2.6rem) !important; }
    .pc-scientific, .pc-library-count, .pc-safety, .pc-upload-sub,
    .pc-analyze-box span, .pc-photo-placeholder span { font-size: 1rem !important; line-height: 1.55 !important; }
    .stExpander details summary, [data-testid="stExpander"] summary {
      min-height: 54px !important;
      font-size: 1.1rem !important;
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
      .stMarkdown h2, h2 { font-size: 1.8rem !important; }
      .stMarkdown h3, h3 { font-size: 1.4rem !important; }
      [data-testid="stTabs"] button[role="tab"], [data-baseweb="tab"] {
        min-height: 50px !important; padding: 10px 12px !important; font-size: 1rem !important;
      }
      .pc-card, .pc-mini, .pc-stat, .pc-result, .pc-featured { padding: 17px !important; }
      .pc-home-hero { min-height: 245px !important; }
    }

    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('\n<style>\n:root{--pc-forest:#003d2d;--pc-deep:#002e23;--pc-green:#137b43;--pc-lime:#d9edaa;--pc-cream:#f8f7e9;--pc-border:#d8e5c4}\n[data-testid="stSidebar"]{min-width:245px!important;background:linear-gradient(180deg,#003c2d 0%,#002f24 100%)!important}\n[data-testid="stSidebar"] .pc-logo{width:62px!important;height:62px!important;border-radius:50%!important;background:transparent!important;border:0!important;box-shadow:none!important}\n[data-testid="stSidebar"] .pc-logo svg{width:58px!important;height:58px!important}\n[data-testid="stSidebar"] .pc-brand-title{font-size:1.42rem!important}\n[data-testid="stSidebar"] .stButton>button{min-height:54px!important;font-size:1.12rem!important;padding:12px 15px!important;border-radius:12px!important}\n.stApp{background:linear-gradient(180deg,#f5f8e9 0%,#fffdf2 50%,#f8f8ed 100%)!important;color:#092f24!important}\n[data-testid="stMain"] .block-container{max-width:1700px!important;padding-top:1.15rem!important;padding-left:2rem!important;padding-right:2rem!important}\n.stMarkdown p,.stMarkdown li,[data-testid="stMarkdownContainer"] p{font-size:1.12rem!important;line-height:1.62!important}\n.stMarkdown h1,h1{font-size:clamp(2.3rem,3.1vw,3.25rem)!important}\n.stMarkdown h2,h2{font-size:2.05rem!important}.stMarkdown h3,h3{font-size:1.48rem!important}\nlabel,[data-testid="stWidgetLabel"] p{font-size:1.08rem!important;font-weight:750!important}\n.stButton>button{min-height:54px!important;font-size:1.1rem!important;font-weight:850!important;border-radius:14px!important}\n[data-testid="stTabs"] button,[data-baseweb="tab"]{min-height:58px!important;padding:13px 20px!important;font-size:1.14rem!important;font-weight:850!important}\n.pc-home-hero{min-height:310px!important;border-radius:24px!important;padding:38px!important;background-image:linear-gradient(90deg,rgba(0,57,38,.94) 0%,rgba(0,74,44,.80) 48%,rgba(0,55,34,.10) 100%),url(\'https://images.unsplash.com/photo-1497250681960-ef046c08a56e?auto=format&fit=crop&w=1800&q=90\')!important;background-position:center 48%!important;background-size:cover!important}\n.pc-home-hero .leaf-icon{width:76px!important;height:76px!important;border-radius:22px!important;background:#f4f9dc!important;font-size:0!important;display:flex!important;align-items:center!important;justify-content:center!important}\n.pc-home-hero .leaf-icon:before{content:"";display:block;width:64px;height:64px;background-image:url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 64 64\'%3E%3Ccircle cx=\'32\' cy=\'32\' r=\'29\' fill=\'%23f8ffe8\' stroke=\'%239bce57\' stroke-width=\'3\'/%3E%3Cpath d=\'M17 42 C16 24 29 14 47 13 C47 30 38 44 22 46 Z\' fill=\'%23168348\'/%3E%3Cpath d=\'M19 49 C26 37 33 29 43 20\' fill=\'none\' stroke=\'%23eaf8bd\' stroke-width=\'3\' stroke-linecap=\'round\'/%3E%3Cpath d=\'M30 36 C28 29 25 25 20 23 C19 31 23 36 30 36 Z\' fill=\'%239bd65d\'/%3E%3C/svg%3E");background-size:contain;background-repeat:no-repeat}\n.pc-home-stat{min-height:112px!important;padding:20px 14px!important;border-radius:17px!important}.pc-home-stat .symbol{font-size:2.35rem!important}.pc-home-stat .value{font-size:2rem!important}.pc-home-stat .label{font-size:1.08rem!important}\n.pc-card,.pc-mini,.pc-stat,.pc-featured{border-radius:19px!important;border:1px solid #d8e5c4!important;background:rgba(255,255,249,.96)!important;box-shadow:0 8px 22px rgba(17,65,38,.06)!important;padding:24px!important}\n.pc-card h3,.pc-featured-body h3{font-size:1.46rem!important;line-height:1.35!important}.pc-card p,.pc-featured-body p{font-size:1.1rem!important;line-height:1.65!important}\n.pc-title{font-size:1.95rem!important;margin-top:30px!important}.pc-pill{font-size:1rem!important;padding:9px 14px!important}.pc-upload-card{min-height:100px!important;padding:20px!important;border-radius:18px!important}.pc-upload-title{font-size:1.35rem!important}.pc-upload-sub{font-size:1.05rem!important}\n.pc-reference-banner{display:flex;align-items:center;gap:22px;min-height:150px;padding:24px 30px;border-radius:20px;margin:12px 0 22px;background:linear-gradient(90deg,rgba(250,250,235,.96),rgba(236,246,218,.86)),url(\'https://images.unsplash.com/photo-1497250681960-ef046c08a56e?auto=format&fit=crop&w=1400&q=85\') center/cover;color:#073d2b;border:1px solid #d8e5c4;box-shadow:0 8px 25px #124f2810}\n.pc-reference-banner h2{font-size:2.05rem!important;margin:0!important;color:#063b2b!important}.pc-reference-banner p{font-size:1.12rem!important;margin:4px 0 0!important}\n.pc-ref-logo{width:72px;height:72px;flex:0 0 72px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#fff;box-shadow:0 4px 16px #06442a22}\n.pc-ref-logo svg{width:66px;height:66px}.pc-how{background:#fffef6;border:1px solid #d8e5c4;border-radius:18px;padding:22px;margin:16px 0 24px}.pc-how-title{font-size:1.5rem;font-weight:900;margin-bottom:14px;color:#082f24}.pc-how-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.pc-how-step{text-align:center;background:#f4f8e8;border-radius:16px;padding:18px 10px;min-height:140px}.pc-how-icon{font-size:2.25rem}.pc-how-step b{display:block;font-size:1.08rem;margin:7px 0}.pc-how-step span{font-size:.98rem;line-height:1.4}\n.pc-about-qr{width:150px;height:150px;image-rendering:pixelated;border:8px solid white;border-radius:10px;box-shadow:0 2px 10px #1234}\n@media(max-width:900px){[data-testid="stMain"] .block-container{padding:1rem!important}.pc-home-hero{min-height:270px!important;padding:24px!important}.pc-home-hero h1{font-size:2.4rem!important}.pc-reference-banner{padding:18px!important}.pc-reference-banner h2{font-size:1.65rem!important}}\n</style>\n', unsafe_allow_html=True)

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
<script>
(() => {{
 const lines = {payload};
 try {{
   const Ctx = window.AudioContext || window.webkitAudioContext;
   if (Ctx) {{ const ctx = new Ctx(); let t = ctx.currentTime + 0.05;
     for (let j=0;j<3;j++) {{ const osc=ctx.createOscillator(); const gain=ctx.createGain(); osc.frequency.value=j===1?880:660; gain.gain.value=0.12; osc.connect(gain); gain.connect(ctx.destination); osc.start(t); osc.stop(t+0.16); t+=0.22; }}
   }}
   if ('speechSynthesis' in window) {{ const u=new SpeechSynthesisUtterance(lines.join(' ')); u.rate=0.92; window.speechSynthesis.cancel(); window.speechSynthesis.speak(u); }}
 }} catch(e) {{}}
}})();
</script>''', height=52)
    if st.button("🔊 Speak due reminders", key="speak_due_reminders"):
        lines = [f"Care reminder. {r.get('task', 'Care task')} for {r.get('plant', 'your plant')}." for r in due]
        payload = json.dumps(lines).replace("<", "\\u003c")
        st.components.v1.html(f'''<script>try {{ if ('speechSynthesis' in window) {{ const u=new SpeechSynthesisUtterance({payload}.join(' ')); u.rate=.92; window.speechSynthesis.cancel(); window.speechSynthesis.speak(u); }} }} catch(e) {{}}</script>''', height=1)

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Optional real vision model: BioCLIP.
# BioCLIP is a biology-focused zero-shot image classifier.  It is loaded lazily
# so the app can still start when the model cannot be downloaded.  The offline
# matcher remains as a fallback, but BioCLIP is preferred for species matching.
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_bioclip():
    """Load one shared BioCLIP model for the whole Streamlit process.

    Community Cloud has limited memory, so every identification component must
    reuse the same model instead of constructing separate model copies.
    """
    import torch
    import open_clip
    # Prefer CPU-safe operation on constrained Streamlit Community Cloud.
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # Use the original BioCLIP checkpoint because the newer BioCLIP 2 model
    # exceeded the available memory budget on Streamlit Community Cloud.
    errors = []
    for model_id in ("hf-hub:imageomics/bioclip",):
        try:
            model, _, preprocess = open_clip.create_model_and_transforms(model_id)
            tokenizer = open_clip.get_tokenizer(model_id)
            model = model.to(device).eval()
            return device, model, preprocess, tokenizer
        except Exception as exc:
            errors.append(f"{model_id}: {type(exc).__name__}")
    raise RuntimeError("Could not load the original BioCLIP checkpoint (" + "; ".join(errors) + ")")


MODEL_HINTS = {
    "Mango": "mango tree, Mangifera indica, long narrow lanceolate leaves, woody tree, mango fruit",
    "Marigold": "marigold, Tagetes erecta, yellow or orange round flower heads, pinnate foliage",
    "Rose": "rose, Rosa, woody shrub with serrated oval leaflets and distinctive rose flowers",
    "Hibiscus": "hibiscus, large five-petaled flowers, prominent central staminal column, serrated leaves",
    "Jasmine": "jasmine, Jasminum, small glossy opposite leaves and fragrant white flowers",
    "Aloe Vera": "aloe vera, thick fleshy pointed succulent leaves arranged in a rosette",
    "Snake Plant": "snake plant, Dracaena trifasciata, upright sword-shaped leaves with banded markings",
    "Money Plant": "money plant, pothos, Epipremnum aureum, heart-shaped leaves on a trailing vine",
    "Spider Plant": "spider plant, Chlorophytum comosum, long narrow arching leaves and plantlets",
    "Peace Lily": "peace lily, Spathiphyllum, clump of glossy dark green lance-shaped leaves arising from the base, distinctive white hood-like spathe surrounding a central spadix",
    "Areca Palm": "areca palm, Dypsis lutescens, multiple thin stems and feather-like palm fronds",
    "Rubber Plant": "rubber plant, Ficus elastica, large thick glossy oval leaves and woody stem",
    "Monstera": "monstera deliciosa, large split or fenestrated leaves",
    "Jade Plant": "jade plant, Crassula ovata, thick succulent stems and small fleshy oval leaves",
    "Croton": "croton, Codiaeum variegatum, colorful multicolored leathery leaves",
    "Anthurium": "anthurium, heart-shaped glossy leaves and waxy colorful spathes",
    "Bougainvillea": "bougainvillea, thorny woody climber with colorful papery bracts",
    "Sunflower": "sunflower, Helianthus annuus, tall stem with one large yellow flower head",
    "Lotus": "lotus, Nelumbo nucifera, round water leaves and large pink or white aquatic flowers",
    "Curry Leaf": "curry leaf, Murraya koenigii, pinnate aromatic compound leaves on a shrub or small tree",
    "Lemongrass": "lemongrass, Cymbopogon citratus, dense clump of long narrow grass blades",
    "Tomato": "tomato plant, Solanum lycopersicum, serrated compound leaves and round tomato fruits",
    "Chilli": "chili pepper, Capsicum annuum, narrow leaves and elongated or round peppers",
    "Brinjal": "eggplant brinjal, Solanum melongena, broad hairy leaves and purple or white fruit",
    "Okra": "okra, Abelmoschus esculentus, lobed leaves and ridged elongated pods",
    "Spinach": "spinach, Spinacia oleracea, low-growing leafy vegetable with soft smooth oval to arrow-shaped leaves in a basal rosette, thin green petioles, no woody trunk",
    "Cucumber": "cucumber, Cucumis sativus, rough broad palmately lobed leaves on a creeping or climbing vine, coiling tendrils, yellow flowers and elongated green cucumbers",
    "Guava": "guava tree, Psidium guajava, opposite oval leaves with prominent veins and pale bark",
    "Papaya": "papaya, Carica papaya, large deeply lobed leaves on a single trunk",
    "Lemon": "lemon tree, Citrus limon, glossy oval leaves and citrus fruit",
    "Neem": "neem tree, Azadirachta indica, pinnate compound leaves and small tree form",
    "Pomegranate": "pomegranate, Punica granatum, narrow glossy leaves and round red fruit",
    "Banana": "banana plant, Musa, huge broad leaves and a soft pseudostem",
    "Moringa": "moringa, Moringa oleifera, feathery compound leaves and slender tree",
    "Amla": "amla, Phyllanthus emblica, small closely spaced leaves along branchlets and round fruit",
    "Coconut": "coconut palm, Cocos nucifera, tall palm trunk and long feather-like fronds",
    "Bamboo": "bamboo, Bambusa, tall segmented hollow-looking green culms and narrow leaves",
    "ZZ Plant": "Zamioculcas zamiifolia, upright arching stems with thick glossy dark green oval leaflets",
    "Heartleaf Philodendron": "Philodendron hederaceum, trailing vine with smooth heart-shaped leaves and pointed tips",
    "Fiddle Leaf Fig": "Ficus lyrata, large violin-shaped leathery leaves with prominent pale veins",
    "Lucky Bamboo": "Dracaena sanderiana, smooth upright green cane stems with clearly visible ring-shaped nodes and tufts of narrow lance-shaped leaves; often grown in water, not true bamboo",
    "English Ivy": "Hedera helix, climbing or trailing vine with lobed angular leaves",
    "Boston Fern": "Nephrolepis exaltata, arching feathery fronds with many small leaflets",
    "Dracaena Marginata": "Dracaena marginata, narrow sword-like leaves in tufts atop thin woody canes",
    "Calathea Orbifolia": "Goeppertia orbifolia, broad round green leaves with pale silvery stripes",
    "Prayer Plant": "Maranta leuconeura, low spreading herb with oval leaves patterned with dark green patches and vivid red or pink midrib-side veins, leaves fold upward at night",
    "Dieffenbachia": "Dieffenbachia seguine, broad oval leaves with cream or pale green variegated centers",
    "Aglaonema": "Aglaonema commutatum, broad oval foliage often patterned silver, green or pink",
    "Syngonium": "Syngonium podophyllum, arrowhead-shaped juvenile leaves on a climbing or trailing vine",
    "Peperomia": "Peperomia obtusifolia, compact plant with thick glossy rounded oval leaves",
    "Tradescantia Zebrina": "Tradescantia zebrina, trailing stems and pointed leaves with silver and purple stripes",
    "Dwarf Schefflera": "Schefflera arboricola, palmate clusters of several oval leaflets radiating from one point",
    "Bird of Paradise": "Strelitzia reginae, large paddle-shaped leaves and distinctive orange-blue bird-like flowers",
    "Chrysanthemum": "Chrysanthemum morifolium, deeply lobed aromatic leaves and dense many-petaled flower heads",
    "Tulsi": "Ocimum tenuiflorum holy basil, opposite ovate leaves with toothed edges, aromatic herb, often purple-green stems and slender flower spikes; distinguish from mint by basil-like flower spikes and leaf form",
    "Mint": "Mentha spicata spearmint, opposite toothed leaves on spreading square stems, aromatic herb, narrow terminal flower spikes; distinguish from holy basil by leaf texture and growth habit",
}

@st.cache_resource(show_spinner=False)
def bioclip_text_features():
    """Encode independent visual descriptions to better separate look-alikes.

    A single averaged text embedding can blur visually similar classes. Keep
    per-class prompt vectors and combine a stable class prototype with the best
    matching botanical descriptions at inference time.
    """
    device, model, _, tokenizer = load_bioclip()
    import torch

    prompt_rows = []
    for p in PLANTS:
        common = str(p.get("common_name", "")).strip()
        scientific = str(p.get("scientific_name", "")).strip()
        hint = str(MODEL_HINTS.get(common, "")).strip()
        # Use complementary botanical views rather than repeating only a whole-plant label.
        # This helps when the uploaded photo shows a leaf, flower, stem, or partial plant.
        prompts = [
            f"a real photograph of the whole living {common} plant, {scientific}",
            f"a botanical photograph showing the identifying leaves of {common}, {scientific}",
            f"a close-up photograph of the foliage and leaf arrangement of {common}, {scientific}",
            f"a field photograph of {scientific} growing naturally",
            f"a plant identification guide photograph of {common} ({scientific}); {hint}",
            f"a close-up botanical photograph of {common} leaves and stems; diagnostic traits: {hint}",
            f"a clear photograph of the natural growth habit of {common}, {scientific}; {hint}",
            f"a real garden photograph of {common} foliage, stems, and leaf arrangement; {hint}",
        ]
        if hint:
            prompts.extend([
                f"a real plant photo of {common}; visible traits: {hint}",
                f"identification photograph of {scientific}; {hint}",
            ])
        else:
            traits = ", ".join(str(p.get(key, "")).strip()
                                for key in ("leaf", "flower", "growth")
                                if str(p.get(key, "")).strip())
            prompts.append(f"a botanical identification photo of {common}; visible traits: {traits}")
        if common == "Tulsi":
            prompts.extend([
                "holy basil Ocimum tenuiflorum plant, opposite ovate leaves with toothed margins and slender basil flower spikes",
                "Tulsi holy basil growing in an Indian home garden, branching herb with green or purple stems and small opposite leaves",
                "close-up of holy basil Ocimum tenuiflorum foliage and flowering spikes, not mint",
                "Ocimum tenuiflorum botanical field photograph, basil leaf shape and upright flowering spikes",
            ])
        elif common == "Mint":
            prompts.extend([
                "spearmint Mentha spicata plant, opposite textured serrated leaves on spreading square stems",
                "close-up of spearmint foliage, wrinkled veined leaves and creeping or spreading herb growth, not holy basil",
                "Mentha spicata botanical field photograph with narrow terminal flower spikes",
                "mint herb growing in a garden, paired serrated leaves on a spreading stem",
            ])
        elif common == "Peace Lily":
            prompts.extend([
                "Spathiphyllum peace lily with white hood-shaped spathe and central spadix above a basal clump of glossy green leaves",
                "close-up of peace lily foliage, broad glossy lance-shaped leaves with prominent midrib, white spathe flower if present",
                "peace lily houseplant in a pot, not a calla lily, not a white flower bouquet",
            ])
        elif common == "Lucky Bamboo":
            prompts.extend([
                "Dracaena sanderiana lucky bamboo, green cane stalks with visible horizontal ring nodes and narrow leaves emerging from nodes",
                "lucky bamboo houseplant with segmented canes arranged in spirals or bundles, often rooted in water, not Bambusa bamboo",
            ])
        elif common == "Spinach":
            prompts.extend([
                "Spinacia oleracea spinach, edible leafy vegetable in a low basal rosette, smooth tender oval or arrow-shaped leaves",
                "close-up of spinach leaves and petioles, soft smooth green foliage, no woody trunk and no deeply lobed papaya leaves",
            ])
        elif common == "Cucumber":
            prompts.extend([
                "Cucumis sativus cucumber vine with rough palmately lobed leaves, coiling tendrils, yellow flowers and elongated green cucumber fruits",
                "close-up of cucumber plant leaves with five angular lobes and rough texture, climbing cucurbit vine, not okra",
            ])
        elif common == "Prayer Plant":
            prompts.extend([
                "Maranta leuconeura prayer plant with oval patterned leaves and red veins radiating from the midrib",
                "close-up of prayer plant foliage with dark green patches, lighter green background and red-pink veins, not Calathea orbifolia",
                "Maranta leuconeura low-growing prayer plant with paired oval leaves, herringbone vein pattern and reddish midrib-side veins",
                "botanical close-up of Maranta prayer plant leaves, oval leaf blades with alternating dark and light green markings",
            ])
        elif common == "ZZ Plant":
            prompts.extend([
                "Zamioculcas zamiifolia ZZ houseplant, thick fleshy upright leaf stalks with paired glossy oval leaflets along each stalk",
                "close-up of ZZ plant pinnate leaves, smooth thick waxy dark green leaflets on arching succulent petioles, not bamboo canes",
                "Zamioculcas zamiifolia growing from thick underground rhizomes, feather-like compound leaves with rounded leaflets",
            ])
        elif common == "Aglaonema":
            prompts.extend([
                "Aglaonema Chinese evergreen houseplant, broad oval pointed leaves with silver or pale green patterned centres and dark green margins",
                "close-up of Aglaonema commutatum foliage, symmetrical silver-green variegation on broad leaves with a central midrib",
                "Chinese evergreen Aglaonema compact clump of patterned leaves emerging from short cane-like stems, distinguish from Dieffenbachia",
            ])
        elif common == "Mango":
            prompts.extend([
                "Mangifera indica mango tree, long narrow leathery lanceolate leaves with smooth edges and pointed tips, leaves alternate along woody twigs",
                "close-up of mango foliage with simple entire-edged elongated leaves and prominent pale midrib, not pinnate neem leaflets",
                "mango tree branch with clusters of long glossy narrow leaves and small mango fruits, botanical field photograph",
            ])
        # Include structured profile traits too, but cap their length to avoid generic filler
        # dominating the text embedding. Keep species-specific MODEL_HINTS as the anchor.
        profile_traits = " ".join(
            str(p.get(key, "")).strip()
            for key in ("leaf", "flower", "growth")
            if str(p.get(key, "")).strip()
        )
        if profile_traits:
            prompts.append(
                f"botanical field guide image of {common} ({scientific}); {profile_traits[:320]}"
            )
        prompt_rows.append(list(dict.fromkeys(prompts)))

    class_prompt_features = []
    class_prototypes = []
    with torch.no_grad():
        for prompts in prompt_rows:
            tokens = tokenizer(prompts).to(device)
            features = model.encode_text(tokens)
            features = features / features.norm(dim=-1, keepdim=True)
            prototype = features.mean(dim=0, keepdim=True)
            prototype = prototype / prototype.norm(dim=-1, keepdim=True)
            class_prompt_features.append(features)
            class_prototypes.append(prototype)
    prototypes = torch.cat(class_prototypes, dim=0)
    prototypes = prototypes / prototypes.norm(dim=-1, keepdim=True)
    return device, model, prototypes, class_prompt_features


@st.cache_resource(show_spinner=False)
def bioclip_gate_text_features():
    """Build a small plant-vs-object vocabulary using the same BioCLIP model.

    Keeping one biology vision model avoids loading two large CLIP models on
    Community Cloud, which reduces memory pressure and first-run failures.
    """
    device, model, _, tokenizer = load_bioclip()
    import torch
    plant_prompts = [
        "a clear photograph of a living plant",
        "a botanical photograph of leaves or foliage",
        "a photograph of a potted plant",
        "a photograph of a tree or shrub",
        "a photograph of a flower or flowering plant",
        "a close-up photograph of plant foliage",
    ]
    object_prompts = [
        "a photograph of a door or wall",
        "a photograph of furniture or a room",
        "a photograph of a car or vehicle",
        "a photograph of a person",
        "a photograph of an animal",
        "a photograph of food",
        "a photograph of a building",
        "a photograph of an electronic device",
        "a photograph of a household object",
        "a photograph of a book, notebook, paper or printed page",
        "a photograph of a pen, pencil, eraser or ruler",
        "a photograph of a door, window, wall or glass pane",
        "a photograph of a box, carton, package or container",
        "a photograph of a person, face or human body",
        "a photograph of a car, motorcycle, bicycle or scooter",
        "a photograph of pavement, floor or road",
    ]
    groups=[]
    with torch.no_grad():
        for prompts in (plant_prompts, object_prompts):
            t=model.encode_text(tokenizer(prompts).to(device))
            t=t/t.norm(dim=-1,keepdim=True)
            t=t.mean(dim=0,keepdim=True)
            t=t/t.norm(dim=-1,keepdim=True)
            groups.append(t)
    return device, model, groups[0], groups[1]


@st.cache_resource(show_spinner=False)
def bioclip_context_text_features():
    """Build plant-vs-document prompt embeddings for a second rejection layer."""
    device, model, _, tokenizer = load_bioclip()
    import torch
    plant_prompts=[
        "a clear photograph of a real living plant",
        "a botanical photograph showing real leaves, stems or flowers",
        "a close-up photograph of real plant foliage",
    ]
    text_prompts=[
        "a photograph of a printed page full of text",
        "a screenshot containing text and words",
        "a document or textbook page",
        "a photograph of a computer screen showing text",
        "a scanned worksheet or paper",
        "a poster or sign containing mostly text",
    ]
    groups=[]
    with torch.no_grad():
        for prompts in (plant_prompts,text_prompts):
            f=model.encode_text(tokenizer(prompts).to(device)); f=f/f.norm(dim=-1,keepdim=True)
            f=f.mean(dim=0,keepdim=True); f=f/f.norm(dim=-1,keepdim=True); groups.append(f)
    return device, model, groups[0], groups[1]


def _document_visual_score(img: Image.Image) -> float:
    """Model-free supporting score for text-heavy documents/screenshots."""
    im=ImageOps.exif_transpose(img).convert("RGB"); im.thumbnail((360,360))
    a=np.asarray(im,dtype=np.float32)/255.0; gray=a.mean(axis=2)
    mx=a.max(axis=2); d=mx-a.min(axis=2); sat=np.divide(d,mx,out=np.zeros_like(d),where=mx>1e-6)
    edge=float(np.abs(np.diff(gray,axis=1)).mean()+np.abs(np.diff(gray,axis=0)).mean())
    low_sat=float((sat<.10).mean()); mid=float(((gray>.18)&(gray<.92)).mean())
    return float(max(0,min(1,min(edge*5,.45)+min(low_sat*.45,.35)+min(mid*.20,.20))))


def bioclip_context_screen(img: Image.Image):
    device, model, plant_text, text_text=bioclip_context_text_features()
    preprocess=load_bioclip()[2]
    import torch
    ps=[]; ts=[]
    with torch.no_grad():
        for view in _analysis_views(img):
            x=preprocess(view).unsqueeze(0).to(device); f=model.encode_image(x); f=f/f.norm(dim=-1,keepdim=True)
            ps.append(float((100.0*f@plant_text.T).squeeze().cpu())); ts.append(float((100.0*f@text_text.T).squeeze().cpu()))
    plant_score=float(np.mean(ps)); text_score=float(np.mean(ts))
    return plant_score,text_score,plant_score-text_score,_document_visual_score(img)


def bioclip_gate(img: Image.Image):
    """Use BioCLIP to screen plant vs obvious non-plant images across views."""
    device, model, plant_text, object_text = bioclip_gate_text_features()
    preprocess = load_bioclip()[2]
    import torch
    plant_scores=[]; object_scores=[]
    with torch.no_grad():
        # This is a safety gate, not the species ranker. Two views balance
        # plant/object screening with the limited memory and CPU budget.
        for view in _analysis_views(img)[:2]:
            x=preprocess(view).unsqueeze(0).to(device)
            f=model.encode_image(x); f=f/f.norm(dim=-1,keepdim=True)
            plant_scores.append(float((100.0*f@plant_text.T).squeeze().cpu()))
            object_scores.append(float((100.0*f@object_text.T).squeeze().cpu()))
    ps=float(np.mean(plant_scores)); os=float(np.mean(object_scores)); margin=ps-os
    # A margin, rather than a raw softmax probability, is used because the
    # vocabulary is intentionally small and the model scores are not calibrated
    # probabilities.
    is_plant = margin >= 1.5 and ps >= 18.0
    clearly_nonplant = os >= 24.0 and margin <= -1.0
    return is_plant and not clearly_nonplant, ps, margin, {"plant_score":ps,"object_score":os}


@st.cache_data(ttl=86400, show_spinner=False)
def reference_features_for_candidates(candidate_names: Tuple[str, ...]):
    """Build a small cached support set from real reference plant photos."""
    import torch
    names = tuple(dict.fromkeys(str(x) for x in candidate_names if str(x)))[:8]
    if not names:
        return {}
    photos = get_plant_photos(names)
    device, model, preprocess, _ = load_bioclip()
    result = {}
    with torch.no_grad():
        for p in PLANTS:
            if p["common_name"] not in names:
                continue
            url = photos.get(p["scientific_name"].lower()) or photos.get(p["common_name"].lower())
            if not url:
                continue
            raw = fetch_reference_image(url)
            if not raw:
                continue
            try:
                ref = Image.open(io.BytesIO(raw))
                feats = []
                for view in _analysis_views(ref)[:2]:
                    x = preprocess(view).unsqueeze(0).to(device)
                    f = model.encode_image(x)
                    f = f / f.norm(dim=-1, keepdim=True)
                    feats.append(f)
                f = torch.cat(feats, dim=0).mean(dim=0, keepdim=True)
                f = f / f.norm(dim=-1, keepdim=True)
                result[p["common_name"]] = f.cpu().numpy()[0].astype(np.float32)
            except Exception:
                continue
    return result


def _focus_crop(img: Image.Image) -> Image.Image | None:
    """Find a vegetation-rich crop so a wide camera frame does not hide the plant."""
    im=ImageOps.exif_transpose(img).convert("RGB")
    small=im.copy(); small.thumbnail((640,640))
    a=np.asarray(small,dtype=np.float32)/255.0
    r,g,b=a[...,0],a[...,1],a[...,2]
    mx=a.max(axis=2); mn=a.min(axis=2); sat=np.divide(mx-mn,mx,out=np.zeros_like(mx),where=mx>1e-6)
    green=(g>r*.96)&(g>b*1.04)&(g>.14)&(sat>.10)
    # Also include common flower/leaf colors so flowering plants are not cropped out.
    yellow=(r>.35)&(g>.30)&(b<.40)&(r>b*1.12)&(sat>.16)
    red=(r>.40)&(r>g*1.18)&(r>b*1.18)&(sat>.18)
    mask=green|yellow|red
    ys,xs=np.where(mask)
    if len(xs)<max(80,int(mask.size*.006)):
        return None
    x0,x1=int(xs.min()),int(xs.max()); y0,y1=int(ys.min()),int(ys.max())
    pad=int(max(x1-x0,y1-y0)*.20)+8
    x0=max(0,x0-pad); y0=max(0,y0-pad); x1=min(small.width,x1+pad+1); y1=min(small.height,y1+pad+1)
    if (x1-x0)*(y1-y0) < small.width*small.height*.04:
        return None
    return im.crop((int(x0/small.width*im.width),int(y0/small.height*im.height),int(x1/small.width*im.width),int(y1/small.height*im.height)))


def _analysis_views(img: Image.Image) -> List[Image.Image]:
    """Build full-frame, vegetation-focused, and context crops in that order."""
    im=ImageOps.exif_transpose(img).convert("RGB")
    # Standardize orientation/size before either camera or gallery reaches the model.
    im.thumbnail((1024,1024),Image.Resampling.LANCZOS)
    views=[im]
    w,h=im.size
    # Put the plant-focused crop second: the fast non-plant gate examines the
    # first two views, so it must see vegetation rather than only a centre crop.
    focus=_focus_crop(im)
    if focus is not None:
        views.append(focus)
    side=int(min(w,h)*.78)
    if side>=160:
        left=max(0,(w-side)//2); top=max(0,(h-side)//2)
        views.append(im.crop((left,top,left+side,top+side)))
    if h>220:
        views.append(im.crop((0,0,w,int(h*.82))))
    # The benchmark uses up to three complementary views. Keep the full frame,
    # vegetation-focused crop, and context crop available to species ranking.
    # Explicit screening gates slice to the first two views where latency matters.
    return views[:3]

def bioclip_rank(img: Image.Image, filename_hint: str = ""):
    """Rank the 56 supported plants with BioCLIP across several image views.

    filename_hint is deliberately ignored. Scores are relative matching scores,
    not calibrated probabilities or a guarantee of correct species identity.
    """
    import torch
    device, model, preprocess, _ = load_bioclip()
    _, _, prototypes, prompt_features = bioclip_text_features()
    views = _analysis_views(img)
    per_view = []
    with torch.no_grad():
        for view in views:
            x = preprocess(view).unsqueeze(0).to(device)
            feat = model.encode_image(x)
            feat = feat / feat.norm(dim=-1, keepdim=True)
            # Prototype scores stabilize class ranking; strongest prompt match
            # helps when one specific leaf/flower description fits better.
            proto_scores = (100.0 * feat @ prototypes.T).squeeze(0)
            prompt_scores = []
            for prompts in prompt_features:
                prompt_scores.append((100.0 * feat @ prompts.T).max(dim=1).values.squeeze(0))
            prompt_scores = torch.stack(prompt_scores)
            # Keep a strong class prototype but give diagnostic prompts more influence.
            # Max-prompt scoring is useful for images showing only one distinctive plant part.
            per_view.append(0.58 * proto_scores + 0.42 * prompt_scores)
        stacked = torch.stack(per_view)
        # Average protects against a misleading crop; the best view preserves leaf/flower detail.
        logits = 0.62 * stacked.mean(dim=0) + 0.38 * stacked.max(dim=0).values
        probs = torch.softmax(logits, dim=0).cpu().numpy()
    order = np.argsort(-probs)[:8]
    rows = [(PLANTS[int(i)], float(probs[int(i)])) for i in order]
    return rows

@st.cache_resource(show_spinner=False)
def _general_object_model():
    """Small general-domain ImageNet model used only as a non-plant safety gate.

    BioCLIP is specialized for biological imagery, so it can sometimes give a
    plant species a high score for an ordinary object. A general ImageNet
    classifier provides an independent object signal before we accept a plant.
    """
    import torch
    from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small
    weights = MobileNet_V3_Small_Weights.DEFAULT
    model = mobilenet_v3_small(weights=weights).eval()
    return model, weights.transforms(), tuple(weights.meta["categories"])


@st.cache_data(ttl=86400, show_spinner=False)
def general_object_screen(img_bytes: bytes):
    """Independent everyday-object gate. This runs before plant species matching."""
    try:
        import torch
        model, preprocess, labels = _general_object_model()
        im=Image.open(io.BytesIO(img_bytes)).convert("RGB")
        # Two views keep the independent object gate useful without making every
        # analysis wait on four serial ImageNet inferences.
        views=_analysis_views(im)[:2]
        votes=[]
        with torch.no_grad():
            for view in views:
                probs=torch.softmax(model(preprocess(view).unsqueeze(0)),dim=1)[0]
                vals,idx=torch.topk(probs,8)
                votes.append([(labels[int(i)].lower(),float(v)) for v,i in zip(vals,idx)])
        flat=[item for vote in votes for item in vote]
        flat.sort(key=lambda x:x[1],reverse=True)
        top=flat[:12]
        hard_nonplant=(
            "car","jeep","sports car","minivan","pickup","truck","bus","motorcycle","bicycle","suv","station wagon","convertible","limousine",
            "scooter","vehicle","airliner","aircraft","person","man","woman","boy","girl",
            "laptop","computer","keyboard","mouse","monitor","screen","television","remote",
            "cellular telephone","telephone","camera","microphone","refrigerator","washer","vacuum",
            "radio","printer","book","notebook","envelope","building","streetcar","street sign",
            "traffic light","parking meter","fire engine","ambulance","police van","school bus","desktop computer",
            "desk","chair","table","bottle","cup","mug","backpack","shoe","clock","watch","car wheel",
            "pencil","pen","ballpoint","fountain pen","ruler","eraser","book jacket","binder",
            "window shade","window screen","screen door","door","window","glass","plate",
            "scissors","stapler","paper towel","toilet tissue","box","carton","packet"
        )
        plant_terms=(
            "plant","tree","flower","daisy","rose","sunflower","leaf","cucumber","zucchini","corn",
            "mushroom","bolete","strawberry","lemon","orange","banana","fig","pineapple","acorn",
            "buckeye","potato","cauliflower","broccoli","head cabbage","bell pepper","artichoke","rapeseed"
        )
        hard_hits=[(name,score) for name,score in top if any(term in name for term in hard_nonplant)]
        plant_hits=[(name,score) for name,score in top if any(term in name for term in plant_terms)]
        hard_max=max((score for _,score in hard_hits),default=0.0)
        plant_max=max((score for _,score in plant_hits),default=0.0)
        top1=top[0][0] if top else ""
        top1_score=top[0][1] if top else 0.0
        # Count object evidence per view instead of letting one crop's guess
        # veto the whole image. This is important for plants photographed in pots,
        # on shelves, or beside people/furniture.
        strong_object_views=0
        for vote in votes:
            view_hard=max((score for name,score in vote
                           if any(term in name for term in hard_nonplant)),default=0.0)
            view_plant=max((score for name,score in vote
                            if any(term in name for term in plant_terms)),default=0.0)
            if view_hard >= 0.32 and view_plant < 0.12:
                strong_object_views += 1
        # Reject repeated, strong non-plant evidence; allow a single ambiguous
        # generic-object label to proceed to the botanical classifier.
        reject=bool(
            hard_hits and (
                (strong_object_views >= 2 and hard_max >= 0.32 and plant_max < 0.20) or
                (hard_max >= 0.72 and plant_max < 0.12) or
                (hard_max >= 0.62 and plant_max < 0.08)
            )
        )
        reason=f"General vision screening recognized a non-plant object ({top1})." if reject else ""
        return reject,reason,{"top":top,"top1":top1,"top1_score":top1_score,"hard_hits":hard_hits,"plant_hits":plant_hits,"hard_max":hard_max,"plant_max":plant_max}
    except Exception as exc:
        # The general-domain model may fail to download on a fresh/cloud deploy.
        # Do not label every genuine plant as a non-plant just because this
        # *optional* gate is unavailable; BioCLIP + the separate conservative
        # plant-presence gate still get a chance to assess the image.
        return False, "", {"error":f"{type(exc).__name__}: {exc}", "gate_unavailable": True}


def optional_vision_rank(img: Image.Image, filename_hint: str = ""):
    try:
        return bioclip_rank(img, filename_hint), True, ""
    except Exception as exc:
        return [], False, f"{type(exc).__name__}: {exc}"


def _strong_object_screen(img: Image.Image):
    """Return the raw BioCLIP plant/object evidence for a final rejection check.

    This is intentionally separate from the old conservative gate. A plant
    identification result should not be discarded merely because a generic
    plant-vs-object prompt set is uncertain. We only use this helper to reject
    images when object evidence is decisively stronger.
    """
    device, model, plant_text, object_text = bioclip_gate_text_features()
    preprocess = load_bioclip()[2]
    import torch
    plant_scores=[]; object_scores=[]
    with torch.no_grad():
        for view in _analysis_views(img):
            x=preprocess(view).unsqueeze(0).to(device)
            f=model.encode_image(x); f=f/f.norm(dim=-1,keepdim=True)
            plant_scores.append(float((100.0*f@plant_text.T).squeeze().cpu()))
            object_scores.append(float((100.0*f@object_text.T).squeeze().cpu()))
    ps=float(np.mean(plant_scores)); os=float(np.mean(object_scores)); margin=ps-os
    return device, model, ps, margin, {"plant_score":ps,"object_score":os}


def vision_gate(img: Image.Image):
    """Reject only strong non-plant/document evidence; avoid false negatives.

    This is a screening gate, not the species classifier. A failure to download
    a model is not evidence that the uploaded image is not a plant.
    """
    local_is_plant, local_score, local_reason, local_features = plant_gate(img)
    sharp, bright, mindim = image_quality(img)
    if mindim < 100 or bright < 5 or sharp < 1.0:
        return False, 0.0, "Photo is too small, dark, or blurred to assess reliably", {"gate": "quality"}
    # Skip the extra ImageNet/MobileNet model on Streamlit Community Cloud.
    # Loading a second neural network caused avoidable memory pressure; the
    # lightweight local plant gate and BioCLIP gate still screen the upload.
    doc_score = _document_visual_score(img)
    if doc_score >= 0.88 and not local_is_plant:
        return False, 0.0, "The image appears to be a text-heavy document or screenshot", {"gate": "document"}
    # If visual evidence is ambiguous, let the species matcher decide rather than
    # rejecting real plants because of unusual colours, pots, lighting or backgrounds.
    if local_is_plant:
        return True, local_score, local_reason, {"gate": "local_visual", "features": local_features}
    return True, local_score, "Plant presence is uncertain; continuing to species matching", {"gate": "defer_to_species_model", "features": local_features}


# -----------------------------------------------------------------------------
# Reliable offline-safe visual analysis
# This intentionally does NOT depend on OpenAI, Gemini, OpenCLIP, BioCLIP or API
# keys. The old version failed at Stage 1 when its external model weights were
# unavailable. This version always completes the local visual screening step.
# -----------------------------------------------------------------------------
def rgb_features(img: Image.Image) -> dict:
    im = ImageOps.exif_transpose(img).convert("RGB")
    im.thumbnail((320, 320))
    a = np.asarray(im, dtype=np.float32) / 255.0
    r,g,b = a[...,0],a[...,1],a[...,2]
    mx = a.max(axis=2); mn = a.min(axis=2); d = mx-mn
    sat = np.divide(d, mx, out=np.zeros_like(d), where=mx>1e-6)
    # Green is deliberately broader than the old rule so warm-lit mango/tulsi
    # photos are not rejected before the species model sees them.
    green = (g > r*1.02) & (g > b*1.02) & (g > .16) & (sat > .12)
    leafy_green = (g > r*.98) & (g > b*1.08) & (g > .20) & (sat > .18)
    yellow = (r > .40) & (g > .34) & (b < .38) & (r > b*1.18) & (sat > .18)
    red = (r > .42) & (r > g*1.22) & (r > b*1.22) & (sat > .20)
    dark = mx < .16
    gray = d < .055
    edges_x=np.abs(np.diff(a.mean(axis=2),axis=1)).mean()
    edges_y=np.abs(np.diff(a.mean(axis=2),axis=0)).mean()
    return {
        "green_ratio":float(green.mean()), "leafy_green_ratio":float(leafy_green.mean()),
        "yellow_ratio":float(yellow.mean()), "red_ratio":float(red.mean()),
        "sat":float(sat.mean()), "dark_ratio":float(dark.mean()), "gray_ratio":float(gray.mean()),
        "edge":float(edges_x+edges_y), "brightness":float(mx.mean()),
        "width":im.width, "height":im.height,
    }


def image_quality(img: Image.Image) -> Tuple[float,float,float]:
    rgb=ImageOps.exif_transpose(img).convert("RGB")
    small=rgb.resize((256,256)).convert("L")
    a=np.asarray(small,dtype=np.float32)
    sharp=float(np.var(np.diff(a,axis=0))+np.var(np.diff(a,axis=1)))
    return sharp,float(a.mean()),float(min(rgb.size))


def plant_gate(img: Image.Image) -> Tuple[bool,float,str,dict]:
    f=rgb_features(img)
    score=0.0
    score += min(f["green_ratio"]*2.4, .60)
    score += min(f["leafy_green_ratio"]*1.4, .25)
    score += min(f["sat"]*.20, .16)
    score += min(f["edge"]*1.4, .10)
    score += min(f["yellow_ratio"]*.06, .03)
    score += min(f["red_ratio"]*.04, .02)
    score -= min(f["gray_ratio"]*.18, .08)
    score -= min(f["dark_ratio"]*.08, .04)
    score=float(max(0,min(1,score)))
    # The fallback gate is intentionally permissive for real plants; the
    # species model and the explicit non-plant check are responsible for the
    # final decision when available. This avoids rejecting warm-lit mango/tulsi.
    is_plant=(f["green_ratio"] >= .045 and f["sat"] >= .16) or (f["leafy_green_ratio"] >= .025) or (f["green_ratio"] >= .025 and f["yellow_ratio"] >= .08 and f["sat"] >= .30) or (f["red_ratio"] >= .08 and f["sat"] >= .25 and f["edge"] >= .08)
    reason="Plant-like vegetation/color/texture detected" if is_plant else "The photo does not contain enough plant-like visual evidence"
    return is_plant,score,reason,f


def clue_tokens(leaf_shape,leaf_texture,flowers,growth,thorns):
    return [x.lower() for x in [leaf_shape,leaf_texture,flowers,growth,thorns] if x and x!="Not sure"]


def identify_locally(img: Image.Image, clues: List[str]) -> List[Tuple[dict,float]]:
    """Return no species prediction without a vision model.

    Leaf clues and pixel colours are not a validated species classifier. Returning
    an empty result is safer than inventing a plant name when model weights fail.
    Kept as a compatibility shim for callers from earlier project versions.
    """
    return []


def visual_health_screen(img: Image.Image) -> dict:
    """Screen approximate colour patterns only; this is not leaf segmentation or diagnosis."""
    focus = _focus_crop(img) or ImageOps.exif_transpose(img).convert("RGB")
    small = focus.copy()
    small.thumbnail((500, 500))
    a = np.asarray(small, dtype=np.float32) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(axis=2)
    sat = np.divide(mx - a.min(axis=2), mx, out=np.zeros_like(mx), where=mx > 1e-6)

    # These masks describe rough colour families, not individual leaves.
    # Flowers, soil, shadows and backgrounds can resemble these colours.
    green = (g > r * .94) & (g > b * 1.04) & (g > .14) & (sat > .10)
    yellow = (r > .38) & (g > .32) & (b < .40) & (r > b * 1.10) & (sat > .16)
    brown = (r > .20) & (g > .10) & (g < r * .78) & (b < g * .95) & (sat > .16)
    colour_mask = green | yellow | brown
    coverage = float(colour_mask.mean())

    # If the photo contains too little plant-like colour, don't manufacture
    # percentages or imply that the plant has been assessed.
    if coverage < .025:
        return {
            "status": "Unable to assess: too little plant-like colour is visible",
            "level": "Unable to assess",
            "green": 0.0, "yellow": 0.0, "brown": 0.0, "dark": 0.0,
            "screenable": False, "colour_coverage": coverage,
            "focus_used": focus is not img,
        }

    area = max(float(colour_mask.sum()), 1.0)
    green_f = float((green & colour_mask).sum() / area)
    yellow_f = float((yellow & colour_mask).sum() / area)
    brown_f = float((brown & colour_mask).sum() / area)

    # Alerts refer only to colour patterns; they are not diagnoses.
    if brown_f >= .16:
        status = "Brown-toned pixels detected; inspect leaves directly"
        level = "Review visible colours"
    elif yellow_f >= .20:
        status = "Yellow-toned pixels detected; inspect leaves directly"
        level = "Review visible colours"
    else:
        status = "No strong yellow/brown colour pattern detected"
        level = "No obvious colour warning"
    return {
        "status": status, "level": level,
        "green": green_f, "yellow": yellow_f, "brown": brown_f, "dark": 0.0,
        "screenable": True, "colour_coverage": coverage,
        "focus_used": focus is not img,
    }


def health_issue_text(p: dict, health: dict) -> str:
    if not health.get("screenable", True):
        return "There is not enough clearly screenable plant-like colour in this photo. Take a closer, well-lit photo of the leaves. This screen cannot reliably assess the current image."
    status = str(health.get("status", "")).lower()
    if "brown-toned" in status:
        return ("Brown-toned pixels can come from mature tissue, flowers, soil, shadows or damage. "
                "Inspect the leaves themselves for spots, rot, pests or physical injury before taking action. "
                "Plant-profile problems are possibilities to investigate, not diagnoses: " +
                str(p.get("diseases", "Check the plant profile for common diseases.")))
    if "yellow-toned" in status:
        return ("Yellow-toned pixels can be flowers, lighting or leaves. If the leaves themselves are yellowing, "
                "check soil moisture, drainage, light and pests; colour alone cannot identify the cause.")
    return ("No strong yellow/brown colour pattern was detected in the screenable pixels. "
            "This does not prove the plant is healthy; continue monitoring and use the species care profile.")


def care_assessment(img: Image.Image, p: dict, health: dict) -> dict:
    """Give cautious care prompts; a photograph cannot measure growing conditions."""
    if not health.get("screenable", True):
        return {
            "water_status": "Check soil physically",
            "water_detail": "The photo is not sufficient for colour screening. Feel the soil and check drainage before watering.",
            "fertilizer_status": "Not measurable from photo",
            "fertilizer_detail": "A photo cannot measure nutrient levels. Follow the species guidance and do not fertilize solely because of leaf colour.",
            "disease_status": "No disease diagnosis",
            "disease_detail": "The photo does not provide enough visible evidence. Inspect leaf surfaces and take a close-up of affected tissue if present.",
            "pest_status": "Not confirmed",
            "pest_detail": "Inspect leaf undersides, stems and new growth for insects, webbing, scale or sticky residue.",
            "sunlight_status": "Species light requirement",
            "sunlight_detail": str(p.get("light", "Use the plant profile for its light requirement.")),
            "growth_status": "Cannot assess from one photo",
            "growth_detail": "Compare repeat photos from a similar distance and angle to track new leaves and overall growth.",
        }

    y = float(health.get("yellow", 0))
    brown = float(health.get("brown", 0))
    colour_alert = y >= .20 or brown >= .16

    if brown >= .16:
        water_status = "Inspect leaves and soil"
        water_detail = ("Brown-toned pixels were detected, but these may be soil, flowers, shadows or leaf tissue. "
                        "Inspect the leaves and check soil moisture/drainage before changing watering.")
    elif y >= .20:
        water_status = "Check leaves and soil"
        water_detail = ("Yellow-toned pixels were detected. Confirm that the leaves themselves are yellow before "
                        "checking soil moisture, drainage, light and pests.")
    else:
        water_status = "No strong colour warning"
        water_detail = "No strong yellow/brown colour pattern was detected. Soil moisture still needs a physical check."

    fertilizer_status = "No fertilizer diagnosis from photo"
    fertilizer_detail = ("Fertilizer need cannot be measured from a photograph. Use the species fertilizer guidance "
                         "and avoid adding fertilizer solely because a leaf looks yellow.")
    if y >= .20:
        fertilizer_detail += " Yellow-toned pixels may also come from flowers or lighting."

    disease_status = "No specific disease confirmed"
    disease_detail = ("The image cannot confirm a disease or pathogen. Inspect affected leaves closely and compare "
                       "symptoms with the plant profile before considering treatment.")
    if brown >= .16:
        disease_status = "Inspect brown-toned areas"
        disease_detail = ("Brown-toned pixels are not proof of leaf damage. Inspect actual leaves for spots, rot, "
                          "pests or physical injury before considering treatment.")

    pest_status = "No pest conclusion from photo"
    pest_detail = ("Pests are not reliably confirmed from this photo. Inspect leaf undersides, stems and new growth "
                   "for insects, webbing, scale or sticky residue before considering treatment.")
    if colour_alert:
        pest_detail += " Colour patterns have many possible causes and are not proof of pests."

    return {
        "water_status": water_status, "water_detail": water_detail,
        "fertilizer_status": fertilizer_status, "fertilizer_detail": fertilizer_detail,
        "disease_status": disease_status, "disease_detail": disease_detail,
        "pest_status": pest_status, "pest_detail": pest_detail,
        "sunlight_status": "Species light requirement",
        "sunlight_detail": str(p.get("light", "Use the plant profile for its light requirement.")),
        "growth_status": "Growth rate cannot be measured from one photo",
        "growth_detail": "Take repeat photos from a similar distance and angle to track new leaves, height and overall growth.",
    }


def confidence_label(rows: List[Tuple[dict,float]]) -> Tuple[str,int]:
    if not rows:
        return "Needs confirmation", 0
    top=float(rows[0][1]); second=float(rows[1][1]) if len(rows)>1 else 0.0
    margin=max(0.0,top-second)
    # BioCLIP softmax scores across 56 classes are not calibrated probabilities.
    # Convert rank separation into a bounded visual-match band instead of using
    # an impossible absolute probability threshold.
    if margin >= .055 and top >= .10:
        return "Strong candidate", min(92,max(75,int(75+margin*220)))
    if margin >= .025 and top >= .055:
        return "Likely candidate", min(84,max(60,int(60+margin*240)))
    if margin >= .012 and top >= .035:
        return "Possible match", min(72,max(52,int(52+margin*260)))
    return "Needs confirmation", 50

# -----------------------------------------------------------------------------
# UI helpers

# -----------------------------------------------------------------------------
NAV=[("🏠","Home"),("📷","Identify a Plant"),("🩺","Plant Health Copilot"),("🌿","Plant Library"),("🔎","Search"),("❤️","My Plants"),("ℹ️","About")]

with st.sidebar:
    st.markdown('<div class="pc-brand"><div class="pc-logo"><svg viewBox="0 0 64 64" width="64" height="64" role="img" aria-label="PlantCare AI logo"><circle cx="32" cy="32" r="29" fill="#f8ffe8" stroke="#9bce57" stroke-width="3"/><path d="M17 42 C16 24 29 14 47 13 C47 30 38 44 22 46 Z" fill="#168348"/><path d="M19 49 C26 37 33 29 43 20" fill="none" stroke="#eaf8bd" stroke-width="3" stroke-linecap="round"/><path d="M30 36 C28 29 25 25 20 23 C19 31 23 36 30 36 Z" fill="#9bd65d"/></svg></div><div><div class="pc-brand-title">PlantCare AI</div><div class="pc-brand-sub">Identify • Learn • Care</div></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="pc-nav-title">Menu</div>',unsafe_allow_html=True)
    for icon,name in NAV:
        if st.button(f"{icon}  {name}",key=f"nav_{name}",width="stretch",type="primary" if st.session_state.page==name else "secondary"):
            st.session_state.page=name
            st.session_state.analysis=None
            st.rerun()
    st.markdown('<div class="pc-page-byline" style="justify-content:flex-start;margin:0 0 12px">🌿 Made by <strong>Aradhy Mundhe</strong></div>',unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown(f'<div class="pc-card" style="padding:16px"><div style="font-size:.72rem;color:#64766b;font-weight:800">PLANT LIBRARY</div><div style="font-size:1.45rem;font-weight:900;color:#0b6b39">{len(PLANTS)} plants</div><div style="font-size:.76rem;color:#64766b;margin-top:5px">Open-source vision model • No paid API key</div></div>',unsafe_allow_html=True)

st.markdown('<div class="pc-page-byline">🌿 Made by <strong>Aradhy Mundhe</strong></div>',unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Plant reference images
# -----------------------------------------------------------------------------
@st.cache_data(ttl=86400, show_spinner=False)
def _inat_exact_photo(scientific_name: str) -> str | None:
    """Return a photo from an exact iNaturalist taxon match.

    The lookup is based on the scientific name, not a free-text image search.
    This prevents unrelated people/objects from becoming plant references.
    """
    name = str(scientific_name or "").strip()
    if not name:
        return None
    try:
        r = requests.get(
            "https://api.inaturalist.org/v1/taxa",
            params={"q": name, "per_page": 10, "order_by": "relevance"},
            headers={"User-Agent": "PlantCareAI/1.0 (student project)"},
            timeout=10,
        )
        r.raise_for_status()
        for taxon in r.json().get("results", []):
            returned = str(taxon.get("name", "")).strip()
            if returned.lower() != name.lower():
                continue
            photo = taxon.get("default_photo") or {}
            url = photo.get("medium_url") or photo.get("square_url") or photo.get("original_url")
            if url:
                return str(url)
    except Exception:
        return None
    return None

@st.cache_data(ttl=86400, show_spinner=False)
def _wiki_exact_photo(title: str) -> str | None:
    """Return a thumbnail only from an exact Wikipedia article.

    This is a last-resort fallback after exact botanical-taxon lookup. Broad
    Wikipedia search is deliberately never used. Disambiguation pages are
    rejected so unrelated search results cannot become reference photos.
    """
    title = str(title or "").strip()
    if not title:
        return None
    try:
        r = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query", "format": "json", "redirects": 1,
                "prop": "pageimages|pageprops", "piprop": "thumbnail",
                "pithumbsize": 700, "ppprop": "disambiguation", "titles": title,
            },
            headers={"User-Agent": "PlantCareAI/1.0 (student project)"},
            timeout=10,
        )
        r.raise_for_status()
        pages = r.json().get("query", {}).get("pages", {})
        for page in pages.values():
            if page.get("missing") is not None:
                continue
            if "disambiguation" in page.get("pageprops", {}):
                continue
            thumb = page.get("thumbnail", {}).get("source")
            if thumb:
                return str(thumb)
    except Exception:
        return None
    return None

# Verified Wikimedia Commons plant photos used as a deterministic final fallback
# for the two records that previously had incorrect/unavailable references.
_VERIFIED_PLANT_PHOTOS = {
    "rose": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Rose_rosa.jpg",
    "rosa": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Rose_rosa.jpg",
    "tradescantia zebrina": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Tradescantia_zebrina.png",
}

@st.cache_data(ttl=86400, show_spinner=False)
def get_plant_photos_for_records(records: Tuple[Tuple[str, str], ...]) -> Dict[str, str]:
    """Resolve each library record to a real plant photo.

    Priority:
      1. Deterministic verified fallback for known problem records.
      2. Exact scientific-name iNaturalist taxon photo.
      3. Exact Wikipedia article thumbnail as a final fallback.
    No free-text image search is used anywhere in the library.
    """
    result: Dict[str, str] = {}
    for common, scientific in records:
        common = str(common or '').strip()
        scientific = str(scientific or '').strip()
        url = (_VERIFIED_PLANT_PHOTOS.get(common.lower()) or
               _VERIFIED_PLANT_PHOTOS.get(scientific.lower()))
        if not url and scientific:
            url = _inat_exact_photo(scientific)
        if not url and scientific:
            url = _wiki_exact_photo(scientific)
        if not url and common:
            # Common-name lookup is still exact, never a search result list.
            url = _wiki_exact_photo(common)
        if url:
            if common:
                result[common.lower()] = url
            if scientific:
                result[scientific.lower()] = url
    return result

@st.cache_data(ttl=86400, show_spinner=False)
def get_plant_photos(names: Tuple[str, ...]) -> Dict[str, str]:
    """Backward-compatible photo resolver for profile pages."""
    names = tuple(str(n).strip() for n in names if str(n).strip())
    result: Dict[str, str] = {}
    for n in names:
        key = n.lower()
        if key in _VERIFIED_PLANT_PHOTOS:
            result[key] = _VERIFIED_PLANT_PHOTOS[key]
            continue
        url = _inat_exact_photo(n) or _wiki_exact_photo(n)
        if url:
            result[key] = url
    return result

def fetch_reference_image(url: str) -> bytes | None:
    """Fetch and validate the image server-side so browser hotlink failures do not break cards."""
    if not url: return None
    try:
        r=requests.get(url, headers={"User-Agent":"PlantCareAI/1.0 (student project)"}, timeout=12)
        r.raise_for_status()
        if len(r.content)<1000: return None
        Image.open(io.BytesIO(r.content)).verify()
        return r.content
    except Exception:
        return None

def botanical_fallback(p: dict, width: int=720, height: int=430) -> Image.Image:
    """Offline visual fallback: every plant still has a clean botanical reference card."""
    img=Image.new("RGB",(width,height),(241,250,244)); d=ImageDraw.Draw(img); cx=width//2; base=height-48
    d.rounded_rectangle((28,28,width-28,height-28),radius=24,outline=(190,221,200),width=3,fill=(248,253,249))
    d.rounded_rectangle((cx-75,base-12,cx+75,base+28),radius=16,fill=(104,169,119),outline=(75,137,92),width=2)
    d.line((cx,base-12,cx,125),fill=(45,119,70),width=12)
    for side,y,size in [(-1,290,34),(1,250,38),(-1,205,30),(1,170,34),(-1,140,26),(1,125,24)]:
        x=cx+side*size; d.ellipse((x-size,y-size//2,x+size,y+size//2),fill=(65,157,87),outline=(42,120,63),width=2)
    cat=str(p.get("category","")).lower()
    if any(k in cat for k in ["flower","ornamental"]):
        for dx,dy in [(-28,115),(0,100),(28,115)]: d.ellipse((cx+dx-12,dy-12,cx+dx+12,dy+12),fill=(232,174,78),outline=(180,125,45),width=2)
    elif any(k in cat for k in ["fruit","tree"]):
        for dx,dy in [(-25,175),(24,145),(30,215)]: d.ellipse((cx+dx-11,dy-11,cx+dx+11,dy+11),fill=(229,183,63),outline=(180,135,35),width=2)
    d.text((48,48),"PLANT REFERENCE",fill=(11,107,57)); d.text((48,78),str(p.get("common_name","Plant")),fill=(23,50,37)); d.text((48,102),str(p.get("scientific_name","")),fill=(100,118,107))
    return img

def get_plant_photo_bytes(p: dict, photo_map: Dict[str,str] | None=None) -> bytes | None:
    url=None
    if photo_map is not None:
        for n in (p.get("scientific_name",""),p.get("common_name","")):
            key=str(n).strip().lower()
            if key in photo_map: url=photo_map[key]; break
    if not url:
        names=(str(p.get("scientific_name","")),str(p.get("common_name","")))
        photos=get_plant_photos(tuple(x for x in names if x))
        for n in names:
            if n.strip().lower() in photos: url=photos[n.strip().lower()]; break
    return fetch_reference_image(url) if url else None

def plant_photo(p: dict, width: int=700, photo_map: Dict[str,str] | None=None):
    data=get_plant_photo_bytes(p,photo_map)
    if data:
        st.image(data,width="stretch",caption=f"Reference photo • {p['common_name']}")
    else:
        st.image(botanical_fallback(p),width="stretch",caption=f"Plant reference • {p['common_name']}")
        st.caption("Reference photo is temporarily unavailable; this offline botanical reference keeps the library usable.")


# -----------------------------------------------------------------------------
# Profiles / library
# -----------------------------------------------------------------------------
def show_profile(p:dict, photo_map: Dict[str,str] | None = None):
    st.markdown(f'<div class="pc-result"><div class="pc-result-name">{p["common_name"]}</div><div class="pc-scientific"><i>{p["scientific_name"]}</i> · {p["family"]} · {p["category"]}</div></div>',unsafe_allow_html=True)
    photo_col, info_col = st.columns([0.85, 1.15], gap="large")
    with photo_col:
        plant_photo(p, photo_map=photo_map)
    with info_col:
        st.markdown("### Quick identification")
        st.write(p["identification"])
        st.markdown(f'<div class="pc-info"><b>Common name:</b> {p["common_name"]}<br><b>Scientific name:</b> <i>{p["scientific_name"]}</i><br><b>Category:</b> {p["category"]}</div>', unsafe_allow_html=True)
    a,b=st.columns(2)
    with a:
        st.markdown("### 🔎 Identification"); st.write(p["identification"])
        st.markdown("### 🌱 Appearance"); st.write("**Leaves:**",p["leaf"]); st.write("**Flowers:**",p["flower"]); st.write("**Growth:**",p["growth"]); st.write("**Typical size:**",p["size"]); st.write("**Similar plants:**",p["similar"])
        st.markdown("### ☀️ Growing conditions"); st.write("**Indoor/outdoor:**",p["indoor_outdoor"]); st.write("**Light:**",p["light"]); st.write("**Water:**",p["water"]); st.write("**Soil:**",p["soil"]); st.write("**Temperature:**",p["temperature"]); st.write("**Humidity:**",p["humidity"])
    with b:
        st.markdown("### 🌿 Care"); st.write("**Fertilizer:**",p["fertilizer"]); st.write("**Propagation:**",p["propagation"]); st.write("**Pruning:**",p["pruning"])
        st.markdown("### 🐛 Problems"); st.write("**Pests:**",p["pests"]); st.write("**Diseases:**",p["diseases"])
        st.markdown("### ⚠️ Safety"); st.write("**Plant safety:**",p["toxicity"]); st.write("**Pet safety:**",p["pet_safety"])
        st.markdown("### 🇮🇳 India relevance"); st.write(p["india_relevance"])
    if p["common_name"] in st.session_state.my_plants:
        if st.button("Remove from My Plants",key="remove_"+p["common_name"]):
            st.session_state.my_plants.remove(p["common_name"]); save_my_plants(st.session_state.my_plants); st.rerun()
    else:
        if st.button("❤️ Add to My Plants",key="add_"+p["common_name"]):
            st.session_state.my_plants.append(p["common_name"]); save_my_plants(st.session_state.my_plants); st.rerun()


page=st.session_state.page

# -----------------------------------------------------------------------------
# Home
# -----------------------------------------------------------------------------
# Shared PlantCare AI logo used across upload cards and page headers.
logo_svg = """<svg viewBox="0 0 64 64" width="64" height="64" role="img" aria-label="PlantCare AI logo"><circle cx="32" cy="32" r="29" fill="#f8ffe8" stroke="#9bce57" stroke-width="3"/><path d="M17 42 C16 24 29 14 47 13 C47 30 38 44 22 46 Z" fill="#168348"/><path d="M19 49 C26 37 33 29 43 20" fill="none" stroke="#eaf8bd" stroke-width="3" stroke-linecap="round"/><path d="M30 36 C28 29 25 25 20 23 C19 31 23 36 30 36 Z" fill="#9bd65d"/></svg>"""

if page=="Home":
    st.markdown('''<div class="pc-home-hero"><div class="eyebrow">Smarter care for healthier plants</div><div class="mark"><div class="leaf-icon"></div><div><h1>PlantCare AI</h1><div class="tagline">Healthy Plants&nbsp; 🌿 Greener Tomorrow</div></div></div><div class="copy">Identify a plant, discover its needs, and build better care habits — all in one friendly place.</div><div class="pc-pills"><span class="pc-pill">📸 Photo identification</span><span class="pc-pill">🌿 56 plant profiles</span><span class="pc-pill">🛡️ Smart rejection</span><span class="pc-pill">💚 Practical care guidance</span></div></div>''',unsafe_allow_html=True)
    st.markdown(
        '<div class="pc-card" style="margin:0 0 18px;border-left:6px solid #168044">'
        '<h3>👋 Welcome! I am PlantCare AI.</h3>'
        '<p>I help you explore 56 plant profiles, identify a possible plant from a photo, compare look-alike species, understand basic care needs, and work through plant-health observations. I show uncertainty when evidence is limited; I cannot guarantee every identification or diagnose a disease.</p>'
        '<p><b>How to start:</b> open <i>Identify a Plant</i> to upload a clear photo, or open <i>Plant Health Copilot</i> to describe symptoms and growing conditions.</p></div>',
        unsafe_allow_html=True,
    )
    st.components.v1.html('''
    <div style="font-family:Arial,sans-serif;padding:0 2px 10px">
      <button id="pcSpeakIntro" style="background:#0b754b;color:white;border:0;border-radius:12px;padding:10px 16px;font-weight:700;cursor:pointer">🔊 Hear the introduction</button>
      <span id="pcSpeakStatus" style="font-size:13px;color:#426450;margin-left:8px">Audio starts only when you press the button.</span>
    </div>
    <script>
      const b=document.getElementById('pcSpeakIntro'); const status=document.getElementById('pcSpeakStatus');
      b.addEventListener('click',()=>{
        try {
          if (!('speechSynthesis' in window) || !('SpeechSynthesisUtterance' in window)) { status.textContent='Speech is not supported in this browser. The introduction is available above as text.'; return; }
          window.speechSynthesis.cancel();
          const u=new SpeechSynthesisUtterance('Welcome to PlantCare AI. I help you explore our library of 56 plants, identify possible plant matches from photographs, compare similar species, and review plant-care concerns with the Plant Health Copilot. For the most useful results, upload a clear photo and check the suggested match carefully. My guidance is educational and cannot guarantee an identification or diagnose a disease. Let us help your plants grow.');
          u.lang='en-IN'; u.rate=0.90; u.pitch=1.0; u.volume=1.0;
          const chooseVoice=()=>{
            const voices=window.speechSynthesis.getVoices() || [];
            const english=voices.filter(v=>/^en(-|_)/i.test(v.lang));
            const preferred=english.find(v=>/en-IN/i.test(v.lang) && /Google|Natural|Neural|Microsoft/i.test(v.name))
              || english.find(v=>/en-IN/i.test(v.lang))
              || english.find(v=>/Google|Natural|Neural|Microsoft/i.test(v.name))
              || english[0];
            if(preferred) u.voice=preferred;
            window.speechSynthesis.speak(u);
          };
          const voices=window.speechSynthesis.getVoices();
          if(voices.length) chooseVoice(); else { window.speechSynthesis.onvoiceschanged=()=>{ window.speechSynthesis.onvoiceschanged=null; chooseVoice(); }; setTimeout(()=>{ if(window.speechSynthesis.speaking===false && window.speechSynthesis.pending===false) chooseVoice(); },350); }
          status.textContent='Playing the best available English voice on this device…';
        } catch(e) { status.textContent='Could not play audio in this browser. Try another browser or use the written introduction above.'; }
      });
    </script>
    ''', height=54)
    stat_cols=st.columns(4)
    for col,emoji,value,label in zip(stat_cols,["🌱","🎯","💚","🌎"],[str(len(PLANTS)),"AI","Care","Green"],["Plant Species","Photo Identification","Plant Care Support","Greener Future"]):
        with col:
            st.markdown(f'<div class="pc-home-stat"><div class="symbol">{emoji}</div><div class="value">{value}</div><div class="label">{label}</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="pc-title">🌼 Start exploring</div>',unsafe_allow_html=True)
    a,b,c=st.columns(3)
    home_destinations=[
        (a,"📸 Identify a Plant","Take a photo or upload an image to find a possible plant match, then review its care profile.","Identify a Plant","home_identify"),
        (b,"🌳 Explore the Plant Library","Browse plant photos, botanical names, growing conditions, common problems and safety information.","Plant Library","home_library"),
        (c,"🪴 My Plants & Reminders","Keep track of your plants and set reminders for watering, sunlight, pruning and other care tasks.","My Plants","home_myplants"),
    ]
    for col,title,desc,destination,key in home_destinations:
        with col:
            st.markdown(f'<div class="pc-card"><h3>{title}</h3><p>{desc}</p></div>',unsafe_allow_html=True)
            if st.button("Open →",key=key,width="stretch",type="primary"):
                st.session_state.page=destination
                st.session_state.analysis=None
                st.rerun()
    st.markdown('<div class="pc-title">🌱 Your plant-care journey</div>',unsafe_allow_html=True)
    steps=st.columns(4)
    journey=[
        (steps[0],"📷","Capture","Choose a clear plant photo.","Identify a Plant","journey_capture"),
        (steps[1],"🔎","Identify","Review a possible match.","Identify a Plant","journey_identify"),
        (steps[2],"🌞","Learn","Understand light, water and soil.","Plant Library","journey_learn"),
        (steps[3],"🪴","Care","Save plants and plan routines.","My Plants","journey_care"),
    ]
    for col,emoji,title,desc,destination,key in journey:
        with col:
            st.markdown(f'<div class="pc-mini" style="min-height:145px"><div style="font-size:2rem;margin-bottom:7px">{emoji}</div><b>{title}</b><span>{desc}</span></div>',unsafe_allow_html=True)
            if st.button(f"{title} →",key=key,width="stretch"):
                st.session_state.page=destination
                st.session_state.analysis=None
                st.rerun()
    st.markdown('<div class="pc-card" style="margin-top:16px"><h3>🩺 New: Plant Health Copilot</h3><p>Report symptoms and growing conditions to receive a cautious, evidence-based checklist of possible causes and safe next steps. It does not claim to diagnose a disease from one photo.</p></div>',unsafe_allow_html=True)
    if st.button("Open Plant Health Copilot →", key="home_copilot_open", type="primary"):
        st.session_state.page = "Plant Health Copilot"
        st.rerun()
    st.markdown('<div class="pc-info" style="margin-top:18px"><b>🌿 Our approach:</b> Helpful plant information with honest uncertainty. Photo-based suggestions are guidance, not a guaranteed botanical diagnosis.</div>',unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Identify
# -----------------------------------------------------------------------------
elif page=="Identify a Plant":
    st.markdown('<div class="pc-hero" style="padding:27px 30px;background:linear-gradient(110deg,#f7f7e8,#e3efd4)!important;color:#063b2b!important"><h1 style="font-size:2.45rem;color:#063b2b!important">🌿 Identify a Plant</h1><p>Take a photo or choose one from your gallery. PlantCare AI first checks whether the image actually contains a plant, then performs species matching. It will refuse a guess when the evidence is weak.</p><div class="pc-pills"><span class="pc-pill">🛡️ Non-plant gate</span><span class="pc-pill">🧠 Multi-view vision</span><span class="pc-pill">🌿 56-plant library</span><span class="pc-pill">⚠️ No forced guess</span></div></div>',unsafe_allow_html=True)
    if "selected_image_bytes" not in st.session_state:
        st.session_state.selected_image_bytes = None
    if "selected_image_source" not in st.session_state:
        st.session_state.selected_image_source = None
    if "selected_image_name" not in st.session_state:
        st.session_state.selected_image_name = ""

    upload_camera, upload_gallery = st.columns(2, gap="large")
    with upload_camera:
        st.markdown('<div class="pc-upload-card"><div class="pc-ref-logo">'+logo_svg+'</div><div class="pc-upload-title">📷 Use Camera</div><div class="pc-upload-sub">Take a photo of your plant.</div></div>',unsafe_allow_html=True)
        camera=st.camera_input("Camera", label_visibility="collapsed", resolution="720p", key="camera_input_v10")
        if camera is not None:
            st.session_state.selected_image_bytes = camera.getvalue()
            st.session_state.selected_image_source = "Camera"
            st.session_state.selected_image_name = "camera_photo"
            st.session_state.analysis = None
    with upload_gallery:
        st.markdown('<div class="pc-upload-card"><div class="pc-ref-logo">'+logo_svg+'</div><div class="pc-upload-title">🖼️ Upload from Gallery</div><div class="pc-upload-sub">Choose an image from your device.</div></div>',unsafe_allow_html=True)
        uploaded=st.file_uploader("Gallery",type=["jpg","jpeg","png","webp"],label_visibility="collapsed", key="gallery_input_v10")
        if uploaded is not None:
            st.session_state.selected_image_bytes = uploaded.getvalue()
            st.session_state.selected_image_source = "Gallery"
            st.session_state.selected_image_name = uploaded.name or "gallery_photo"
            st.session_state.analysis = None
    st.markdown('<div class="pc-how"><div class="pc-how-title">How It Works?</div><div class="pc-how-grid"><div class="pc-how-step"><div class="pc-how-icon">🛡️</div><b>1. Smart Rejection</b><span>Non-plant check</span></div><div class="pc-how-step"><div class="pc-how-icon">🌿</div><b>2. Visual Health Check</b><span>Plant health analysis</span></div><div class="pc-how-step"><div class="pc-how-icon">🔬</div><b>3. Plant Identification</b><span>BioCLIP vision model</span></div><div class="pc-how-step"><div class="pc-how-icon">🌱</div><b>4. Care Recommendations</b><span>Care checklist</span></div></div></div>',unsafe_allow_html=True)

    raw=st.session_state.selected_image_bytes
    if raw:
        try:
            image=ImageOps.exif_transpose(Image.open(__import__("io").BytesIO(raw))).convert("RGB")
            st.markdown(f'<div class="pc-selected-label">✓ {st.session_state.selected_image_source} photo selected</div>',unsafe_allow_html=True)
            st.image(image,caption="Selected image",width="stretch")

            with st.expander("Optional plant clues — improves matching when you know them", expanded=False):
                c1,c2,c3=st.columns(3)
                with c1: leaf_shape=st.selectbox("Leaf shape",["Not sure","Heart-shaped","Long/strap-like","Broad/oval","Needle-like","Lobed","Round","Feathery"],key="leaf_shape_v5")
                with c2: leaf_texture=st.selectbox("Leaf texture",["Not sure","Fleshy/thick","Glossy","Hairy/rough","Thin","Leathery"],key="leaf_texture_v5")
                with c3: flowers=st.selectbox("Flowers",["Not sure","None visible","White","Yellow","Pink/red","Purple/blue","Orange"],key="flowers_v5")
                c4,c5=st.columns(2)
                with c4: growth=st.selectbox("Growth habit",["Not sure","Upright","Trailing/vining","Clumping","Tree/shrub","Rosette"],key="growth_v5")
                with c5: thorns=st.selectbox("Thorns / spines",["Not sure","Present","Not visible"],key="thorns_v5")

            id_engine_copy = "PlantCare AI compares the image with botanical descriptions for the 56 supported species using the original BioCLIP vision model. The filename is never used to choose the plant. Results are model-ranked suggestions, not a guarantee of identity."
            st.markdown(f'<div class="pc-analyze-box"><div><b>Ready to identify this photo?</b><br><span>{id_engine_copy}</span></div></div>',unsafe_allow_html=True)
            analyze=st.button("🔎  ANALYZE IMAGE",type="primary",width="stretch",key="analyze_v10")
            cclear,_=st.columns([1,4])
            with cclear:
                if st.button("Clear photo",width="stretch",key="clear_v5"):
                    st.session_state.selected_image_bytes=None
                    st.session_state.selected_image_source=None
                    st.session_state.selected_image_name=""
                    st.session_state.analysis=None
                    st.rerun()

            if analyze:
                sharp,bright,mindim=image_quality(image)
                if mindim<100 or bright<5 or sharp<1:
                    st.session_state.analysis=None
                    st.markdown('<div class="pc-warning"><b>🟡 Photo quality is too low.</b><br>Use daylight and move closer so leaves, flowers or the whole plant are clearly visible.</div>',unsafe_allow_html=True)
                else:
                    with st.spinner("Analyzing plant photo… first run may take longer while the vision model loads."):
                        clues=clue_tokens(leaf_shape,leaf_texture,flowers,growth,thorns)
                        # Stage 1: explicitly verify plant presence before ranking the
                        # image against the 56 library species. Camera and gallery share
                        # the same normalized image pipeline and decision gate.
                        reject_object=False
                        object_reason=""
                        general_meta={}
                        try:
                            gate_is_plant, gate_score, gate_reason, gate_meta = vision_gate(image)
                            general_meta = gate_meta
                            if not gate_is_plant:
                                reject_object = True
                                object_reason = gate_reason or "Plant not detected with enough confidence"
                        except Exception as gate_exc:
                            # A screening-stage exception is not proof that an image
                            # contains no plant. Continue to the independent species
                            # and BioCLIP plant/object checks; surface errors only if
                            # those checks cannot produce a usable result.
                            general_meta = {"gate_unavailable": type(gate_exc).__name__}
                            reject_object = False
                        # Run the BioCLIP safety screen once before species ranking.
                        # Ambiguous safety evidence is allowed through; only decisive
                        # non-plant/document evidence blocks the species classifier.
                        if not reject_object:
                            try:
                                _, bio_plant_score, _, object_meta = bioclip_gate(image)
                                bio_object_score = float(object_meta.get("object_score", 0.0))
                                accepted, bio_reason, bio_category = decide_vision_gate(
                                    quality_ok=True,
                                    general_object_rejected=False,
                                    bio_plant_score=float(bio_plant_score),
                                    bio_object_score=bio_object_score,
                                    document_score=_document_visual_score(image),
                                )
                                if not accepted:
                                    reject_object = True
                                    object_reason = bio_reason
                            except Exception:
                                # Model-screen failure is not proof that the image is
                                # non-plant; let species matching attempt a result.
                                pass

                        if reject_object:
                            st.session_state.analysis = {"nonplant": True, "reason": object_reason, "score": 0.0}
                        else:
                            ai_rows, model_used, model_error = optional_vision_rank(image, st.session_state.get("selected_image_name", ""))
                            if model_used and ai_rows:
                                rows = ai_rows
                                if clues:
                                    adjusted = []
                                    for p, s in rows:
                                        txt = " ".join(str(p.get(k, "")) for k in ["common_name", "category", "identification", "leaf", "flower", "growth", "similar"]).lower()
                                        bonus = sum(.01 for clue in clues if clue in txt)
                                        adjusted.append((p, min(1.0, s + bonus)))
                                    rows = sorted(adjusted, key=lambda x: x[1], reverse=True)
                                label, conf = confidence_label(rows)
                                model_note = "Original BioCLIP local biology vision model (56 supported species)"
                                health = visual_health_screen(image)
                                care = care_assessment(image, rows[0][0], health)
                                st.session_state.analysis = {
                                    "rows": rows, "label": label, "conf": conf, "score": 1.0,
                                    "model_note": model_note, "model_error": model_error,
                                    "health": health, "care": care, "species_unavailable": False
                                }
                            elif not reject_object:
                                # A model-loading failure is not evidence that a photo contains
                                # no plant. Do not invent species matches from colour or manual clues.
                                st.session_state.analysis={
                                    "rows":[], "label":"Identification unavailable", "conf":0,
                                    "model_note":"Vision model unavailable", "model_error":model_error,
                                    "health":None, "care":None, "species_unavailable":True
                                }
        except Exception as exc:
            st.session_state.analysis=None
            # Distinguish a genuinely invalid image from a processing bug. This avoids
            # misleading users into repeatedly re-uploading valid photos after a code error.
            try:
                Image.open(io.BytesIO(raw)).verify()
                image_is_readable = True
            except Exception:
                image_is_readable = False
            if image_is_readable:
                st.error(f"The image was opened, but analysis failed because of an internal processing error ({type(exc).__name__}). Please retry once; if it repeats, report this message to the project maintainer.")
            else:
                st.error("This image file could not be decoded. Please upload a standard JPG or PNG photo, or take a new photo with the camera.")
    else:
        st.markdown('<div class="pc-card"><h3>📌 Start here</h3><p>Choose <b>Camera</b> to take a photo or <b>Gallery</b> to upload one. After the image appears, the green <b>ANALYZE IMAGE</b> button will always be available.</p></div>',unsafe_allow_html=True)

    result=st.session_state.analysis
    if result and result.get("nonplant"):
        st.markdown(f'<div class="pc-error"><b>🚫 NO PLANT DETECTED / PLANT NOT VERIFIED</b><br>{result["reason"]}. Try a clear, well-lit photo of a real plant with leaves, stems or flowers filling most of the frame. Ordinary objects must not be forced into a plant name.</div>',unsafe_allow_html=True)
    elif result and result.get("species_unavailable"):
        st.markdown('<div class="pc-warning"><b>🌿 Species identification is temporarily unavailable.</b><br>The vision model could not produce a reliable result, so PlantCare AI will not guess a species or claim that a plant was confirmed. Check the deployment logs and retry when the model is available.</div>',unsafe_allow_html=True)
        health=result.get("health")
        if health:
            st.markdown("### 🩺 Visual health screening")
            st.markdown(f'<div class="pc-result"><div class="pc-result-name" style="font-size:1.35rem">{health["level"]}</div><div class="pc-scientific">{health["status"]}</div></div>',unsafe_allow_html=True)
            st.caption("Health screening is visual only and does not identify a disease.")
    elif result and result.get("rows"):
        top=result["rows"][0][0]
        if result.get("label") == "Needs confirmation":
            st.warning("🌿 POSSIBLE PLANT MATCH — CONFIRMATION NEEDED")
        elif result.get("label") == "Possible match":
            st.info("🌿 POSSIBLE PLANT MATCH — CHECK THE ALTERNATIVES")
        else:
            st.success("🌱 TOP PLANT MATCH FOUND — VERIFY VISUALLY")
        st.caption(f"Analysis engine: {result.get('model_note','')}")
        if result.get("model_error"):
            st.warning("The main vision model could not be loaded, so this result is only a local shortlist. Check the internet connection and try Analyze again.")
        st.markdown(f'<div class="pc-result"><div style="font-size:.78rem;font-weight:900;color:#64766b;text-transform:uppercase;letter-spacing:.08em">TOP PLANT MATCH</div><div class="pc-result-name">🌿 {top["common_name"]}</div><div class="pc-scientific"><b>Common name:</b> {top["common_name"]} &nbsp; · &nbsp; <i>{top["scientific_name"]}</i> · {top["family"]}</div><div class="pc-badge">{result["label"]} · relative model ranking</div></div>',unsafe_allow_html=True)
        # Show an independent real reference photo so the user can visually compare
        # the prediction instead of trusting the text label alone.
        reference_records = tuple(
            (item[0]["common_name"], item[0]["scientific_name"])
            for item in result["rows"][:4]
        )
        reference_map = get_plant_photos_for_records(reference_records)
        photo_col, compare_col = st.columns([1, 2])
        with photo_col:
            plant_photo(top, photo_map=reference_map)
            st.caption("Reference image from an exact botanical taxon/article match when available; compare it with your upload.")
        with compare_col:
            st.markdown("**Visual cross-check before accepting the result**")
            st.write(f"Expected scientific name: *{top['scientific_name']}*")
            st.write(top.get("identification", "Compare the visible leaves, stems, flowers, and growth habit."))
            st.info("Reference photos support visual comparison; they are not training images and do not guarantee the prediction is correct.")
        if result["label"] in ["Possible match","Needs confirmation"] or "confirm visually" in result["label"]:
            st.markdown('<div class="pc-warning"><b>Confirm before relying on the name:</b> visually similar plants can look alike. Use the alternatives and the reference photo below.</div>',unsafe_allow_html=True)
        st.markdown('<div class="pc-info"><b>How to read the result:</b> the label describes relative separation between model candidates, not a calibrated probability. Compare the alternative species and visible traits before relying on the name.</div>',unsafe_allow_html=True)

        # Signature feature: explainable match passport. These are profile traits
        # for the user to compare with the uploaded photo, not claims that every
        # listed trait was detected by the vision model.
        st.markdown("### 🧭 PlantMatch Intelligence")
        st.markdown("**Why this is a candidate:** compare the visible features in your photo with this plant profile. The model ranks visual similarity; it does not prove a species from one image.")
        trait_cols=st.columns(3)
        trait_items=[
            ("🍃 Leaf clues",top.get("leaf","Compare leaf shape, arrangement and veins with the profile.")),
            ("🌸 Flower clues",top.get("flower","Flower details may help when flowers are visible.")),
            ("🌿 Growth habit",top.get("growth","Compare the overall growth pattern with the profile.")),
        ]
        for trait_col,(trait_title,trait_text) in zip(trait_cols,trait_items):
            with trait_col:
                st.markdown(f'<div class="pc-card"><h3>{trait_title}</h3><p>{trait_text}</p></div>',unsafe_allow_html=True)
        st.caption("Evidence boundary: a visual match is not a botanical confirmation. If the top candidates look similar, photograph the leaves and flowers separately in good light.")
        st.markdown("### 🌿 Other possible matches")
        alt=result["rows"][1:4]
        alt_map=reference_map
        for p,s in alt:
            col1,col2=st.columns([1,2])
            with col1:
                plant_photo(p, photo_map=alt_map)
            with col2:
                st.markdown(f'<div class="pc-card"><h3>{p["common_name"]}</h3><p><i>{p["scientific_name"]}</i><br>Visual score: {s:.3f}</p></div>',unsafe_allow_html=True)
        health=result.get("health")
        if health:
            st.markdown("### 🩺 Visual health screening")
            st.markdown(f'<div class="pc-result"><div class="pc-result-name" style="font-size:1.35rem">{health["level"]}</div><div class="pc-scientific">{health["status"]}</div></div>',unsafe_allow_html=True)
            if health.get("screenable", True):
                hc1,hc2,hc3=st.columns(3)
                with hc1: st.metric("Green-toned pixels",f'{health["green"]*100:.0f}%')
                with hc2: st.metric("Yellow-toned pixels",f'{health["yellow"]*100:.0f}%')
                with hc3: st.metric("Brown-toned pixels",f'{health["brown"]*100:.0f}%')
                st.caption("These percentages describe colour patterns among selected plant-like pixels, not the percentage of healthy or damaged leaves. Flowers, soil, lighting and backgrounds can affect them.")
            else:
                st.info("There is not enough clearly screenable plant-like colour for percentage estimates. Try a closer, well-lit photo of the leaves.")
            st.markdown(f'<div class="pc-warning"><b>Important:</b> {health_issue_text(top,health)}<br><small>This is a colour-pattern screen only. It cannot confirm plant health, diagnose disease, detect pests reliably, or measure soil moisture or nutrients.</small></div>',unsafe_allow_html=True)
        st.markdown("### 🩺 PlantCare check")
        care=result.get("care") or care_assessment(image, top, health or visual_health_screen(image))
        st.markdown('<div class="pc-info"><b>Care checklist:</b> the items below are prompts for physical checks. A photo alone cannot establish overall plant health or measure soil, roots or nutrients.</div>', unsafe_allow_html=True)
        care_cards=[
            ("💧 Water / hydration", care["water_status"], care["water_detail"]),
            ("🌿 Fertilizer", care["fertilizer_status"], care["fertilizer_detail"]),
            ("🦠 Disease", care["disease_status"], care["disease_detail"]),
            ("🐛 Pests", care["pest_status"], care["pest_detail"]),
            ("☀️ Sunlight", care["sunlight_status"], care["sunlight_detail"]),
            ("📈 Growth", care["growth_status"], care["growth_detail"]),
        ]
        for start in range(0, len(care_cards), 3):
            cols=st.columns(3)
            for col,(title,status,detail) in zip(cols, care_cards[start:start+3]):
                with col:
                    st.markdown(f'<div class="pc-card"><h3>{title}</h3><p><b>{status}</b><br>{detail}</p></div>',unsafe_allow_html=True)

        # Differentiating feature: transparent evidence-vs-unknowns care passport.
        # It deliberately avoids turning colour heuristics into a disease diagnosis.
        st.markdown("### 🧭 PlantCare Care Confidence Passport")
        st.markdown('''
        <div class="pc-card">
          <h3>What the photo can tell us — and what it cannot</h3>
          <p><b>Visible evidence:</b> approximate green, yellow, brown and dark colour patterns in the selected image.</p>
          <p><b>Care guidance:</b> light, watering, soil, fertilizer and common-problem information from the selected plant profile.</p>
          <p><b>Not measured by the camera:</b> soil moisture, nutrient levels, root health, exact sunlight exposure, or a confirmed pathogen.</p>
          <p><b>Next best step:</b> inspect the soil and leaf undersides, take a close-up of any affected area, and compare symptoms before applying fertilizer or treatment.</p>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown("### 🌱 Species care requirements")
        c1,c2,c3=st.columns(3)
        with c1:
            st.markdown(f'<div class="pc-card"><h3>💧 Watering</h3><p>{top.get("water", "See plant profile.")}</p></div>',unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="pc-card"><h3>☀️ Light</h3><p>{top.get("light", "See plant profile.")}</p></div>',unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="pc-card"><h3>💨 Humidity</h3><p>{top.get("humidity", "See plant profile.")}</p></div>',unsafe_allow_html=True)
        c4,c5,c6=st.columns(3)
        with c4:
            st.markdown(f'<div class="pc-card"><h3>🌱 Soil</h3><p>{top.get("soil", "See plant profile.")}</p></div>',unsafe_allow_html=True)
        with c5:
            st.markdown(f'<div class="pc-card"><h3>🌿 Fertilizer guidance</h3><p>{top.get("fertilizer", "See plant profile.")}</p></div>',unsafe_allow_html=True)
        with c6:
            st.markdown(f'<div class="pc-card"><h3>🐛 Pests & diseases to watch</h3><p>{top.get("pests", "Inspect regularly for pests.")}<br><br>{top.get("diseases", "See plant profile for common diseases.")}</p></div>',unsafe_allow_html=True)
        st.markdown('<div class="pc-info"><b>Important:</b> A single photo cannot directly measure soil moisture, fertilizer concentration, growth rate, sunlight exposure, or confirm a disease. PlantCare AI therefore labels these as checks or visual screens instead of pretending they are measured values.</div>',unsafe_allow_html=True)
        st.markdown("### 🌱 Plant profile")
        show_profile(top)


elif page=="Plant Library":
    st.markdown('<div class="pc-reference-banner"><div class="pc-ref-logo"><svg viewBox="0 0 64 64" width="64" height="64" role="img" aria-label="PlantCare AI logo"><circle cx="32" cy="32" r="29" fill="#f8ffe8" stroke="#9bce57" stroke-width="3"/><path d="M17 42 C16 24 29 14 47 13 C47 30 38 44 22 46 Z" fill="#168348"/><path d="M19 49 C26 37 33 29 43 20" fill="none" stroke="#eaf8bd" stroke-width="3" stroke-linecap="round"/><path d="M30 36 C28 29 25 25 20 23 C19 31 23 36 30 36 Z" fill="#9bd65d"/></svg></div><div><h2>🌿 Plant Library</h2><p>Explore 56 amazing plant species with detailed information.</p><p><b>Discover · Learn · Grow</b> — browse photos, names and care tips.</p></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="pc-title" style="margin-top:6px">🌸 Popular Plants</div>',unsafe_allow_html=True)
    popular_names=["Rose","Tulsi","Neem","Mango","Marigold"]
    popular=[PLANT_BY_NAME[n] for n in popular_names if n in PLANT_BY_NAME]
    if popular:
        pcols=st.columns(len(popular))
        pmap=get_plant_photos_for_records(tuple((p["common_name"],p["scientific_name"]) for p in popular))
        for pcol,p in zip(pcols,popular):
            with pcol:
                st.markdown('<div class="pc-featured">',unsafe_allow_html=True)
                plant_photo(p,photo_map=pmap)
                st.markdown(f'<div class="pc-featured-body"><h3>{p["common_name"]}</h3><p><i>{p["scientific_name"]}</i></p></div>',unsafe_allow_html=True)
                if st.button("View plant →",key="popular_"+p["common_name"],width="stretch"):
                    st.session_state.selected_plant=p["common_name"]; st.session_state.page="Search"; st.rerun()
                st.markdown('</div>',unsafe_allow_html=True)
    query=st.text_input("Search the plant library",placeholder="Search by common name, scientific name or category…",key="library_search_v7")
    f1,f2=st.columns(2)
    categories=sorted({str(p.get("category","Other")) for p in PLANTS})
    with f1: category=st.selectbox("Filter by category",["All categories"]+categories,key="library_category_v1")
    with f2: sort_mode=st.selectbox("Sort plants",["A–Z by common name","A–Z by scientific name"],key="library_sort_v1")
    q=query.strip().lower()
    items=[p for p in PLANTS if (not q or q in (p["common_name"]+" "+p["scientific_name"]+" "+p["category"]).lower()) and (category=="All categories" or p.get("category")==category)]
    items=sorted(items,key=lambda p:p["scientific_name" if sort_mode.endswith("scientific name") else "common_name"].lower())
    st.markdown(f'<div class="pc-library-count">Showing {len(items)} of {len(PLANTS)} plants</div>',unsafe_allow_html=True)
    if not items: st.info("No plants match those filters. Try a different name or category.")
    else:
        photo_map=get_plant_photos_for_records(tuple((x["common_name"],x["scientific_name"]) for x in items))
        cols=st.columns(3)
        for i,p in enumerate(items):
            with cols[i%3]:
                st.markdown('<div class="pc-featured">',unsafe_allow_html=True)
                plant_photo(p,photo_map=photo_map)
                st.markdown(f'<div class="pc-featured-body"><h3>🌿 {p["common_name"]}</h3><p><i>{p["scientific_name"]}</i><br>{p["category"]}</p></div>',unsafe_allow_html=True)
                if st.button("Open full profile",key="lib_"+p["common_name"],width="stretch"):
                    st.session_state.selected_plant=p["common_name"]; st.session_state.search_q=""; st.session_state.page="Search"; st.rerun()
                st.markdown('</div>',unsafe_allow_html=True)

elif page=="Search":
    st.markdown('<div class="pc-reference-banner"><div class="pc-ref-logo"><svg viewBox="0 0 64 64" width="64" height="64" role="img" aria-label="PlantCare AI logo"><circle cx="32" cy="32" r="29" fill="#f8ffe8" stroke="#9bce57" stroke-width="3"/><path d="M17 42 C16 24 29 14 47 13 C47 30 38 44 22 46 Z" fill="#168348"/><path d="M19 49 C26 37 33 29 43 20" fill="none" stroke="#eaf8bd" stroke-width="3" stroke-linecap="round"/><path d="M30 36 C28 29 25 25 20 23 C19 31 23 36 30 36 Z" fill="#9bd65d"/></svg></div><div><h2>🔎 Search Plants</h2><p>Find your plant quickly by name, category or features.</p></div></div>',unsafe_allow_html=True)
    if "search_q" not in st.session_state: st.session_state.search_q=""
    q=st.text_input("🔎 Search by plant name",value=st.session_state.search_q,placeholder="Search by plant name (e.g., Rose, Tulsi, Mango…)",key="search_box_v7")
    categories_search=["All"]+sorted({str(p.get("category","Other")) for p in PLANTS})
    search_category=st.radio("Browse categories",categories_search,horizontal=True,key="search_category_v2")
    st.session_state.search_q=q; ql=q.strip().lower()
    if not ql:
        quick=[p for p in PLANTS if search_category=="All" or p.get("category")==search_category][:5]
        st.markdown('<div class="pc-title" style="margin-top:14px">Quick Search</div>',unsafe_allow_html=True)
        if quick:
            qcols=st.columns(min(5,len(quick)))
            qmap=get_plant_photos_for_records(tuple((p["common_name"],p["scientific_name"]) for p in quick))
            for qcol,p in zip(qcols,quick):
                with qcol:
                    st.markdown('<div class="pc-featured">',unsafe_allow_html=True)
                    plant_photo(p,photo_map=qmap)
                    st.markdown(f'<div class="pc-featured-body"><h3>{p["common_name"]}</h3><p>{p["category"]}</p></div>',unsafe_allow_html=True)
                    if st.button("View →",key="quick_"+p["common_name"],width="stretch"):
                        st.session_state.selected_plant=p["common_name"]; st.rerun()
                    st.markdown('</div>',unsafe_allow_html=True)
    if ql:
        suggestions=[p for p in PLANTS if ql in (p["common_name"]+" "+p["scientific_name"]+" "+p["category"]).lower() and (search_category=="All" or p.get("category")==search_category)][:8]
        if suggestions:
            st.markdown("**Suggestions**")
            scols=st.columns(2)
            for i,p in enumerate(suggestions):
                with scols[i%2]:
                    if st.button(f"🌿 {p['common_name']} · {p['scientific_name']}",key="suggest_"+p["common_name"],width="stretch"):
                        st.session_state.search_q=p["common_name"]; st.session_state.selected_plant=p["common_name"]; st.rerun()
        else:
            st.info("No plant suggestion yet. Try another spelling or search by scientific name.")
    selected=st.session_state.get("selected_plant")
    if selected and (not ql or selected.lower()==ql):
        p=PLANT_BY_NAME.get(selected)
        st.session_state.pop("selected_plant",None)
        if p: show_profile(p)
    elif ql:
        matches=[p for p in PLANTS if ql in (p["common_name"]+" "+p["scientific_name"]+" "+p["category"]).lower() and (search_category=="All" or p.get("category")==search_category)]
        if len(matches)==1: show_profile(matches[0])
        elif len(matches)>1:
            st.markdown("### Matching plants")
            for p in matches:
                if st.button(f"🌿 {p['common_name']} — {p['scientific_name']}",key="match_"+p["common_name"],width="stretch"):
                    st.session_state.selected_plant=p["common_name"]; st.rerun()

elif page=="My Plants":
    st.markdown('<div class="pc-hero" style="padding:27px 30px"><h1 style="font-size:2.35rem">❤️ My Plants</h1><p>Add your plants directly and create reminders for watering, fertilizer, sunlight, pest checks and other care tasks.</p></div>',unsafe_allow_html=True)
    render_due_reminder_alerts()
    now=india_now_naive()
    st.markdown("### ➕ Add a plant to My Plants")
    add_col1,add_col2=st.columns([2,1])
    with add_col1:
        add_choice=st.selectbox("Choose a plant",[p["common_name"] for p in PLANTS],key="myplant_add_choice_v7")
    with add_col2:
        st.markdown("<div style='height:28px'></div>",unsafe_allow_html=True)
        if st.button("➕ Add to My Plants",type="primary",width="stretch",key="add_myplant_direct_v7"):
            if add_choice not in st.session_state.my_plants: st.session_state.my_plants.append(add_choice); st.success(f"{add_choice} added to My Plants.")
            else: st.info(f"{add_choice} is already in My Plants.")
            st.rerun()
    due_count=sum(1 for r in st.session_state.reminders if not r.get("done") and datetime.fromisoformat(r["when"])<=now)
    upcoming_count=sum(1 for r in st.session_state.reminders if not r.get("done") and datetime.fromisoformat(r["when"])>now)
    m1,m2,m3=st.columns(3)
    with m1: st.markdown(f'<div class="pc-stat"><div class="pc-stat-num">{len(st.session_state.my_plants)}</div><div class="pc-stat-label">Saved plants</div></div>',unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="pc-stat"><div class="pc-stat-num">{upcoming_count}</div><div class="pc-stat-label">Upcoming reminders</div></div>',unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="pc-stat"><div class="pc-stat-num">{due_count}</div><div class="pc-stat-label">Due now</div></div>',unsafe_allow_html=True)
    if st.session_state.reminders:
        st.markdown('<div class="pc-title">⏰ Care reminders</div>',unsafe_allow_html=True)
        for r in list(st.session_state.reminders):
            when=datetime.fromisoformat(r["when"]); due=(not r.get("done")) and when<=now; status="Completed" if r.get("done") else ("Due now" if due else "Upcoming")
            st.markdown(f'<div class="pc-reminder"><div class="pc-reminder-title">{r["task"]} • {r["plant"]}</div><div class="pc-reminder-meta">{when.strftime("%d %b %Y, %I:%M %p")} • {r["repeat"]} • {status}</div></div>',unsafe_allow_html=True)
            b1,b2=st.columns(2)
            with b1:
                if not r.get("done") and st.button("✓ Mark done",key="done_"+r["id"],width="stretch"):
                    if r["repeat"]!="One-time":
                        delta={"Daily":timedelta(days=1),"Weekly":timedelta(days=7),"Every 30 days":timedelta(days=30)}[r["repeat"]]; nxt=when+delta
                        while nxt<=now: nxt+=delta
                        r["when"]=nxt.isoformat(timespec="minutes")
                    else: r["done"]=True
                    st.rerun()
            with b2:
                if st.button("Delete",key="del_"+r["id"],width="stretch"): st.session_state.reminders=[x for x in st.session_state.reminders if x["id"]!=r["id"]]; st.rerun()
    if not st.session_state.my_plants:
        st.info("No plants saved yet. Use the Add a plant box above to get started.")
    else:
        st.markdown('<div class="pc-title">🌱 Your plants</div>',unsafe_allow_html=True)
        for name in list(st.session_state.my_plants):
            p=PLANT_BY_NAME[name]
            with st.expander(f"🌿 {p['common_name']} — {p['scientific_name']}",expanded=False):
                show_profile(p)
                st.markdown("### ⏰ Add a care reminder")
                with st.form(f"reminder_form_{p['common_name']}_v7",clear_on_submit=True):
                    r1,r2=st.columns(2)
                    with r1:
                        task=st.selectbox("Task",["Watering","Fertilizer","Pesticide","Weedicide","Sunlight / move plant to light","Rotate plant","Check soil moisture","Pest inspection","Misting / humidity","Pruning","Repotting","Custom"],key=f"task_{p['common_name']}_v7")
                        reminder_date=st.date_input("Date",value=date.today(),key=f"date_{p['common_name']}_v7")
                    with r2:
                        st.markdown("**Time (12-hour clock)**")
                        th,tm,tp=st.columns([1,1,1])
                        with th:
                            reminder_hour=st.selectbox("Hour",list(range(1,13)),index=7,key=f"time_hour_{p['common_name']}_v8")
                        with tm:
                            reminder_minute=st.selectbox("Minute",list(range(60)),index=0,format_func=lambda x:f"{x:02d}",key=f"time_minute_{p['common_name']}_v8")
                        with tp:
                            reminder_period=st.selectbox("AM / PM",["AM","PM"],index=0,key=f"time_period_{p['common_name']}_v8")
                        reminder_time=time_from_12h(reminder_hour,reminder_minute,reminder_period)
                        repeat=st.selectbox("Repeat",["One-time","Daily","Weekly","Every 30 days"],key=f"repeat_{p['common_name']}_v8")
                    custom=st.text_input("Custom task / note",placeholder="e.g. Check for aphids",key=f"custom_{p['common_name']}_v7")
                    notes=st.text_input("Notes (optional)",placeholder="e.g. Move near a bright window",key=f"notes_{p['common_name']}_v7")
                    if st.form_submit_button("➕ Add reminder",type="primary",width="stretch"):
                        final_task=custom.strip() if task=="Custom" and custom.strip() else task; when=datetime.combine(reminder_date,reminder_time)
                        if when<now: st.warning("Choose a future date/time for a new reminder.")
                        else:
                            st.session_state.reminders.append({"id":str(uuid.uuid4()),"plant":p["common_name"],"task":final_task,"when":when.isoformat(timespec="minutes"),"repeat":repeat,"notes":notes.strip(),"done":False}); st.success("Reminder added."); st.rerun()

elif page=="Plant Health Copilot":
    st.markdown(
        '<div class="pc-hero" style="padding:27px 30px">'
        '<h1 style="font-size:2.35rem">🩺 Plant Health Copilot</h1>'
        '<p>Describe what you observe and check growing conditions. Get a transparent checklist of possible causes and safe next steps—not an unsupported disease diagnosis.</p>'
        '<div class="pc-pills"><span class="pc-pill">Evidence-first</span><span class="pc-pill">No paid AI API required</span><span class="pc-pill">Honest uncertainty</span></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="pc-info"><b>How it works:</b> This version uses a transparent rule-based checklist. It cannot confirm pathogens, measure soil moisture, or replace an experienced horticulturist. The selected plant profile supplies general care context.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("### 💬 Ask PlantCare Copilot")
    st.caption("Local knowledge-base chat: answers are retrieved from the 56 plant profiles and simple safety rules. No paid AI API is used; this is not a general-purpose language model.")
    if "copilot_chat_messages" not in st.session_state:
        st.session_state.copilot_chat_messages = []
    for chat_message in st.session_state.copilot_chat_messages[-12:]:
        with st.chat_message(chat_message["role"]):
            st.markdown(chat_message["content"])
    user_question = st.chat_input("Ask about watering, light, soil, pests, or a supported plant…", key="copilot_chat_input")
    if user_question:
        st.session_state.copilot_chat_messages.append({"role": "user", "content": user_question})
        answer = answer_copilot_question(user_question, PLANTS)
        st.session_state.copilot_chat_messages.append({"role": "assistant", "content": answer})
        st.rerun()
    chat_col1, chat_col2 = st.columns([1, 5])
    with chat_col1:
        if st.button("Clear chat", key="clear_copilot_chat"):
            st.session_state.copilot_chat_messages = []
            st.rerun()
    st.markdown("---")
    st.markdown("### 🧾 Guided symptom assessment")
    with st.form("health_copilot_form_v1"):
        plant_name = st.selectbox("Which plant are you checking?", [p["common_name"] for p in PLANTS], key="copilot_plant_v1")
        symptoms = st.multiselect(
            "What have you observed? (Select all that apply)",
            [
                "Yellowing leaves", "Brown or crispy edges", "Wilting",
                "Spots or powder on leaves", "Sticky residue or webbing",
                "Slow or stunted growth", "Soft or foul-smelling soil",
                "Holes or chewed leaves", "Curled or distorted new leaves",
                "Leaf drop", "Leggy growth", "Mold on soil surface",
                "Black or soft stem tissue",
            ],
            key="copilot_symptoms_v2",
        )
        col1, col2 = st.columns(2)
        with col1:
            soil_state = st.selectbox("Soil moisture (check physically)", ["Not checked", "Dry", "Moist", "Wet / soggy"], key="copilot_soil_v2")
            watering_frequency = st.selectbox("How often do you water?", ["Not sure", "Daily", "Every 2–3 days", "About weekly", "Less than weekly", "Only when soil feels dry"], key="copilot_frequency_v2")
            drainage_state = st.selectbox("Water drainage", ["Not sure", "Good", "Poor"], key="copilot_drainage_v2")
            pot_drainage = st.selectbox("Does the pot have drainage holes?", ["Not sure", "Yes", "No drainage holes"], key="copilot_potdrain_v2")
        with col2:
            light_state = st.selectbox("Current light", ["Not sure", "Low light", "Bright indirect light", "Strong direct sun"], key="copilot_light_v2")
            plant_location = st.selectbox("Where is the plant?", ["Not sure", "Indoors", "Outdoors", "Balcony / windowsill", "Greenhouse"], key="copilot_location_v2")
            symptom_location = st.selectbox("Where do symptoms appear first?", ["Not sure", "Mostly older/lower leaves", "Mostly new/upper growth", "Across the whole plant", "One branch or one side"], key="copilot_symptom_location_v2")
            symptom_duration = st.selectbox("How quickly did it develop?", ["Not sure", "Gradually over weeks", "Over 1–2 weeks", "Spreading quickly (1–3 days)"], key="copilot_duration_v2")
        recent_change = st.selectbox("Recent change", ["None known", "Moved location", "Changed watering", "Repotted", "Added fertilizer", "Pesticide / cleaning spray exposure", "Weather / temperature changed", "New plant nearby"], key="copilot_change_v2")
        pest_seen = st.selectbox("Have you physically seen pests?", ["Not checked", "No visible pests", "Yes, visible"], key="copilot_pests_v2")
        notes = st.text_area("Extra observations (optional)", placeholder="Describe which leaves are affected, spots or insects you can see, smell, recent watering, and whether symptoms are spreading…", max_chars=1000, key="copilot_notes_v2")
        symptom_photo = st.file_uploader("Optional close-up symptom photo", type=["jpg", "jpeg", "png", "webp"], key="copilot_photo_v2")
        submitted = st.form_submit_button("Build my care action plan", type="primary", use_container_width=True)
    if submitted:
        plant = PLANT_BY_NAME[plant_name]
        assessment = assess_plant_health(
            plant,
            symptoms,
            soil_state=soil_state,
            light_state=light_state,
            drainage_state=drainage_state,
            recent_change=recent_change,
            notes=notes,
            watering_frequency=watering_frequency,
            pot_drainage=pot_drainage,
            symptom_location=symptom_location,
            symptom_duration=symptom_duration,
            plant_location=plant_location,
            pest_seen=pest_seen,
        )
        if symptom_photo is not None:
            try:
                photo_image = ImageOps.exif_transpose(Image.open(io.BytesIO(symptom_photo.getvalue()))).convert("RGB")
                visual_screen = visual_health_screen(photo_image)
                assessment["photo_screen"] = visual_screen
            except Exception:
                assessment["photo_screen"] = {"status": "Photo could not be analysed", "level": "Not available"}
        assessment["created_at"] = india_now_naive().isoformat(timespec="minutes")
        st.session_state.health_copilot_assessment = assessment
        st.session_state.plant_journal.append({
            "created_at": assessment["created_at"],
            "plant": plant_name,
            "entry_type": "Health check",
            "summary": ", ".join(symptoms) if symptoms else "General care check",
            "notes": notes.strip()[:500],
        })
    assessment = st.session_state.get("health_copilot_assessment")
    if assessment:
        st.markdown("### Assessment summary")
        if assessment.get("priority") == "Prompt inspection recommended":
            st.warning("**Priority:** Prompt inspection recommended. Review the first action in the plan today; this is not a confirmed diagnosis.")
        else:
            st.info("**Priority:** Routine observation and care checks. Reassess if symptoms worsen or spread.")
        st.markdown(
            f'<div class="pc-result"><div class="pc-result-name" style="font-size:1.45rem">{assessment["plant"]}</div>'
            f'<div class="pc-scientific"><i>{assessment["scientific_name"]}</i></div>'
            f'<div class="pc-badge">{assessment["assessment_type"]}</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown("#### Possible causes to investigate")
        for idx, cause in enumerate(assessment["possible_causes"], start=1):
            with st.expander(f"{idx}. {cause['possible_cause']}", expanded=(idx == 1)):
                st.write("**Why consider it:**", cause["why_consider_it"])
                st.write("**Safe check:**", cause["safe_check"])
        st.markdown("#### Practical next-step plan")
        for action in assessment["action_plan"]:
            st.markdown(f"- {action}")
        if assessment.get("photo_screen"):
            photo_screen = assessment["photo_screen"]
            st.markdown("#### Optional photo screen")
            st.info(f"Visual screen: {photo_screen.get('level', 'Not available')} — {photo_screen.get('status', 'No visual result available')}. This is a visual flag only, not a disease diagnosis.")
        with st.expander("Review the observations used"):
            st.json(assessment.get("observations", {}))
        st.markdown("#### What to do next")
        st.write("1. Do the physical checks above before adding fertilizer or pesticide.")
        st.write("2. Change one growing condition at a time where possible, so you can tell what helped.")
        st.write("3. Photograph the same area again in 3–7 days and compare whether symptoms are spreading.")
        if assessment.get("notes"):
            st.markdown("**Your notes:**")
            st.write(assessment["notes"])
        st.warning(assessment["disclaimer"])
        plant = PLANT_BY_NAME.get(assessment["plant"])
        if plant:
            with st.expander("View this plant's reference care profile"):
                st.write("**Water:**", plant.get("water", "See plant profile."))
                st.write("**Light:**", plant.get("light", "See plant profile."))
                st.write("**Soil:**", plant.get("soil", "See plant profile."))
                st.write("**Common problems to monitor:**", plant.get("pests", "See plant profile."), plant.get("diseases", "See plant profile."))
    st.markdown("### 🗒️ Plant journal")
    st.caption("Journal entries are stored only in this browser session in the current version. They are not guaranteed to survive a refresh, new session, or deployment restart.")
    journal = st.session_state.get("plant_journal", [])
    if journal:
        for entry in reversed(journal[-10:]):
            with st.expander(f"{entry['created_at']} · {entry['plant']} · {entry['entry_type']}"):
                st.write("**Observation:**", entry["summary"])
                if entry.get("notes"):
                    st.write("**Notes:**", entry["notes"])
        if st.button("Clear session journal", key="clear_copilot_journal_v1"):
            st.session_state.plant_journal = []
            st.rerun()
    else:
        st.info("No journal entries yet. Complete an assessment to create the first entry.")

elif page=="About":
    st.markdown('<div class="pc-reference-banner"><div class="pc-ref-logo"><svg viewBox="0 0 64 64" width="64" height="64" role="img" aria-label="PlantCare AI logo"><circle cx="32" cy="32" r="29" fill="#f8ffe8" stroke="#9bce57" stroke-width="3"/><path d="M17 42 C16 24 29 14 47 13 C47 30 38 44 22 46 Z" fill="#168348"/><path d="M19 49 C26 37 33 29 43 20" fill="none" stroke="#eaf8bd" stroke-width="3" stroke-linecap="round"/><path d="M30 36 C28 29 25 25 20 23 C19 31 23 36 30 36 Z" fill="#9bd65d"/></svg></div><div><h2>🌿 About PlantCare AI</h2><p>Bringing nature and technology together for a greener world.</p></div></div>',unsafe_allow_html=True)
    about_left,about_right=st.columns([1,1.25],gap="large")
    with about_left:
        st.markdown('<div class="pc-card" style="text-align:center"><div style="display:flex;justify-content:center"><svg viewBox="0 0 64 64" width="64" height="64" role="img" aria-label="PlantCare AI logo"><circle cx="32" cy="32" r="29" fill="#f8ffe8" stroke="#9bce57" stroke-width="3"/><path d="M17 42 C16 24 29 14 47 13 C47 30 38 44 22 46 Z" fill="#168348"/><path d="M19 49 C26 37 33 29 43 20" fill="none" stroke="#eaf8bd" stroke-width="3" stroke-linecap="round"/><path d="M30 36 C28 29 25 25 20 23 C19 31 23 36 30 36 Z" fill="#9bd65d"/></svg></div><h2 style="color:#075b35;margin:10px 0 2px">PlantCare AI</h2><p>Healthy Plants · 🌿 Greener Tomorrow</p><p><b>“A small step towards plant care, makes a big difference for our planet.”</b></p></div>',unsafe_allow_html=True)
        st.markdown('<div class="pc-card"><h3>🌱 Made by Aradhy Mundhe</h3><p>Student project · Identify · Learn · Care</p></div>',unsafe_allow_html=True)
    with about_right:
        st.markdown('<div class="pc-card"><h3>Project Information</h3><p><b>Project Name:</b> PlantCare AI<br><b>Developed by:</b> Aradhy Mundhe<br><b>Technologies:</b> Python, Streamlit, PyTorch, OpenCLIP, BioCLIP<br><b>Total Plant Species:</b> 56<br><b>Deployment:</b> Streamlit Community Cloud<br><b>Live Website:</b> <a href="https://plantcareai-kznq8jblfdsk3u5jvsw9rt.streamlit.app" target="_blank">Open PlantCare AI</a></p></div>',unsafe_allow_html=True)
        st.markdown('<div class="pc-card" style="display:flex;align-items:center;gap:22px;flex-wrap:wrap"><img class="pc-about-qr" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAZoAAAGaAQAAAAAefbjOAAAC/klEQVR4nO2cQW7jMAxFP0cCsrSBHKBHka/WI+UG9lFygAHkZQEZfxYUHbuzSlvYqU0vhLj2QySEIPlJqUI8fQ1/nmcAhxxyyCGHHHLomJDUK0K6UUSkBUTaSUTaSYDRXuh2mZ5D20OJJJkBoCn6J/J+IXmPABBIklxD203Poe2hsToA9mMEmScx2wiUDoCIxP2m59BmUPx0L0AowNhC0PyNBABi3Gt6Du0OsW8+BBomMiAd6vDj3+TQa0MNyR4A0j0CQwsd+N7WF0iW/abn0GZQjRqDAAACJN1CkZSvkHS/UFK+AsAk+0zPoc0htYhlKbspmjhweLNP6xdefk0OfQeCqsqUAfaoA1IOagPsGxIpB7JvSlWp/YuvyaHvQNVHDG0oSJwiqtYAkG4tBM0UiXESYnT1eQZIfQSZAfYI1ByT6hSonkH9BtxHnAKqUUO1hg2Y1SeSDTV+uEUcHao+oqYLs8sgLXHIK6OhW8TRIfu5AajMmH/9lTEUrUe4RRwfwsIf6K3JDL1SDpZluI84BbRSn5oplKo+VXPCZClzcIs4AbSIC5jzSVUY2hxHoIqQ5BZxCmhOJau0RGJZOwVzGXCtcQpIq06CJhODhPLpsQCBwDgJ0i0Wbj09h/aCkm6RqY1wrUIMb6U+GNpAe7rL9BzaQX0Gq0vZLXtY4ZIWSTxqnArSnGEQ21WX+CHSYRIRucxGs9v0HNoGmrvhkyDdWiDlq26tEzSZok/HKyRx8qhxAmhRoap9DcBUR8YsMwoeFU2PGoeGrEJlIlOzB64kqL5YtalbxMGhZWvr0cNYFLXnQoV3us4EPc50YVYdSCyQbowAxlj74vtMz6E9ogapEaK2tmzoAfMR9sl9xKGhRadr2dqyRHPxona/3CKODv13pisREOBiTuF2LQCmuDzY9eJrcujHodVZnkk0j8Bjx+VvXJNDT0JWiuC7iHY4RN6Kqk/psD7v90vW5NBXoNWuOlMY1RUgzHuxl10PzyMODYn/ZzKHHHLIIYcccuiL0D8b8JWmdpC6LAAAAABJRU5ErkJggg==" alt="QR code to open PlantCare AI"><div><h3>📱 Scan to open PlantCare AI</h3><p>Open your phone camera and point it at the QR code.</p><p><a href="https://plantcareai-kznq8jblfdsk3u5jvsw9rt.streamlit.app" target="_blank">plantcareai-kznq8jblfdsk3u5jvsw9rt.streamlit.app</a></p></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="pc-card"><h3>PlantCare AI — Made by Aradhy Mundhe</h3><p>This project was created by <b>Aradhy Mundhe</b> as a student project for plant identification, plant education and practical plant care.</p></div><div class="pc-card"><h3>What changed in this updated version?</h3><p>• Added memory-conscious plant screening and biological vision checks before species matching.<br>• Kept the offline-safe local visual screening so a model-loading problem does not crash the app.<br>• Reworked the sidebar into clear, large navigation buttons.<br>• Converted the interface to a consistent white-and-green theme.<br>• Added multi-view camera/gallery analysis, visual health screening, care requirements and clearer uncertainty messages.<br>• Added a repeatable real-photo benchmark for the 56 supported classes and automated code/data regression checks. A preliminary original-BioCLIP run ranked 49 real photos across 49 classes at 89.8% top-1 and 95.9% top-3; seven classes had no downloadable test photo, so this is not a 56-class certification. Diagnostic prompts were strengthened for ZZ Plant, Aglaonema, Mango and Prayer Plant.</p></div>',unsafe_allow_html=True)
    st.markdown('<div class="pc-title">Sharing</div>',unsafe_allow_html=True)
    st.markdown('<div class="pc-info"><b>For your teacher:</b> the easiest experience is a public hosted URL. A <code>localhost</code> address only works on the computer running PlantCare AI. The included launcher is for local use; online sharing requires deployment to a web host.</div>',unsafe_allow_html=True)

st.markdown('<div class="pc-footer">PlantCare AI • Made by Aradhy Mundhe • Identify • Learn • Care</div>',unsafe_allow_html=True)
