from __future__ import annotations

import json
import io
import math
import re
import os
from pathlib import Path
from datetime import datetime, date, time, timedelta
import uuid
from typing import Dict, List, Tuple

import numpy as np
import requests
import streamlit as st
from PIL import Image, ImageOps, ImageFilter, ImageDraw


APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "plant_data.json"

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
    :root{--g:#138a4b;--gd:#0b6b39;--gm:#eaf8ef;--ink:#173225;--muted:#64766b;--line:#d8e9dd;--bg:#f7fbf8;--white:#fff}
    .stApp{background:linear-gradient(180deg,#f7fbf8 0,#fff 40%);color:var(--ink)}
    [data-testid="stHeader"]{background:rgba(255,255,255,.94)}
    [data-testid="stSidebar"]{background:linear-gradient(180deg,#effaf3 0,#f8fcf9 100%);border-right:1px solid var(--line)}
    [data-testid="stSidebar"] *{color:var(--ink)}
    .pc-brand{display:flex;align-items:center;gap:12px;padding:6px 4px 22px}
    .pc-logo{width:52px;height:52px;border-radius:17px;background:linear-gradient(135deg,#17a65a,#0a6a39);display:flex;align-items:center;justify-content:center;font-size:27px;box-shadow:0 10px 22px rgba(10,106,57,.18)}
    .pc-brand-title{font-size:1.2rem;font-weight:900;line-height:1.05}.pc-brand-sub{font-size:.78rem;color:var(--muted);margin-top:5px}
    .pc-nav-title{font-size:.73rem;font-weight:800;letter-spacing:.08em;color:#6a7d71;text-transform:uppercase;margin:4px 0 8px}
    .pc-hero{color:#fff;border-radius:28px;padding:34px 36px;margin-bottom:22px;background:radial-gradient(circle at 92% 10%,rgba(255,255,255,.35),transparent 25%),linear-gradient(135deg,#0b6a38,#15914f 55%,#62bf7e);box-shadow:0 18px 45px rgba(20,120,64,.16)}
    .pc-hero h1{margin:0;color:#fff;font-size:clamp(2rem,4vw,3.25rem);line-height:1;letter-spacing:-.035em}.pc-hero p{margin:13px 0 0;color:rgba(255,255,255,.94);max-width:800px;line-height:1.55;font-size:1.02rem}
    .pc-pills{display:flex;flex-wrap:wrap;gap:9px;margin-top:18px}.pc-pill{border:1px solid rgba(255,255,255,.25);background:rgba(255,255,255,.15);border-radius:999px;padding:7px 11px;color:#fff;font-size:.82rem;font-weight:800}
    .pc-card{background:#fff;border:1px solid var(--line);border-radius:22px;padding:21px;box-shadow:0 10px 28px rgba(22,55,35,.055);height:100%}.pc-card h3{margin:0 0 8px;color:var(--ink);font-size:1.05rem}.pc-card p{margin:0;color:var(--muted);line-height:1.55;font-size:.92rem}
    .pc-stat{background:#fff;border:1px solid var(--line);border-radius:18px;padding:18px 20px;box-shadow:0 8px 22px rgba(22,55,35,.05)}.pc-stat-num{font-size:1.6rem;font-weight:900;color:var(--gd)}.pc-stat-label{font-size:.78rem;color:var(--muted);margin-top:5px}
    .pc-title{font-size:1.45rem;font-weight:900;color:var(--ink);margin:28px 0 12px}.pc-result{background:linear-gradient(180deg,#f5fcf7,#fff);border:1px solid #c9e5d1;border-radius:24px;padding:23px;box-shadow:0 10px 28px rgba(22,55,35,.06)}.pc-result-name{font-size:clamp(1.7rem,3vw,2.35rem);font-weight:950;color:var(--gd);margin:0}.pc-scientific{color:var(--muted);font-size:.93rem;margin-top:5px}.pc-badge{display:inline-block;background:var(--gm);color:#116335;border:1px solid #cde8d4;border-radius:999px;padding:6px 10px;font-size:.82rem;font-weight:850;margin-top:10px}
    .pc-info{background:#f5fbf7;border:1px solid var(--line);border-radius:16px;padding:14px 16px;line-height:1.5}.pc-warning{background:#fff8e8;border:1px solid #f0dd9b;color:#6e5513;border-radius:16px;padding:14px 16px}.pc-error{background:#fff1f1;border:1px solid #f1c5c5;color:#8a2020;border-radius:16px;padding:14px 16px}
    .pc-footer{text-align:center;color:#7b8c82;font-size:.78rem;padding:35px 0 15px}
    .stButton>button{border-radius:13px!important;min-height:44px!important;border:1px solid #cfe2d5!important;font-weight:800!important;background:#fff!important;color:#173225!important}
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
    [data-testid="stTabs"] button[aria-selected="true"]{color:#0b6b39!important;border-bottom-color:#138a4b!important}
    div[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:14px}

    .pc-upload-card{background:#fff;border:1px solid #cfe2d5;border-radius:16px;padding:14px 16px;margin-bottom:8px}.pc-upload-title{font-weight:900;color:#0b6b39}.pc-upload-sub{font-size:.82rem;color:#64766b;margin-top:3px}.pc-selected-label{background:#eaf8ef;color:#116335;border:1px solid #cde8d4;border-radius:12px;padding:9px 12px;font-weight:800;margin:12px 0}.pc-analyze-box{background:#f3fbf6;border:1px solid #cce5d3;border-radius:16px;padding:14px 16px;margin:12px 0}.pc-analyze-box span{color:#64766b;font-size:.84rem}.pc-photo-placeholder{height:230px;border-radius:18px;background:#eff9f2;border:1px dashed #b7d4bf;display:flex;align-items:center;justify-content:center;text-align:center;flex-direction:column;color:#0b6b39;font-size:1.15rem}.pc-photo-placeholder span{color:#64766b;font-size:.8rem;margin-top:4px}
    @media(max-width:900px){.pc-hero{padding:25px 22px}.pc-hero h1{font-size:2.2rem}}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Data
# -----------------------------------------------------------------------------
@st.cache_data

def load_plants() -> List[dict]:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

PLANTS = load_plants()
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

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Optional real vision model: BioCLIP.
# BioCLIP is a biology-focused zero-shot image classifier.  It is loaded lazily
# so the app can still start when the model cannot be downloaded.  The offline
# matcher remains as a fallback, but BioCLIP is preferred for species matching.
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_bioclip():
    """Load BioCLIP lazily. The model is never downloaded just to open the app."""
    import torch
    import open_clip
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, _, preprocess = open_clip.create_model_and_transforms(
        "hf-hub:imageomics/bioclip"
    )
    tokenizer = open_clip.get_tokenizer("hf-hub:imageomics/bioclip")
    model = model.to(device).eval()
    return device, model, preprocess, tokenizer


MODEL_HINTS = {
    "Tulsi": "holy basil, tulasi, aromatic herb, opposite oval serrated leaves, purple or green stems, small flower spikes",
    "Mint": "mint herb, opposite serrated oval leaves, aromatic leafy herb, spreading stems",
    "Mango": "mango tree, Mangifera indica, long narrow lanceolate leaves, woody tree, mango fruit",
    "Marigold": "marigold, Tagetes erecta, yellow or orange round flower heads, pinnate foliage",
    "Rose": "rose, Rosa, woody shrub with serrated oval leaflets and distinctive rose flowers",
    "Hibiscus": "hibiscus, large five-petaled flowers, prominent central staminal column, serrated leaves",
    "Jasmine": "jasmine, Jasminum, small glossy opposite leaves and fragrant white flowers",
    "Aloe Vera": "aloe vera, thick fleshy pointed succulent leaves arranged in a rosette",
    "Snake Plant": "snake plant, Dracaena trifasciata, upright sword-shaped leaves with banded markings",
    "Money Plant": "money plant, pothos, Epipremnum aureum, heart-shaped leaves on a trailing vine",
    "Spider Plant": "spider plant, Chlorophytum comosum, long narrow arching leaves and plantlets",
    "Peace Lily": "peace lily, Spathiphyllum, broad leaves and white spathe flowers",
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
    "Spinach": "spinach, Spinacia oleracea, soft broad green edible leaves",
    "Cucumber": "cucumber, Cucumis sativus, rough lobed leaves and climbing vine with elongated fruits",
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
}

@st.cache_resource(show_spinner=False)
def load_generic_clip_gate():
    """Optional generic CLIP gate for plant-vs-object screening."""
    import torch
    import open_clip
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    model = model.to(device).eval()
    prompts = [
        "a clear photograph of a plant", "a clear photograph of a tree", "a clear photograph of leaves",
        "a clear photograph of a flower", "a clear photograph of a car or vehicle",
        "a clear photograph of a person", "a clear photograph of an animal",
        "a clear photograph of food", "a clear photograph of a building or furniture",
        "a clear photograph of an electronic device or household object",
    ]
    with torch.no_grad():
        t = model.encode_text(tokenizer(prompts).to(device))
        t = t / t.norm(dim=-1, keepdim=True)
    return device, model, preprocess, t


def generic_clip_gate(img: Image.Image):
    """Return plant decision, score and margin using generic CLIP."""
    device, model, preprocess, text_features = load_generic_clip_gate()
    import torch
    with torch.no_grad():
        x=preprocess(ImageOps.exif_transpose(img).convert("RGB")).unsqueeze(0).to(device)
        f=model.encode_image(x); f=f/f.norm(dim=-1,keepdim=True)
        logits=(100.0*f@text_features.T).squeeze(0)
        probs=torch.softmax(logits,dim=0).cpu().numpy()
    plant_score=float(np.max(probs[:4]))
    object_score=float(np.max(probs[4:]))
    margin=plant_score-object_score
    # CLIP is used as a conservative rejector, not as proof that a plant is
    # absent. This prevents false "not a plant" results for real plants under
    # warm light, cluttered backgrounds, or unusual camera angles.
    clearly_nonplant = object_score >= 0.78 and margin <= -0.18
    return (not clearly_nonplant), plant_score, margin, probs


@st.cache_resource(show_spinner=False)
def bioclip_text_features():
    """Create richer species-specific text features for every library plant."""
    device, model, _, tokenizer = load_bioclip()
    import torch
    templates = [
        "a photograph of {}",
        "a clear photograph of {}",
        "a botanical photograph of {}",
        "a field photograph showing {}",
        "a close-up photograph of {}",
    ]
    features = []
    for p in PLANTS:
        cname=p["common_name"]
        sname=p["scientific_name"]
        hint=MODEL_HINTS.get(cname, "")
        details="; ".join([
            str(p.get("identification", "")),
            str(p.get("leaf", "")),
            str(p.get("flower", "")),
            str(p.get("growth", "")),
        ])
        descriptions=[
            f"{cname} ({sname})",
            f"{cname} ({sname}): {hint or details}",
        ]
        prompt_features=[]
        for desc in descriptions:
            texts=tokenizer([t.format(desc) for t in templates]).to(device)
            with torch.no_grad():
                tf=model.encode_text(texts)
                tf=tf/tf.norm(dim=-1,keepdim=True)
                tf=tf.mean(dim=0)
                tf=tf/tf.norm()
            prompt_features.append(tf)
        merged=torch.stack(prompt_features).mean(dim=0)
        merged=merged/merged.norm()
        features.append(merged)
    return device, model, torch.stack(features)


def _analysis_views(img: Image.Image) -> List[Image.Image]:
    """Create a small ensemble of views so background/pot color matters less."""
    im = ImageOps.exif_transpose(img).convert("RGB")
    w, h = im.size
    views = [im]
    # Center crop, preserving the plant when it is roughly centered.
    side = int(min(w, h) * 0.78)
    if side >= 160:
        left = max(0, (w-side)//2); top = max(0, (h-side)//2)
        views.append(im.crop((left, top, left+side, top+side)))
    # Upper/central crop helps when a potted plant has a large pot/floor area.
    if h > 220:
        top_h = int(h * 0.78)
        views.append(im.crop((0, 0, w, top_h)))
    return views


def bioclip_rank(img: Image.Image, filename_hint: str = ""):
    device, model, preprocess = load_bioclip()[:3]
    _, _, text_features = bioclip_text_features()
    import torch
    image_features = []
    with torch.no_grad():
        for view in _analysis_views(img):
            x = preprocess(view).unsqueeze(0).to(device)
            f = model.encode_image(x)
            f = f / f.norm(dim=-1, keepdim=True)
            image_features.append(f)
        image_features = torch.cat(image_features, dim=0).mean(dim=0, keepdim=True)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        logits = (100.0 * image_features @ text_features.T).squeeze(0)
        probs = torch.softmax(logits, dim=0).cpu().numpy()
    order = np.argsort(-probs)
    rows = [(PLANTS[i], float(probs[i])) for i in order]
    # Do not use the filename as an identification signal. A file named
    # "tulsi.jpg" can be renamed to anything, so the image itself must decide.
    return rows


def optional_vision_rank(img: Image.Image, filename_hint: str = ""):
    try:
        return bioclip_rank(img, filename_hint), True, ""
    except Exception as exc:
        return [], False, f"{type(exc).__name__}: {exc}"


def vision_gate(img: Image.Image):
    """Two-signal gate: never let a single CLIP mistake reject a plant photo."""
    local_is_plant, local_score, local_reason, local_features = plant_gate(img)
    try:
        clip_is_plant, clip_plant_score, margin, probs = generic_clip_gate(img)
        if clip_is_plant:
            return True, max(clip_plant_score, local_score), "Image passed the plant screening step", {"gate":"combined", "margin":margin}
        # If CLIP calls an image a non-plant but the independent local visual
        # screen sees clear plant-like evidence, keep the image. This specifically
        # prevents warm lighting, flowers, pots, or unusual framing from causing
        # false 'NO PLANT DETECTED' results. A car/random object without plant-like
        # cues is still rejected.
        if local_is_plant:
            return True, local_score, "Plant-like visual evidence detected; continuing to species analysis", {"gate":"local_override", "margin":margin}
        return False, clip_plant_score, "The image strongly appears to contain a non-plant object", {"gate":"combined", "margin":margin}
    except Exception:
        return local_is_plant, local_score, local_reason, {"gate":"local_fallback"}

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
    f=rgb_features(img)
    rows=[]
    for p in PLANTS:
        text=" ".join(str(p.get(k,"")) for k in ["common_name","category","identification","leaf","flower","growth","similar"]).lower()
        score=.02
        # Broad visual evidence from the image.
        cat=str(p.get("category","")).lower()
        if f["green_ratio"]>.22: score+=.10
        if "flower" in cat and (f["red_ratio"]+f["yellow_ratio"])>.035: score+=.035
        if "succulent" in cat and f["sat"]>.32: score+=.025
        if "fruit" in cat and f["yellow_ratio"]>.03: score+=.025
        if "herb" in cat and f["green_ratio"]>.20: score+=.025
        # Use user-supplied visual clues as a strong structured signal.
        for c in clues:
            if c in text: score+=.07
        # Do not guess a species from a single colour. Yellow/green pixels
        # are shared by many plants and caused the earlier Mango -> Marigold
        # failure. The offline matcher therefore remains conservative.
        if "cactus" in text and f["green_ratio"]>.10: score+=.01
        rows.append((p,float(score)))
    rows.sort(key=lambda x:x[1],reverse=True)
    return rows


def confidence_label(rows: List[Tuple[dict,float]]) -> Tuple[str,int]:
    if not rows:
        return "Needs confirmation", 0
    top = rows[0][1]
    second = rows[1][1] if len(rows) > 1 else 0.0
    margin = max(0.0, top - second)
    # These are UI confidence bands, not probabilities of correctness.
    if margin >= .10 and top >= .20:
        return "Strong candidate", min(90, max(70, int(70 + margin*120)))
    if margin >= .045 and top >= .12:
        return "Likely candidate", min(82, max(58, int(58 + margin*120)))
    return "Needs confirmation", 50

# -----------------------------------------------------------------------------
# UI helpers

# -----------------------------------------------------------------------------
NAV=[("🏠","Home"),("📷","Identify a Plant"),("🌿","Plant Library"),("🔎","Search"),("❤️","My Plants"),("ℹ️","About")]

with st.sidebar:
    st.markdown('<div class="pc-brand"><div class="pc-logo">🌿</div><div><div class="pc-brand-title">PlantCare AI</div><div class="pc-brand-sub">Identify • Learn • Care</div></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="pc-nav-title">Menu</div>',unsafe_allow_html=True)
    for icon,name in NAV:
        if st.button(f"{icon}  {name}",key=f"nav_{name}",use_container_width=True,type="primary" if st.session_state.page==name else "secondary"):
            st.session_state.page=name
            st.session_state.analysis=None
            st.rerun()
    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown(f'<div class="pc-card" style="padding:16px"><div style="font-size:.72rem;color:#64766b;font-weight:800">PLANT LIBRARY</div><div style="font-size:1.45rem;font-weight:900;color:#0b6b39">{len(PLANTS)} plants</div><div style="font-size:.76rem;color:#64766b;margin-top:5px">Offline-safe • No API key</div></div>',unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Plant reference images
# -----------------------------------------------------------------------------
@st.cache_data(ttl=86400, show_spinner=False)
def get_plant_photos(names: Tuple[str, ...]) -> Dict[str, str]:
    """Resolve reference thumbnails and preserve Wikipedia redirects."""
    result: Dict[str, str] = {}
    names = tuple(dict.fromkeys(str(n).strip() for n in names if str(n).strip()))
    if not names:
        return result
    session = requests.Session()
    session.headers.update({"User-Agent": "PlantCareAI/1.0 (student project)"})
    for start_i in range(0, len(names), 20):
        batch = list(names[start_i:start_i+20])
        try:
            r=session.get("https://en.wikipedia.org/w/api.php", params={
                "action":"query","format":"json","redirects":1,
                "prop":"pageimages","piprop":"thumbnail","pithumbsize":700,
                "titles":"|".join(batch)}, timeout=10)
            r.raise_for_status(); data=r.json().get("query", {})
            pages=data.get("pages", {})
            redirects={str(x.get("from","")).strip().lower():str(x.get("to","")).strip().lower() for x in data.get("redirects", []) if x.get("from") and x.get("to")}
            by_title={}
            for page in pages.values():
                title=str(page.get("title","")).strip().lower(); thumb=page.get("thumbnail",{}).get("source")
                if title and thumb: by_title[title]=thumb; result[title]=thumb
            for original,target in redirects.items():
                if target in by_title: result[original]=by_title[target]
        except Exception:
            pass
    missing=[n for n in names if n.lower() not in result]
    for n in missing:
        try:
            sr=session.get("https://en.wikipedia.org/w/api.php", params={"action":"query","format":"json","list":"search","srsearch":n,"srnamespace":0,"srlimit":3}, timeout=8)
            sr.raise_for_status()
            for hit in sr.json().get("query",{}).get("search",[]):
                title=hit.get("title")
                if not title: continue
                pr=session.get("https://en.wikipedia.org/w/api.php", params={"action":"query","format":"json","redirects":1,"prop":"pageimages","piprop":"thumbnail","pithumbsize":700,"titles":title}, timeout=8)
                pr.raise_for_status(); data=pr.json().get("query",{})
                redirects={str(x.get("from","")).strip().lower():str(x.get("to","")).strip().lower() for x in data.get("redirects",[]) if x.get("from") and x.get("to")}
                for page in data.get("pages",{}).values():
                    thumb=page.get("thumbnail",{}).get("source"); actual=str(page.get("title","")).strip().lower()
                    if thumb:
                        result[n.lower()]=thumb
                        if actual: result[actual]=thumb
                        for original,target in redirects.items():
                            if target==actual: result[original]=thumb
                        break
                if n.lower() in result: break
        except Exception:
            continue
    return result

@st.cache_data(ttl=86400, show_spinner=False)
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
        st.image(data,use_container_width=True,caption=f"Reference photo • {p['common_name']}")
    else:
        st.image(botanical_fallback(p),use_container_width=True,caption=f"Plant reference • {p['common_name']}")
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
if page=="Home":
    st.markdown('<div class="pc-hero"><h1>PlantCare AI</h1><p>Identify plants, learn their characteristics, and explore practical care information in a clean, simple interface.</p><div class="pc-author">🌿 Made by Aradhy Mundhe</div><div class="pc-pills"><span class="pc-pill">📷 Photo analysis</span><span class="pc-pill">🌱 Plant library</span><span class="pc-pill">🧠 BioCLIP vision</span><span class="pc-pill">⚡ No API key</span><span class="pc-pill">💻 Easy Windows setup</span></div></div>',unsafe_allow_html=True)
    cols=st.columns(4)
    for c,(v,l) in zip(cols,[(len(PLANTS),"Plants in library"),("📷","Photo identification"),("🌱","Plant care"),("⏰","Care reminders")]):
        with c: st.markdown(f'<div class="pc-stat"><div class="pc-stat-num">{v}</div><div class="pc-stat-label">{l}</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="pc-title">Explore PlantCare AI</div>',unsafe_allow_html=True)
    a,b,c=st.columns(3)
    for col,title,desc in [(a,"📷 Identify a Plant","Take a photo with the camera or upload one from your gallery to find a possible plant match."),(b,"📚 Learn & Explore","Browse plant photos, identification features, growing conditions, care, pests and safety information."),(c,"❤️ My Plants","Save plants and set reminders for watering, fertilizer, pesticide, weedicide and other care tasks.")]:
        with col: st.markdown(f'<div class="pc-card"><h3>{title}</h3><p>{desc}</p></div>',unsafe_allow_html=True)
    st.markdown('<div class="pc-title">How it works</div>',unsafe_allow_html=True)
    st.markdown('<div class="pc-info"><b>1.</b> Choose a photo &nbsp; → &nbsp; <b>2.</b> Analyze the image &nbsp; → &nbsp; <b>3.</b> Review the possible plant match &nbsp; → &nbsp; <b>4.</b> Explore its care profile or save it to My Plants.</div>',unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Identify
# -----------------------------------------------------------------------------
elif page=="Identify a Plant":
    st.markdown('<div class="pc-hero" style="padding:27px 30px"><h1 style="font-size:2.35rem">📷 Identify a Plant</h1><p>Take a photo or choose one from your gallery. Then press the green Analyze Image button. The analysis never depends on a paid API key.</p></div>',unsafe_allow_html=True)

    if "selected_image_bytes" not in st.session_state:
        st.session_state.selected_image_bytes = None
    if "selected_image_source" not in st.session_state:
        st.session_state.selected_image_source = None
    if "selected_image_name" not in st.session_state:
        st.session_state.selected_image_name = ""

    t1,t2=st.tabs(["📷 Camera","🖼️ Gallery"])
    with t1:
        st.markdown('<div class="pc-upload-card"><div class="pc-upload-title">📷 Take a plant photo</div><div class="pc-upload-sub">Allow camera access when Chrome asks.</div></div>',unsafe_allow_html=True)
        camera=st.camera_input("Camera", label_visibility="collapsed")
        if camera is not None:
            st.session_state.selected_image_bytes = camera.getvalue()
            st.session_state.selected_image_source = "Camera"
            st.session_state.selected_image_name = "camera_photo"
            st.session_state.analysis = None
    with t2:
        st.markdown('<div class="pc-upload-card"><div class="pc-upload-title">🖼️ Choose from gallery</div><div class="pc-upload-sub">JPG, JPEG, PNG or WEBP • Use a clear photo.</div></div>',unsafe_allow_html=True)
        uploaded=st.file_uploader("Gallery",type=["jpg","jpeg","png","webp"],label_visibility="collapsed")
        if uploaded is not None:
            st.session_state.selected_image_bytes = uploaded.getvalue()
            st.session_state.selected_image_source = "Gallery"
            st.session_state.selected_image_name = uploaded.name or "gallery_photo"
            st.session_state.analysis = None

    raw=st.session_state.selected_image_bytes
    if raw:
        try:
            image=ImageOps.exif_transpose(Image.open(__import__("io").BytesIO(raw))).convert("RGB")
            st.markdown(f'<div class="pc-selected-label">✓ {st.session_state.selected_image_source} photo selected</div>',unsafe_allow_html=True)
            st.image(image,caption="Selected image",use_container_width=True)

            with st.expander("Optional plant clues — improves matching when you know them", expanded=False):
                c1,c2,c3=st.columns(3)
                with c1: leaf_shape=st.selectbox("Leaf shape",["Not sure","Heart-shaped","Long/strap-like","Broad/oval","Needle-like","Lobed","Round","Feathery"],key="leaf_shape_v5")
                with c2: leaf_texture=st.selectbox("Leaf texture",["Not sure","Fleshy/thick","Glossy","Hairy/rough","Thin","Leathery"],key="leaf_texture_v5")
                with c3: flowers=st.selectbox("Flowers",["Not sure","None visible","White","Yellow","Pink/red","Purple/blue","Orange"],key="flowers_v5")
                c4,c5=st.columns(2)
                with c4: growth=st.selectbox("Growth habit",["Not sure","Upright","Trailing/vining","Clumping","Tree/shrub","Rosette"],key="growth_v5")
                with c5: thorns=st.selectbox("Thorns / spines",["Not sure","Present","Not visible"],key="thorns_v5")

            st.markdown('<div class="pc-analyze-box"><div><b>Ready to identify this photo?</b><br><span>The app first screens for a likely plant, then compares the photo with the plant library using a biology vision model. The filename is never used to choose the plant.</span></div></div>',unsafe_allow_html=True)
            analyze=st.button("🔎  ANALYZE IMAGE",type="primary",use_container_width=True,key="analyze_v5")
            cclear,_=st.columns([1,4])
            with cclear:
                if st.button("Clear photo",use_container_width=True,key="clear_v5"):
                    st.session_state.selected_image_bytes=None
                    st.session_state.selected_image_source=None
                    st.session_state.selected_image_name=""
                    st.session_state.analysis=None
                    st.rerun()

            if analyze:
                sharp,bright,mindim=image_quality(image)
                if mindim<180 or bright<15 or bright>250 or sharp<8:
                    st.session_state.analysis=None
                    st.markdown('<div class="pc-warning"><b>🟡 Photo quality is too low.</b><br>Use daylight and move closer so leaves, flowers or the whole plant are clearly visible.</div>',unsafe_allow_html=True)
                else:
                    with st.spinner("Analyzing plant photo… first run may take longer while the vision model loads."):
                        is_plant,score,reason,features=vision_gate(image)
                        if not is_plant:
                            st.session_state.analysis={"nonplant":True,"reason":reason,"score":score}
                        else:
                            clues=clue_tokens(leaf_shape,leaf_texture,flowers,growth,thorns)
                            ai_rows, model_used, model_error = optional_vision_rank(image, st.session_state.get("selected_image_name", ""))
                            if model_used and ai_rows:
                                rows=ai_rows
                                if clues:
                                    adjusted=[]
                                    for p,s in rows:
                                        txt=" ".join(str(p.get(k,"")) for k in ["common_name","category","identification","leaf","flower","growth","similar"]).lower()
                                        bonus=sum(.01 for c in clues if c in txt)
                                        adjusted.append((p,min(1.0,s+bonus)))
                                    rows=sorted(adjusted,key=lambda x:x[1],reverse=True)
                                label,conf=confidence_label(rows)
                                model_note="BioCLIP biology vision model"
                            else:
                                # Never hide a model failure. The local matcher is only a
                                # shortlist and must not be presented as reliable species AI.
                                rows=identify_locally(image,clues)
                                rows=rows[:4]
                                label="Needs confirmation"
                                conf=50
                                model_note="Offline shortlist — BioCLIP unavailable"
                            st.session_state.analysis={"rows":rows,"label":label,"conf":conf,"score":score,"model_note":model_note,"model_error":model_error}
        except Exception as exc:
            st.session_state.analysis=None
            st.error(f"The selected image could not be read: {type(exc).__name__}. Please choose another JPG or PNG image.")
    else:
        st.markdown('<div class="pc-card"><h3>📌 Start here</h3><p>Choose <b>Camera</b> to take a photo or <b>Gallery</b> to upload one. After the image appears, the green <b>ANALYZE IMAGE</b> button will always be available.</p></div>',unsafe_allow_html=True)

    result=st.session_state.analysis
    if result and result.get("nonplant"):
        st.markdown(f'<div class="pc-error"><b>🚫 NO PLANT DETECTED</b><br>{result["reason"]}. Try a photo where the plant fills more of the frame.</div>',unsafe_allow_html=True)
    elif result and result.get("rows"):
        top=result["rows"][0][0]
        st.success("🌱 PLANT PHOTO ACCEPTED")
        st.caption(f"Analysis engine: {result.get('model_note','')}")
        if result.get("model_error"):
            st.warning("The main vision model could not be loaded, so this result is only a local shortlist. Check the internet connection and try Analyze again.")
        st.markdown(f'<div class="pc-result"><div style="font-size:.78rem;font-weight:900;color:#64766b;text-transform:uppercase;letter-spacing:.08em">TOP PLANT MATCH</div><div class="pc-result-name">🌿 {top["common_name"]}</div><div class="pc-scientific"><b>Common name:</b> {top["common_name"]} &nbsp; · &nbsp; <i>{top["scientific_name"]}</i> · {top["family"]}</div><div class="pc-badge">{result["label"]} · {result["conf"]}% visual-match score</div></div>',unsafe_allow_html=True)
        if result["label"] in ["Possible match","Needs confirmation"]:
            st.markdown('<div class="pc-warning"><b>Confirm before relying on the name:</b> visually similar plants can look alike. Use the alternatives and the reference photo below.</div>',unsafe_allow_html=True)
        st.markdown("### 🌿 Other possible matches")
        alt=result["rows"][1:4]
        alt_map=get_plant_photos(tuple([x[0]["scientific_name"] for x in alt] + [x[0]["common_name"] for x in alt])) if alt else {}
        for p,s in alt:
            col1,col2=st.columns([1,2])
            with col1:
                plant_photo(p, photo_map=alt_map)
            with col2:
                st.markdown(f'<div class="pc-card"><h3>{p["common_name"]}</h3><p><i>{p["scientific_name"]}</i><br>Visual score: {s:.3f}</p></div>',unsafe_allow_html=True)
        st.markdown("### 🌱 Plant profile")
        show_profile(top)


elif page=="Plant Library":
    st.markdown('<div class="pc-hero" style="padding:27px 30px"><h1 style="font-size:2.35rem">🌿 Plant Library</h1><p>Browse all plants with reference images and complete care profiles.</p></div>',unsafe_allow_html=True)
    query=st.text_input("Search the plant library",placeholder="Type mango, tulsi, rose…",key="library_search_v7")
    q=query.strip().lower()
    items=[p for p in PLANTS if not q or q in (p["common_name"]+" "+p["scientific_name"]+" "+p["category"]).lower()]
    photo_map=get_plant_photos(tuple([x["scientific_name"] for x in items]+[x["common_name"] for x in items])) if items else {}
    cols=st.columns(3)
    for i,p in enumerate(items):
        with cols[i%3]:
            plant_photo(p,photo_map=photo_map)
            st.markdown(f'<div class="pc-card" style="margin-bottom:12px"><h3>🌿 {p["common_name"]}</h3><p><i>{p["scientific_name"]}</i><br>{p["category"]}</p></div>',unsafe_allow_html=True)
            if st.button("Open profile",key="lib_"+p["common_name"],use_container_width=True):
                st.session_state.selected_plant=p["common_name"]; st.session_state.search_q=""; st.session_state.page="Search"; st.rerun()

elif page=="Search":
    st.markdown('<div class="pc-hero" style="padding:27px 30px"><h1 style="font-size:2.35rem">🔎 Search Plants</h1><p>Start typing and choose a suggested plant, or search by common name, scientific name or category.</p></div>',unsafe_allow_html=True)
    if "search_q" not in st.session_state: st.session_state.search_q=""
    q=st.text_input("Search plants",value=st.session_state.search_q,placeholder="Type mango, tulsi, rose…",key="search_box_v7")
    st.session_state.search_q=q; ql=q.strip().lower()
    if ql:
        suggestions=[p for p in PLANTS if ql in (p["common_name"]+" "+p["scientific_name"]+" "+p["category"]).lower()][:8]
        if suggestions:
            st.markdown("**Suggestions**")
            scols=st.columns(2)
            for i,p in enumerate(suggestions):
                with scols[i%2]:
                    if st.button(f"🌿 {p['common_name']} · {p['scientific_name']}",key="suggest_"+p["common_name"],use_container_width=True):
                        st.session_state.search_q=p["common_name"]; st.session_state.selected_plant=p["common_name"]; st.rerun()
        else:
            st.info("No plant suggestion yet. Try another spelling or search by scientific name.")
    selected=st.session_state.get("selected_plant")
    if selected and (not ql or selected.lower()==ql):
        p=PLANT_BY_NAME.get(selected)
        st.session_state.pop("selected_plant",None)
        if p: show_profile(p)
    elif ql:
        matches=[p for p in PLANTS if ql in (p["common_name"]+" "+p["scientific_name"]+" "+p["category"]).lower()]
        if len(matches)==1: show_profile(matches[0])
        elif len(matches)>1:
            st.markdown("### Matching plants")
            for p in matches:
                if st.button(f"🌿 {p['common_name']} — {p['scientific_name']}",key="match_"+p["common_name"],use_container_width=True):
                    st.session_state.selected_plant=p["common_name"]; st.rerun()

elif page=="My Plants":
    st.markdown('<div class="pc-hero" style="padding:27px 30px"><h1 style="font-size:2.35rem">❤️ My Plants</h1><p>Add your plants directly and create reminders for watering, fertilizer, sunlight, pest checks and other care tasks.</p></div>',unsafe_allow_html=True)
    now=datetime.now()
    st.markdown("### ➕ Add a plant to My Plants")
    add_col1,add_col2=st.columns([2,1])
    with add_col1:
        add_choice=st.selectbox("Choose a plant",[p["common_name"] for p in PLANTS],key="myplant_add_choice_v7")
    with add_col2:
        st.markdown("<div style='height:28px'></div>",unsafe_allow_html=True)
        if st.button("➕ Add to My Plants",type="primary",use_container_width=True,key="add_myplant_direct_v7"):
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
                if not r.get("done") and st.button("✓ Mark done",key="done_"+r["id"],use_container_width=True):
                    if r["repeat"]!="One-time":
                        delta={"Daily":timedelta(days=1),"Weekly":timedelta(days=7),"Every 30 days":timedelta(days=30)}[r["repeat"]]; nxt=when+delta
                        while nxt<=now: nxt+=delta
                        r["when"]=nxt.isoformat(timespec="minutes")
                    else: r["done"]=True
                    st.rerun()
            with b2:
                if st.button("Delete",key="del_"+r["id"],use_container_width=True): st.session_state.reminders=[x for x in st.session_state.reminders if x["id"]!=r["id"]]; st.rerun()
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
                        reminder_time=st.time_input("Time",value=time(8,0),key=f"time_{p['common_name']}_v7")
                        repeat=st.selectbox("Repeat",["One-time","Daily","Weekly","Every 30 days"],key=f"repeat_{p['common_name']}_v7")
                    custom=st.text_input("Custom task / note",placeholder="e.g. Check for aphids",key=f"custom_{p['common_name']}_v7")
                    notes=st.text_input("Notes (optional)",placeholder="e.g. Move near a bright window",key=f"notes_{p['common_name']}_v7")
                    if st.form_submit_button("➕ Add reminder",type="primary",use_container_width=True):
                        final_task=custom.strip() if task=="Custom" and custom.strip() else task; when=datetime.combine(reminder_date,reminder_time)
                        if when<now: st.warning("Choose a future date/time for a new reminder.")
                        else:
                            st.session_state.reminders.append({"id":str(uuid.uuid4()),"plant":p["common_name"],"task":final_task,"when":when.isoformat(timespec="minutes"),"repeat":repeat,"notes":notes.strip(),"done":False}); st.success("Reminder added."); st.rerun()

elif page=="About":
    st.markdown('<div class="pc-hero" style="padding:27px 30px"><h1 style="font-size:2.35rem">ℹ️ About PlantCare AI</h1><p>A student project focused on plant identification, plant education and practical care information.</p></div>',unsafe_allow_html=True)
    st.markdown('<div class="pc-card"><h3>PlantCare AI — Made by Aradhy Mundhe</h3><p>This project was created by <b>Aradhy Mundhe</b> as a student project for plant identification, plant education and practical plant care.</p></div><div class="pc-card"><h3>What changed in this updated version?</h3><p>• Added BioCLIP-based species matching with an automatic offline fallback.<br>• Kept the offline-safe local visual screening so a model-loading problem does not crash the app.<br>• Reworked the sidebar into clear, large navigation buttons.<br>• Converted the interface to a consistent white-and-green theme.<br>• Added clearer error messages, photo-quality checks and alternative matches.<br>• No OpenAI key, Gemini key or paid API is required.</p></div>',unsafe_allow_html=True)
    st.markdown('<div class="pc-title">Sharing</div>',unsafe_allow_html=True)
    st.markdown('<div class="pc-info"><b>For your teacher:</b> the easiest experience is a public hosted URL. A <code>localhost</code> address only works on the computer running PlantCare AI. The included launcher is for local use; online sharing requires deployment to a web host.</div>',unsafe_allow_html=True)

st.markdown('<div class="pc-footer">PlantCare AI • Made by Aradhy Mundhe • Identify • Learn • Care</div>',unsafe_allow_html=True)
