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
    """Load one shared BioCLIP model for the whole Streamlit process.

    Community Cloud has limited memory, so every identification component must
    reuse the same model instead of constructing separate model copies.
    """
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
def bioclip_text_features():
    """Build an ensemble of BioCLIP text embeddings for every library plant.

    BioCLIP is documented to support zero-shot classification through OpenCLIP
    text/image embeddings.  We use several short botanical prompts per plant
    (common name, scientific name, and a visual description when available)
    and average the normalized prompt embeddings.  This is substantially more
    stable than relying on a single wording, while keeping the classifier
    deterministic and free of API keys.
    """
    device, model, _, tokenizer = load_bioclip()
    import torch

    prompt_rows = []
    for p in PLANTS:
        common = str(p.get("common_name", "")).strip()
        scientific = str(p.get("scientific_name", "")).strip()
        hint = str(MODEL_HINTS.get(common, "")).strip()
        prompts = [
            f"a photograph of {scientific}",
            f"a photograph of the plant {common}",
        ]
        if hint:
            prompts.append(f"a botanical photograph of {common}, showing {hint}")
        else:
            prompts.append(f"a botanical photograph of {common}")
        prompt_rows.append(prompts)

    # Encode in small batches so the 56-plant library remains memory-friendly.
    plant_vectors = []
    with torch.no_grad():
        for prompts in prompt_rows:
            tokens = tokenizer(prompts).to(device)
            features = model.encode_text(tokens)
            features = features / features.norm(dim=-1, keepdim=True)
            feature = features.mean(dim=0, keepdim=True)
            feature = feature / feature.norm(dim=-1, keepdim=True)
            plant_vectors.append(feature)
        text_features = torch.cat(plant_vectors, dim=0)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
    return device, model, text_features


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


def bioclip_gate(img: Image.Image):
    """Use BioCLIP to screen plant vs obvious non-plant images across views."""
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
    """Use original, center, upper and vegetation-focused views for camera/gallery parity."""
    im=ImageOps.exif_transpose(img).convert("RGB")
    # Standardize orientation/size before either camera or gallery reaches the model.
    im.thumbnail((1600,1600),Image.Resampling.LANCZOS)
    views=[im]
    w,h=im.size
    side=int(min(w,h)*.78)
    if side>=160:
        left=max(0,(w-side)//2); top=max(0,(h-side)//2)
        views.append(im.crop((left,top,left+side,top+side)))
    if h>220:
        views.append(im.crop((0,0,w,int(h*.82))))
    focus=_focus_crop(im)
    if focus is not None:
        views.append(focus)
        fw,fh=focus.size
        side2=int(min(fw,fh)*.90)
        if side2>=160:
            views.append(focus.crop(((fw-side2)//2,(fh-side2)//2,(fw+side2)//2,(fh+side2)//2)))
    return views[:5]


def bioclip_rank(img: Image.Image, filename_hint: str = ""):
    """Rank species using BioCLIP across multiple crops; filename_hint is never used for classification."""
    device, model, preprocess = load_bioclip()[:3]
    _, _, text_features = bioclip_text_features()
    import torch
    image_features=[]
    with torch.no_grad():
        for view in _analysis_views(img):
            x=preprocess(view).unsqueeze(0).to(device)
            f=model.encode_image(x); f=f/f.norm(dim=-1,keepdim=True)
            image_features.append(f)
        image_features=torch.cat(image_features,dim=0)
        # Mean plus a small max-view contribution: this helps a leaf-rich crop matter
        # when the original camera frame contains lots of background.
        mean_feat=image_features.mean(dim=0,keepdim=True)
        mean_feat=mean_feat/mean_feat.norm(dim=-1,keepdim=True)
        mean_logits=(100.0*mean_feat@text_features.T).squeeze(0)
        probs=torch.softmax(mean_logits,dim=0).cpu().numpy()

    order=np.argsort(-probs); candidate_idx=order[:8]
    rows=[]
    for i in candidate_idx:
        p=PLANTS[i]
        text_score=float(probs[i])
        # Keep the species matcher deterministic and memory-friendly on Cloud:
        # reference images remain available in the UI, but are not downloaded and
        # encoded during every identification request.
        rows.append((p,text_score))
    rows.sort(key=lambda x:x[1],reverse=True)
    return [(p,float(score)) for p,score in rows]


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
    """Conservative plant/object gate with a single shared BioCLIP model.

    The local screen is deliberately only a fallback. If BioCLIP is available,
    its plant-vs-object margin is the primary decision signal.
    """
    local_is_plant, local_score, local_reason, local_features=plant_gate(img)
    try:
        clip_is_plant, plant_score, margin, meta=bioclip_gate(img)
        object_score=float(meta["object_score"])
        if object_score >= 32.0 and margin <= -6.0:
            return False, max(0.0,min(1.0,object_score/100.0)), "The photo appears to show an object rather than a plant", {"gate":"bioclip_object","margin":margin}
        if clip_is_plant or margin > -6.0:
            gate_score=max(0.0,min(1.0,0.5+margin/20.0))
            return True, gate_score, "Image passed the plant screening step", {"gate":"bioclip_ensemble","margin":margin}
        # For borderline BioCLIP results, require strong local foliage evidence.
        if local_is_plant and local_features.get("leafy_green_ratio",0)>=.10 and local_features.get("edge",0)>=.10:
            return True,local_score,"Plant-like foliage detected",{"gate":"strong_local_foliage","margin":margin}
        return False,max(0.0,min(1.0,0.5+margin/20.0)),"The photo does not contain enough reliable plant evidence",{"gate":"conservative_reject","margin":margin}
    except Exception:
        # If the model cannot load, use a strict local fallback rather than
        # returning a random plant class.
        strong_local=(local_features.get("leafy_green_ratio",0)>=.12 and local_features.get("edge",0)>=.09) or (local_features.get("green_ratio",0)>=.18 and local_features.get("edge",0)>=.11)
        return strong_local,local_score,("Plant-like foliage detected" if strong_local else "The photo does not contain enough reliable plant evidence"),{"gate":"local_strict_fallback"}


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
    """Conservative offline shortlist. Never invent a species from color alone.

    Without the vision model there is not enough evidence for reliable species
    identification from pixels alone, so this fallback only returns candidates
    when the user supplied explicit botanical clues.
    """
    f=rgb_features(img)
    rows=[]
    for p in PLANTS:
        text=" ".join(str(p.get(k,"")) for k in ["common_name","category","identification","leaf","flower","growth","similar"]).lower()
        score=0.0
        for c in clues:
            if c in text:
                score += .16
        cat=str(p.get("category"," ")).lower()
        # Image colors provide only weak category evidence; they can never
        # create a species match by themselves.
        if "flower" in cat and (f["red_ratio"]+f["yellow_ratio"])>.035: score+=.02
        if "succulent" in cat and f["sat"]>.32: score+=.015
        if "fruit" in cat and f["yellow_ratio"]>.03: score+=.01
        if "herb" in cat and f["green_ratio"]>.20: score+=.01
        if score>0: rows.append((p,float(score)))
    rows.sort(key=lambda x:x[1],reverse=True)
    if not clues:
        return []
    # Require at least one meaningful clue match. Ties remain a shortlist, not
    # a claimed identification.
    return [r for r in rows[:6] if r[1]>=.16]


def visual_health_screen(img: Image.Image) -> dict:
    """Screen visible foliage for stress cues. This is not a disease diagnosis."""
    focus=_focus_crop(img) or ImageOps.exif_transpose(img).convert("RGB")
    small=focus.copy(); small.thumbnail((500,500))
    a=np.asarray(small,dtype=np.float32)/255.0
    r,g,b=a[...,0],a[...,1],a[...,2]
    mx=a.max(axis=2); mn=a.min(axis=2); sat=np.divide(mx-mn,mx,out=np.zeros_like(mx),where=mx>1e-6)
    green=(g>r*.94)&(g>b*1.04)&(g>.14)&(sat>.10)
    yellow=(r>.38)&(g>.32)&(b<.40)&(r>b*1.10)&(sat>.16)
    brown=(r>.20)&(g>.10)&(g<r*.78)&(b<g*.95)&(sat>.16)
    dark=(mx<.18)&(sat>.05)
    foliage=green|yellow|brown
    area=max(float(foliage.mean()),.001)
    yellow_f=float((yellow&foliage).mean()/area)
    brown_f=float((brown&foliage).mean()/area)
    dark_f=float((dark&foliage).mean()/area)
    green_f=float((green&foliage).mean()/area)
    if brown_f>=.16 or dark_f>=.12:
        status="Possible visible leaf damage / stress signs"; level="Review closely"
    elif yellow_f>=.20:
        status="Possible yellowing / stress signs"; level="Monitor"
    else:
        status="No obvious visual stress signs detected"; level="Looks generally healthy in this photo"
    return {"status":status,"level":level,"green":green_f,"yellow":yellow_f,"brown":brown_f,"dark":dark_f,"focus_used":focus is not img}


def health_issue_text(p: dict, health: dict) -> str:
    if "damage" in health["status"].lower():
        return "Inspect the leaves for spots, rot, pests or physical damage. The plant profile lists these diseases/pests to watch for: " + str(p.get("diseases","Check the plant profile for common diseases."))
    if "yellowing" in health["status"].lower():
        return "Check soil moisture, drainage, light and pests before changing the watering routine. Yellowing has several possible causes."
    return "No obvious stress pattern was detected in this photo; continue normal monitoring and use the species care profile below."


def care_assessment(img: Image.Image, p: dict, health: dict) -> dict:
    """Turn visible image evidence + the species profile into safe care guidance.

    A single photograph cannot directly measure soil moisture, fertilizer levels,
    growth rate, sunlight exposure or the presence of a specific pathogen. This
    function therefore separates what the camera can screen from what the owner
    must physically check, instead of presenting guesses as measurements.
    """
    y=float(health.get("yellow",0)); b=float(health.get("brown",0)); d=float(health.get("dark",0)); g=float(health.get("green",0))
    stress = y >= .20 or b >= .16 or d >= .12
    if b >= .16 or d >= .12:
        visual_water = "Possible stress visible"
        visual_water_detail = "Brown/dark foliage is visible. Check the soil with a finger or moisture meter and inspect drainage before watering."
    elif y >= .20:
        visual_water = "Check watering"
        visual_water_detail = "Yellowing is visible. Check soil moisture and drainage; yellowing alone cannot prove overwatering or underwatering."
    else:
        visual_water = "No obvious water-stress pattern"
        visual_water_detail = "The photo does not show a strong visible stress pattern. Soil moisture still needs a physical check."

    nutrient = "No fertilizer diagnosis from photo"
    nutrient_detail = "Fertilizer need cannot be measured from a photograph. Use the species fertilizer guidance and avoid adding fertilizer solely because a leaf looks yellow."
    if y >= .20:
        nutrient_detail += " Yellowing can have many causes, including light, watering, roots, age or nutrients."

    disease = "No specific disease confirmed"
    disease_detail = "The image can screen for visible damage, but it cannot confirm a disease or pathogen. For suspected disease, inspect the affected leaf closely and compare symptoms with the plant profile."
    if b >= .16 or d >= .12:
        disease = "Visible damage/stress — inspect closely"
        disease_detail = "Visible brown/dark areas deserve a close-up inspection for leaf spots, rot, pests or physical injury. Do not treat based on color alone."

    pest = "No obvious pest conclusion"
    pest_detail = "Pests are not reliably confirmed from this photo. Inspect leaf undersides, stems and new growth for insects, webbing, scale or sticky residue before considering treatment."
    if stress:
        pest_detail += " Stress symptoms can overlap with pest and disease symptoms."

    sunlight = str(p.get("light", "Use the plant profile for its light requirement."))
    growth = "Growth rate cannot be measured from one photo"
    growth_detail = "Take repeat photos from a similar distance and angle to track new leaves, height and overall growth over time."

    return {
        "water_status": visual_water, "water_detail": visual_water_detail,
        "fertilizer_status": nutrient, "fertilizer_detail": nutrient_detail,
        "disease_status": disease, "disease_detail": disease_detail,
        "pest_status": pest, "pest_detail": pest_detail,
        "sunlight_status": "Species light requirement", "sunlight_detail": sunlight,
        "growth_status": growth, "growth_detail": growth_detail,
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
        camera=st.camera_input("Camera", label_visibility="collapsed", resolution="720p", key="camera_input_v10")
        if camera is not None:
            st.session_state.selected_image_bytes = camera.getvalue()
            st.session_state.selected_image_source = "Camera"
            st.session_state.selected_image_name = "camera_photo"
            st.session_state.analysis = None
    with t2:
        st.markdown('<div class="pc-upload-card"><div class="pc-upload-title">🖼️ Choose from gallery</div><div class="pc-upload-sub">JPG, JPEG, PNG or WEBP • Use a clear photo.</div></div>',unsafe_allow_html=True)
        uploaded=st.file_uploader("Gallery",type=["jpg","jpeg","png","webp"],label_visibility="collapsed", key="gallery_input_v10")
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

            st.markdown('<div class="pc-analyze-box"><div><b>Ready to identify this photo?</b><br><span>The app compares the photo with the plant library using BioCLIP first, then rejects it only when there is strong evidence that it is a non-plant object. If BioCLIP is unavailable, the app uses a local fallback. The filename is never used to choose the plant.</span></div></div>',unsafe_allow_html=True)
            analyze=st.button("🔎  ANALYZE IMAGE",type="primary",use_container_width=True,key="analyze_v10")
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
                if mindim<140 or bright<10 or bright>252 or sharp<4:
                    st.session_state.analysis=None
                    st.markdown('<div class="pc-warning"><b>🟡 Photo quality is too low.</b><br>Use daylight and move closer so leaves, flowers or the whole plant are clearly visible.</div>',unsafe_allow_html=True)
                else:
                    with st.spinner("Analyzing plant photo… first run may take longer while the vision model loads."):
                        clues=clue_tokens(leaf_shape,leaf_texture,flowers,growth,thorns)
                        # IMPORTANT: identify first, then use the plant/object model only
                        # as a strong rejection check. The previous V12 version ran a
                        # conservative gate first; that gate could reject genuine plants
                        # (especially flowers, mango/tulsi and warm-lit photos) before
                        # BioCLIP ever got a chance to identify them.
                        ai_rows, model_used, model_error = optional_vision_rank(image, st.session_state.get("selected_image_name", ""))
                        if model_used and ai_rows:
                            rows=ai_rows
                            # Keep the non-plant protection, but reject only when the
                            # object evidence is decisively stronger than plant evidence.
                            # BioCLIP scores are similarities, not calibrated probabilities.
                            reject_object=False
                            object_reason=""
                            try:
                                _, _, obj_plant_score, obj_margin, obj_meta = _strong_object_screen(image)
                                if obj_meta.get("object_score",0.0) >= 32.0 and obj_margin <= -6.0:
                                    reject_object=True
                                    object_reason="The photo is much more consistent with a non-plant object than with plant imagery."
                            except Exception:
                                # Never turn a model-screening failure into a false
                                # NO PLANT result. The species model already succeeded.
                                pass

                            if reject_object:
                                st.session_state.analysis={"nonplant":True,"reason":object_reason,"score":0.0}
                            else:
                                if clues:
                                    adjusted=[]
                                    for p,s in rows:
                                        txt=" ".join(str(p.get(k,"")) for k in ["common_name","category","identification","leaf","flower","growth","similar"]).lower()
                                        bonus=sum(.01 for c in clues if c in txt)
                                        adjusted.append((p,min(1.0,s+bonus)))
                                    rows=sorted(adjusted,key=lambda x:x[1],reverse=True)
                                label,conf=confidence_label(rows)
                                model_note="BioCLIP biology vision model"
                                health=visual_health_screen(image)
                                care=care_assessment(image, rows[0][0], health)
                                st.session_state.analysis={"rows":rows,"label":label,"conf":conf,"score":1.0,"model_note":model_note,"model_error":model_error,"health":health,"care":care,"species_unavailable":False}
                        else:
                            # BioCLIP could not run. Use the local visual screen only
                            # as a plant-presence fallback; do not claim a species unless
                            # the user supplied meaningful botanical clues.
                            local_is_plant,local_score,local_reason,local_features=plant_gate(image)
                            if not local_is_plant:
                                st.session_state.analysis={"nonplant":True,"reason":local_reason,"score":local_score}
                            else:
                                rows=identify_locally(image,clues)[:4]
                                label="Needs confirmation"
                                conf=50
                                model_note="Offline shortlist — BioCLIP unavailable"
                                health=visual_health_screen(image)
                                care=care_assessment(image, rows[0][0], health) if rows else None
                                st.session_state.analysis={"rows":rows,"label":label,"conf":conf,"score":local_score,"model_note":model_note,"model_error":model_error,"health":health,"care":care,"species_unavailable":(not rows)}
        except Exception as exc:
            st.session_state.analysis=None
            st.error(f"The selected image could not be read: {type(exc).__name__}. Please choose another JPG or PNG image.")
    else:
        st.markdown('<div class="pc-card"><h3>📌 Start here</h3><p>Choose <b>Camera</b> to take a photo or <b>Gallery</b> to upload one. After the image appears, the green <b>ANALYZE IMAGE</b> button will always be available.</p></div>',unsafe_allow_html=True)

    result=st.session_state.analysis
    if result and result.get("nonplant"):
        st.markdown(f'<div class="pc-error"><b>🚫 NO PLANT DETECTED</b><br>{result["reason"]}. Try a photo where the plant fills more of the frame.</div>',unsafe_allow_html=True)
    elif result and result.get("species_unavailable"):
        st.markdown('<div class="pc-warning"><b>🌱 Plant detected, but species identification is temporarily unavailable.</b><br>No plant name was guessed. Check the internet connection and press <b>ANALYZE IMAGE</b> again, or add the optional leaf/flower clues to get a conservative shortlist.</div>',unsafe_allow_html=True)
        health=result.get("health")
        if health:
            st.markdown("### 🩺 Visual health screening")
            st.markdown(f'<div class="pc-result"><div class="pc-result-name" style="font-size:1.35rem">{health["level"]}</div><div class="pc-scientific">{health["status"]}</div></div>',unsafe_allow_html=True)
            st.caption("Health screening is visual only and does not identify a disease.")
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
        alt_map=get_plant_photos_for_records(tuple((x[0]['common_name'], x[0]['scientific_name']) for x in alt)) if alt else {}
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
            hc1,hc2,hc3,hc4=st.columns(4)
            with hc1: st.metric("Green foliage",f'{health["green"]*100:.0f}%')
            with hc2: st.metric("Yellowing",f'{health["yellow"]*100:.0f}%')
            with hc3: st.metric("Brown/damaged",f'{health["brown"]*100:.0f}%')
            with hc4: st.metric("Dark areas",f'{health["dark"]*100:.0f}%')
            st.markdown(f'<div class="pc-warning"><b>Important:</b> {health_issue_text(top,health)}<br><small>This is a visual screening only, not a definitive disease diagnosis. A clear close-up of affected leaves is needed for more reliable assessment.</small></div>',unsafe_allow_html=True)
        st.markdown("### 🩺 PlantCare check")
        care=result.get("care") or care_assessment(image, top, health or visual_health_screen(image))
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
    st.markdown('<div class="pc-hero" style="padding:27px 30px"><h1 style="font-size:2.35rem">🌿 Plant Library</h1><p>Browse all plants with reference images and complete care profiles.</p></div>',unsafe_allow_html=True)
    query=st.text_input("Search the plant library",placeholder="Type mango, tulsi, rose…",key="library_search_v7")
    q=query.strip().lower()
    items=[p for p in PLANTS if not q or q in (p["common_name"]+" "+p["scientific_name"]+" "+p["category"]).lower()]
    photo_map=get_plant_photos_for_records(tuple((x['common_name'], x['scientific_name']) for x in items)) if items else {}
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
    st.markdown('<div class="pc-card"><h3>PlantCare AI — Made by Aradhy Mundhe</h3><p>This project was created by <b>Aradhy Mundhe</b> as a student project for plant identification, plant education and practical plant care.</p></div><div class="pc-card"><h3>What changed in this updated version?</h3><p>• Added Multi-view BioCLIP species matching with camera/gallery normalization and conservative object rejection.<br>• Kept the offline-safe local visual screening so a model-loading problem does not crash the app.<br>• Reworked the sidebar into clear, large navigation buttons.<br>• Converted the interface to a consistent white-and-green theme.<br>• Added multi-view camera/gallery analysis, visual health screening, care requirements and clearer uncertainty messages.<br>• No OpenAI key, Gemini key or paid API is required.</p></div>',unsafe_allow_html=True)
    st.markdown('<div class="pc-title">Sharing</div>',unsafe_allow_html=True)
    st.markdown('<div class="pc-info"><b>For your teacher:</b> the easiest experience is a public hosted URL. A <code>localhost</code> address only works on the computer running PlantCare AI. The included launcher is for local use; online sharing requires deployment to a web host.</div>',unsafe_allow_html=True)

st.markdown('<div class="pc-footer">PlantCare AI • Made by Aradhy Mundhe • Identify • Learn • Care</div>',unsafe_allow_html=True)
