import streamlit as st
import json, time, hashlib
from pathlib import Path

st.set_page_config(page_title="MISSION 100", page_icon="🎯", layout="wide")
st.markdown("""
<style>
.stApp{background:#f3f6fb;color:#13233f;font-size:18px}.block-container{max-width:1500px;padding-top:1.3rem;padding-bottom:3rem}
html,body,[class*="css"]{font-size:18px} p,li,label,.stMarkdown{font-size:18px;line-height:1.55} h1{font-size:2.45rem!important;font-weight:850!important} h2{font-size:1.85rem!important;font-weight:800!important} h3{font-size:1.4rem!important;font-weight:800!important} [data-testid="stSidebar"]{background:linear-gradient(180deg,#e6eef9 0%,#f5f8fd 100%);border-right:1px solid #cfdaeb;min-width:300px!important} [data-testid="stSidebar"] *{font-size:19px;font-weight:700} [data-testid="stSidebar"] [data-testid="stRadio"] label{padding:11px 13px!important;border:1px solid #d3deed;border-radius:10px!important;background:#fff;margin:5px 0;min-height:48px;box-shadow:0 2px 5px #152e4a0a} [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked){background:#174ea6!important;color:#fff!important;border-color:#174ea6;box-shadow:0 4px 12px #174ea633} [data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stWidgetLabel"]{font-size:18px!important;font-weight:850!important} [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"]>label>div:first-child{display:none!important}
.stTabs [data-baseweb="tab-list"]{gap:7px;background:#e8eef7;padding:8px;border-radius:14px;flex-wrap:wrap}
.stTabs [data-baseweb="tab"]{height:auto;border-radius:9px;padding:10px 13px;color:#314563;font-weight:650}
.stTabs [aria-selected="true"]{background:#174ea6!important;color:white!important}
div[data-testid="stMetric"]{background:white;border:1px solid #dce5f0;padding:16px;border-radius:15px;box-shadow:0 4px 14px #162f530a}
div[data-testid="stMetricValue"]{color:#122746;font-weight:800}
div[data-testid="stVerticalBlockBorderWrapper"]{border-color:#dce5f0;border-radius:15px;background:white}
.stButton>button,.stDownloadButton>button{border-radius:10px;font-weight:650;min-height:2.6rem}
.stButton>button[kind="primary"]{background:#1757b7;border-color:#1757b7}
.stProgress>div>div>div>div{background:#1757b7}
.mission-hero{background:linear-gradient(115deg,#102849,#173e73);padding:28px 30px;border-radius:18px;color:white;margin:8px 0 20px;box-shadow:0 10px 26px #10284924}
.mission-hero h2{color:white;font-size:1.9rem;margin:0 0 6px}.mission-hero p{color:#dce8fb;margin:0}.small-tagline{color:#a8c9ff!important;font-weight:750;letter-spacing:.08em}
@media(max-width:800px){.block-container{padding-left:1rem;padding-right:1rem}.stTabs [data-baseweb="tab"]{padding:8px}}
</style>
""",unsafe_allow_html=True)

def check_access():
    import base64, hmac
    from datetime import datetime, timedelta, timezone
    import extra_streamlit_components as stx

    cfg = st.secrets.get("access", {})
    expected = str(cfg.get("password", ""))
    allowed = list(cfg.get("device_keys", []))
    if not expected or not allowed:
        st.title("MISSION 100 — Private setup")
        st.error("Access protection is not configured. Add your password and approved device key in your hosting provider's Secrets settings before use.")
        st.info("For security, this screen never displays saved passwords or device keys. Keep both values private and never add them to GitHub.")
        st.stop()

    # A signed, expiring cookie remembers this browser after reloads.
    # The cookie contains no password or device key.
    signing_key = str(cfg.get("cookie_signing_key", expected + "|" + "|".join(str(k) for k in allowed))).encode()
    cookie_manager = stx.CookieManager(key="mission100_cookie_manager")
    cookie_name = "mission100_login"

    # CookieManager loads browser cookies asynchronously. Wait for its first
    # response before showing the login form, otherwise a valid cookie can
    # briefly look like a missing cookie on a page reload.
    browser_cookies = cookie_manager.get_all()
    if not isinstance(browser_cookies, dict):
        if not st.session_state.get("_mission100_cookie_ready_waited"):
            st.session_state["_mission100_cookie_ready_waited"] = True
            st.info("Restoring your remembered login…")
            time.sleep(1)
            st.rerun()
        browser_cookies = {}
    st.session_state.pop("_mission100_cookie_ready_waited", None)
    cookie_token = browser_cookies.get(cookie_name)
    if cookie_token is None:
        cookie_token = cookie_manager.get(cookie=cookie_name)
    # An empty dictionary can also mean the browser component has not finished
    # reading cookies yet. Give it one additional render before showing login.
    if not cookie_token and not st.session_state.get("_mission100_cookie_missing_waited"):
        st.session_state["_mission100_cookie_missing_waited"] = True
        st.info("Checking this browser for your saved login…")
        time.sleep(1)
        st.rerun()
    st.session_state.pop("_mission100_cookie_missing_waited", None)

    def make_token(device_fingerprint, expires):
        payload = f"{device_fingerprint}:{expires}"
        signature = hmac.new(signing_key, payload.encode(), hashlib.sha256).hexdigest()
        return base64.urlsafe_b64encode(f"{payload}:{signature}".encode()).decode()

    def verify_token(token):
        try:
            decoded = base64.urlsafe_b64decode(token.encode()).decode()
            fingerprint, expires_text, signature = decoded.rsplit(":", 2)
            payload = f"{fingerprint}:{expires_text}"
            expected_sig = hmac.new(signing_key, payload.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected_sig):
                return None
            if int(expires_text) <= int(time.time()):
                return None
            if not any(hashlib.sha256(str(k).encode()).hexdigest() == fingerprint for k in allowed):
                return None
            return fingerprint
        except Exception:
            return None

    if not st.session_state.get("authenticated"):
        fingerprint = verify_token(cookie_token) if cookie_token else None
        if fingerprint:
            st.session_state.authenticated = True
            st.session_state.device_fingerprint = fingerprint
        else:
            st.title("🎯 MISSION 100")
            st.subheader("Private Study Command Centre")
            with st.form("login"):
                password = st.text_input("Private password", type="password")
                device_key = st.text_input("Approved device key", type="password")
                remember = st.checkbox("Remember this browser for 14 days", value=True)
                submitted = st.form_submit_button("Unlock Mission 100", type="primary")
            if submitted:
                okp = hmac.compare_digest(hashlib.sha256(password.encode()).digest(), hashlib.sha256(expected.encode()).digest())
                okd = any(hmac.compare_digest(hashlib.sha256(device_key.encode()).digest(), hashlib.sha256(str(k).encode()).digest()) for k in allowed)
                if okp and okd:
                    fingerprint = hashlib.sha256(device_key.encode()).hexdigest()
                    st.session_state.authenticated = True
                    st.session_state.device_fingerprint = fingerprint
                    if remember:
                        expires = int((datetime.now(timezone.utc) + timedelta(days=14)).timestamp())
                        cookie_manager.set(cookie=cookie_name, val=make_token(fingerprint, expires), expires_at=datetime.now(timezone.utc) + timedelta(days=14), key="mission100_set_login_cookie")
                        # Give the browser component time to persist the cookie before rerunning.
                        time.sleep(1)
                    st.rerun()
                else:
                    st.error("Access denied. Check the password and approved device key.")
            st.caption("Choose “Remember this browser” to stay signed in across reloads for up to 14 days. Locking the session clears the current session; use browser cookie settings to revoke a remembered login.")
            st.stop()

    fingerprint = st.session_state.get("device_fingerprint", "")
    if not any(hashlib.sha256(str(k).encode()).hexdigest() == fingerprint for k in allowed):
        st.session_state.clear()
        st.error("This device key is no longer approved. Sign in again.")
        st.stop()

check_access()
DATA_FILE = Path("mission100_progress.json")
def load_data():
    default = {"done": {}, "ap": {}, "cover": {}, "custom": [], "custom_ap": [], "goals": {}, "dreams": [], "mistakes": [], "discipline": {}, "xp": 0, "notes": "", "focus_sessions": 0, "study_minutes": 0}
    try:
        if DATA_FILE.exists(): default.update(json.loads(DATA_FILE.read_text(encoding="utf-8")))
    except Exception: pass
    return default
if "data" not in st.session_state: st.session_state.data = load_data()
d = st.session_state.data
def save():
    try: DATA_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception: pass
def mark_task(key, value):
    old = bool(d["done"].get(key, False)); d["done"][key] = value
    if old != value: d["xp"] = max(0, int(d.get("xp",0)) + (10 if value else -10))
    save()

tasks = [
("m1","Marathi","संतवाणी — अंकिला मी दास तुझा","Read, understand, recall meaning, practise written answers."),
("m2","Marathi","शाल","Recall the lesson and write answers without copying."),
("m3","Marathi","उपास","Understand key events and practise textbook questions."),
("m4","Marathi","मोठे होत असलेल्या मुलांनो","Recall central ideas; practise answers."),
("m5","Marathi","दोन दिवस","Review poem/theme and write answers."),
("m6","Marathi","चुडीवाला","Recall plot, characters and details."),
("m7","Marathi","फुटप्रिंट्स","Recall the lesson and practise answers."),
("m8","Marathi","ऊर्जा शक्तीचा जागर","Recall key ideas and answer independently."),
("m9","Marathi","Marathi full-syllabus self-test","Test all eight entries without the book; correct weak answers. Include grammar/writing only if prescribed."),
("a0","Maths","AP formulas + concept check","Identify first term, common difference, nth term and sum; solve examples yourself."),
("a1","Maths","AP NCERT exercise pass 1","Attempt every question independently; mark mistakes."),
("sst","SST","History — Nationalism in India","Read prescribed section, recall timeline and practise written answers."),
("sci","Science","Chemical Reactions and Equations","Balance equations and practise NCERT questions."),
("sleep","Routine","Set tomorrow’s first task and protect sleep","Prepare materials; put phone away before bedtime.")
]
apbase = [
("ap1","NCERT AP exercise set 1 · Pass 1","Every question; note errors and doubts."),
("ap2","NCERT AP exercise set 2 · Pass 1","Attempt independently and check working."),
("ap3","NCERT AP exercise set 3 · Pass 1","Complete all questions from your edition."),
("ap4","NCERT AP exercise set 4 · Pass 1","Only if present in your textbook edition."),
("ap5","Pass 2 · Redo all missed questions","No looking at old solutions."),
("ap6","Pass 2 · Repeat all exercise questions","Correct every error and record why."),
("ap7","Pass 3 · Timed mixed AP test","Simulate exam conditions and analyse mistakes."),
("ap8","Verified previous-paper/PYQ set 1","Record paper year and source."),
("ap9","Verified previous-paper/PYQ set 2","Different paper; analyse errors."),
("ap10","Verified PYQ sets 3–5","Finish across later sessions using real papers.")
]
exams = [("26 OCT","Monday","Hindi / Marathi / Sanskrit"),("27 OCT","Tuesday","SST"),("28 OCT","Wednesday","P. L."),("29 OCT","Thursday","Science"),("30 OCT","Friday","P. L."),("31 OCT","Saturday","Maths"),("01 NOV","Sunday","Holiday"),("02 NOV","Monday","English"),("03 NOV","Tuesday","A. I.")]
syllabus = {
"Maths":["Real Numbers","Arithmetic Progressions","Coordinate Geometry","Triangles","Introduction to Trigonometry","Some Applications of Trigonometry","Surface Areas and Volumes","Statistics"],
"Science":["Chemical Reactions and Equations","Acids, Bases and Salts","Life Processes","Control and Coordination","Light: Reflection and Refraction","Electricity"],
"SST":["History: Nationalism in India","History: Rise of Nationalism in Europe","History: Making of a Global World","Geography: Resources and Development","Geography: Forest and Wildlife Resources","Geography: Water Resources","Geography: Agriculture","Political Science: Power Sharing","Political Science: Federalism","Political Science: Gender, Religion and Caste","Economics: Development","Economics: Sectors of Indian Economy","Economics: Money and Credit","Economics: Globalisation"],
"English":["A Letter to God","Dust of Snow","Fire and Ice","Nelson Mandela","A Tiger in the Zoo","Two Stories about Flying","How to Tell Wild Animals","The Ball Poem","From the Diary of Anne Frank","Glimpses of India","Amanda!","Mijbil the Otter","Fog","Madam Rides the Bus","The Tale of Custard the Dragon","A Triumph of Surgery","The Thief’s Story","The Midnight Visitor","A Question of Trust","Footprints Without Feet","The Making of a Scientist","The Necklace","Tenses","Determiners","Modals","Subject-verb concord","Letter writing","Analytical paragraph"],
"Marathi":["संतवाणी — अंकिला मी दास तुझा","शाल","उपास","मोठे होत असलेल्या मुलांनो","दोन दिवस","चुडीवाला","फुटप्रिंट्स","ऊर्जा शक्तीचा जागर"],
"Hindi":["Exact Hindi chapters from school syllabus (source image text was too small to transcribe reliably)"],
"Sanskrit":["Exact Sanskrit पाठ from school syllabus (source image text was too small to transcribe reliably)"],
"AI":["Communication Skills","Self-Management Skills","Information and Communication Technology Skills","Entrepreneurship Skills","Green Skills","Natural Language Processing"]
}
goals = [
("G1","Score 100% in Class 10 board examinations","Chapter mastery, timed papers, error correction and spaced revision."),
("G2","Buy a Toyota Fortuner Legender","Long-term milestone after education and financial stability."),
("G3","Own a Porsche 911 GT3 RS","Aspirational goal; focus first on education and career foundations."),
("G4","Build one of India’s biggest fitness gym businesses","Learn coaching, business operations, customer safety and leadership."),
("G5","Become a leading fitness influencer in India","Create useful, honest fitness education and build communication skills."),
("G6","Earn a MuscleBlaze sponsorship","Build credibility, knowledge, consistency and an audience before pursuing partnerships.")
]
st.sidebar.title("MISSION 100")
st.sidebar.caption("Class X · Study Command Centre")
if st.sidebar.button("Lock this session"):
    st.session_state.clear(); st.rerun()
st.sidebar.markdown("**Rule:** study first, reward second.")
st.markdown('<div class="mission-hero"><p class="small-tagline">MISSION 100 · PERSONAL STUDY COMMAND CENTRE</p><h2>YOUR FUTURE IS BUILT TODAY.</h2><h2 style="color:#f4d58d">100% IS THE GOAL.</h2><p>Stay focused. Stay disciplined. Work hard. Make every day count.</p></div>', unsafe_allow_html=True)
st.subheader("Small focused blocks. Serious preparation.")
st.caption("Your goals are the destination. Today's honest work is the route. This dashboard supports preparation; it cannot guarantee 100% marks.")
total = len(tasks) + len(d.get("custom", []))
completed = sum(bool(d["done"].get(t[0])) for t in tasks) + sum(bool(d["done"].get(t["id"])) for t in d.get("custom", []))
total_chapters = sum(len(v) for v in syllabus.values())
covered = sum(bool(d["cover"].get(sub+"_"+str(i))) for sub, arr in syllabus.items() for i in range(len(arr)))
c1,c2,c3,c4 = st.columns(4)
c1.metric("Today's tasks",str(completed)+"/"+str(total)); c2.metric("XP earned",str(d.get("xp",0)))
c3.metric("Syllabus first-pass",str(round(covered*100/total_chapters))+"%"); c4.metric("Focus sessions logged",str(d.get("focus_sessions",0)))
pages = ["Today's Mission","AP Mastery","Syllabus","Life Goals","Focus Room","My Dreams","Mistake Book","Daily Discipline","Progress & Backup"]
page = st.sidebar.radio("NAVIGATION", pages, index=0, label_visibility="visible")
st.sidebar.markdown("---")
st.sidebar.markdown("### STAY FOCUSED.\n\n### WORK HARD.\n\n### 100% IS THE GOAL.")
if page == "Today's Mission":
    st.info("Priority from your HTML: Marathi CM preparation, Arithmetic Progressions, Nationalism in India, Chemical Reactions and Equations, and protected sleep. Adjust tasks to match your actual school timetable.")
    left,right = st.columns([1.2,0.8])
    with left:
        st.header("Today's task board")
        for key,subject,title,detail in tasks:
            v=st.checkbox(subject+" — "+title,value=bool(d["done"].get(key)),key="task_"+key,help=detail)
            if v != bool(d["done"].get(key)): mark_task(key,v)
            st.caption(detail)
        with st.form("custom_task_form"):
            st.subheader("Add a custom task")
            subj=st.selectbox("Subject",["Maths","Science","SST","English","Marathi","Hindi","Sanskrit","AI","Routine"])
            title=st.text_input("Task name")
            if st.form_submit_button("Add task") and title.strip():
                d["custom"].append({"id":"custom_"+str(int(time.time()*1000)),"subject":subj,"title":title.strip(),"detail":"Custom task — mark complete only after finishing."})
                save(); st.rerun()
        for t in d.get("custom",[]):
            v=st.checkbox(t["subject"]+" — "+t["title"],value=bool(d["done"].get(t["id"])),key="task_"+t["id"])
            if v != bool(d["done"].get(t["id"])): mark_task(t["id"],v)
    with right:
        st.header("Term 1 exam timetable")
        st.caption("Transcribed from supplied HTML. “P. L.” is preserved as printed; its meaning is not guessed.")
        for date,day,subject in exams:
            st.markdown("**"+date+"** · "+subject+"  \n"+day); st.divider()
        st.header("Focus timer")
        minutes=st.select_slider("Session length",options=[10,25,45],value=25)
        if "timer_end" not in st.session_state: st.session_state.timer_end=0
        if st.button("Start focus session",type="primary"):
            st.session_state.timer_end=time.time()+minutes*60
            st.session_state.timer_length=minutes; st.rerun()
        if st.session_state.timer_end > time.time():
            remain=int(st.session_state.timer_end-time.time())
            st.metric("Time remaining",str(remain//60).zfill(2)+":"+str(remain%60).zfill(2))
            st.progress(max(0,min(1,1-remain/(st.session_state.get("timer_length",25)*60))))
            st.caption("Keep this tab open. The timer may rerun the app each second; it is not guaranteed to sound an alarm.")
            time.sleep(1); st.rerun()
        elif st.session_state.get("timer_end",0):
            st.success("Session complete. Take a short break, then record what you learned.")
            if st.button("Log completed focus session"):
                d["focus_sessions"]=int(d.get("focus_sessions",0))+1
                d["study_minutes"]=int(d.get("study_minutes",0))+st.session_state.get("timer_length",25)
                st.session_state.timer_end=0; save(); st.rerun()
        st.markdown("**Focus rules**")
        st.write("• Phone outside study space.  \n• One task per session.  \n• Recall or solve without notes.  \n• Take a five-minute break after a 25-minute Pomodoro.")
if page == "AP Mastery":
    st.header("Arithmetic Progressions — mastery track")
    st.warning("Repeat questions 2–3 times and advance only after an independent attempt. Verify exercise numbering in your NCERT edition. PYQs must be real papers with year/source recorded; this dashboard does not invent question papers.")
    for key,title,detail in apbase:
        v=st.checkbox(title,value=bool(d["ap"].get(key)),key="ap_"+key,help=detail); st.caption(detail)
        if v != bool(d["ap"].get(key)): d["ap"][key]=v; save()
    with st.form("custom_ap_form"):
        custom_ap=st.text_input("Add an AP exercise, question set or verified PYQ")
        source=st.text_input("Source / year")
        if st.form_submit_button("Add AP set") and custom_ap.strip():
            d["custom_ap"].append({"id":"cap_"+str(int(time.time()*1000)),"title":custom_ap.strip(),"source":source.strip()})
            save(); st.rerun()
    for t in d.get("custom_ap",[]):
        label=t["title"]+(" — "+t.get("source","") if t.get("source") else "")
        v=st.checkbox(label,value=bool(d["ap"].get(t["id"])),key="ap_"+t["id"])
        if v != bool(d["ap"].get(t["id"])): d["ap"][t["id"]]=v; save()
    st.markdown("**Chapter mastery cycle**")
    st.write("Understand concept → NCERT examples/exercises → competency questions → verified chapter-wise PYQs → timed test → mistake analysis → correction → retest and spaced revision.")
if page == "Syllabus":
    st.header("Syllabus coverage tracker")
    st.caption("A checked chapter means a first study attempt only—not mastery. Return for recall, written practice, timed testing and mistake correction.")
    for subject,chapters in syllabus.items():
        with st.expander(subject+" — "+str(sum(bool(d["cover"].get(subject+"_"+str(i))) for i in range(len(chapters))))+"/"+str(len(chapters)),expanded=(subject=="Maths")):
            for i,chapter in enumerate(chapters):
                key=subject+"_"+str(i); v=st.checkbox(chapter,value=bool(d["cover"].get(key)),key="cover_"+key)
                if v != bool(d["cover"].get(key)): d["cover"][key]=v; save()
    st.info("Hindi and Sanskrit chapter names remain placeholders because the source image text was too small to read reliably. Replace them with the exact school syllabus rather than guessing.")
if page == "Life Goals":
    st.header("Long-term goals")
    st.write("Keep these visible, but do not let distant rewards replace today's schoolwork. Build the foundation first.")
    # Avoid unrelated stock photos. Use clean, labeled goal cards until the user supplies the exact personal inspiration images.
    goal_icons = {"G1":"💯","G2":"🚘","G3":"🏎️","G4":"🏋️","G5":"🏆","G6":"💪"}
    goal_overrides = d.get("goal_customizations", {})
    hidden_goal_ids = set(d.get("deleted_goals", []))
    visible_goals = [(gid, goal_overrides.get(gid, {}).get("title", title), goal_overrides.get(gid, {}).get("detail", detail)) for gid,title,detail in goals if gid not in hidden_goal_ids]
    for gid,title,detail in visible_goals:
        with st.container(border=True):
            left,right=st.columns([1,2],gap="large")
            with left:
                st.markdown(f'<div style="min-height:150px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#e8effa,#d5e3f7);border:1px solid #cbd9ec;border-radius:14px;font-size:64px;font-weight:800">{goal_icons.get(gid,"🎯")}</div>',unsafe_allow_html=True)
            with right:
                st.subheader(title)
                st.write(detail)
                done=st.checkbox("Milestone achieved",value=bool(d["goals"].get(gid)),key="goal_"+gid)
                if done != bool(d["goals"].get(gid)): d["goals"][gid]=done; save()
    st.subheader("Manage your life goals")
    st.caption("Edit or remove a goal whenever your priorities change. Changes are saved with your Mission 100 progress.")
    for gid,title,detail in list(goals):
        with st.expander("Edit: " + title):
            edited_title = st.text_input("Goal title", value=title, key="edit_title_"+gid)
            edited_detail = st.text_area("Why this goal matters / next steps", value=detail, key="edit_detail_"+gid)
            ec1, ec2 = st.columns(2)
            if ec1.button("Save changes", key="save_goal_"+gid, type="primary"):
                goals = [(g, edited_title.strip() if g == gid and edited_title.strip() else t, edited_detail.strip() if g == gid else desc) for g,t,desc in goals]
                d.setdefault("goal_customizations", {})[gid] = {"title": edited_title.strip(), "detail": edited_detail.strip()}
                save(); st.rerun()
            if ec2.button("Delete goal", key="delete_goal_"+gid):
                d["deleted_goals"] = list(set(d.get("deleted_goals", []) + [gid]))
                save(); st.rerun()
    with st.form("add_life_goal_form", clear_on_submit=True):
        st.subheader("Add a new life goal")
        new_goal_title = st.text_input("Goal")
        new_goal_detail = st.text_area("Reason / next steps")
        if st.form_submit_button("Add life goal") and new_goal_title.strip():
            d.setdefault("custom_goals", []).append({"id":"UG_"+str(int(time.time()*1000)), "title":new_goal_title.strip(), "detail":new_goal_detail.strip()})
            save(); st.rerun()
    for ug in d.get("custom_goals", []):
        with st.container(border=True):
            st.subheader(ug.get("title","Untitled goal"))
            st.write(ug.get("detail",""))
            changed_title = st.text_input("Edit goal", value=ug.get("title",""), key="custom_goal_title_"+ug["id"])
            changed_detail = st.text_area("Edit details", value=ug.get("detail",""), key="custom_goal_detail_"+ug["id"])
            cc1, cc2 = st.columns(2)
            if cc1.button("Save goal", key="save_custom_goal_"+ug["id"]):
                ug["title"] = changed_title.strip() or ug["title"]
                ug["detail"] = changed_detail.strip()
                save(); st.rerun()
            if cc2.button("Delete goal", key="delete_custom_goal_"+ug["id"]):
                d["custom_goals"] = [x for x in d["custom_goals"] if x.get("id") != ug["id"]]
                save(); st.rerun()
    st.subheader("Daily identity")
    st.markdown("- I start before I feel motivated.\n- I practise Maths every day.\n- I correct mistakes instead of hiding them.\n- I protect sleep and use my phone intentionally.\n- I measure honest work, not just hours.")
    review=st.text_area("Weekly review: what worked, what distracted me, what will I change?",value=d.get("notes",""),height=120)
    if review != d.get("notes",""): d["notes"]=review; save()
if page == "Focus Room":
    st.header("Focus Room")
    st.caption("Use a focused block, take intentional breaks, and record completed sessions.")
    focus_minutes = st.select_slider("Focus block length", options=[10,25,45,60], value=25, key="focus_room_minutes")
    if "room_end" not in st.session_state: st.session_state.room_end=0
    if "room_remaining" not in st.session_state: st.session_state.room_remaining=0
    if "room_length" not in st.session_state: st.session_state.room_length=focus_minutes
    if "room_finished" not in st.session_state: st.session_state.room_finished=False
    room_running = st.session_state.room_end > time.time()
    room_paused = st.session_state.room_remaining > 0 and not room_running
    c1,c2,c3,c4 = st.columns(4)
    if not room_running and not room_paused and c1.button("Start",type="primary",key="room_start"):
        st.session_state.room_length=focus_minutes; st.session_state.room_end=time.time()+focus_minutes*60; st.session_state.room_finished=False; st.rerun()
    if room_running and c2.button("Pause",key="room_pause"):
        st.session_state.room_remaining=max(1,int(st.session_state.room_end-time.time())); st.session_state.room_end=0; st.rerun()
    if room_paused and c1.button("Resume",type="primary",key="room_resume"):
        st.session_state.room_end=time.time()+st.session_state.room_remaining; st.session_state.room_remaining=0; st.rerun()
    if (room_running or room_paused) and c3.button("Stop",key="room_stop"):
        st.session_state.room_end=0; st.session_state.room_remaining=0; st.session_state.room_finished=False; st.rerun()
    if c4.button("Reset",key="room_reset"):
        st.session_state.room_end=0; st.session_state.room_remaining=0; st.session_state.room_finished=False; st.rerun()
    if room_running:
        remaining=max(0,int(st.session_state.room_end-time.time()))
        st.metric("Time remaining",f"{remaining//60:02d}:{remaining%60:02d}")
        st.progress(max(0,min(1,1-remaining/(st.session_state.room_length*60))))
        if remaining == 0:
            st.session_state.room_end=0; st.session_state.room_remaining=0; st.session_state.room_finished=True; st.rerun()
        time.sleep(1); st.rerun()
    elif room_paused:
        remaining=int(st.session_state.room_remaining)
        st.metric("Paused",f"{remaining//60:02d}:{remaining%60:02d}")
    elif st.session_state.room_finished:
        st.success("Focus block completed.")
        if st.button("Log completed session",key="room_log"):
            d["focus_sessions"]=int(d.get("focus_sessions",0))+1
            d["study_minutes"]=int(d.get("study_minutes",0))+int(st.session_state.room_length)
            st.session_state.room_finished=False; save(); st.rerun()
    st.metric("Completed focus sessions",int(d.get("focus_sessions",0)))
    st.metric("Recorded study minutes",int(d.get("study_minutes",0)))

if page == "My Dreams":
    st.header("My Dreams")
    st.caption("Keep your long-term ambitions visible; make progress through today's actions.")
    with st.form("dream_form",clear_on_submit=True):
        dream_title=st.text_input("Dream or goal")
        dream_reason=st.text_area("Why does it matter?")
        dream_target=st.text_input("Milestone or target date (optional)")
        if st.form_submit_button("Add dream") and dream_title.strip():
            d.setdefault("dreams",[]).append({"id":"dream_"+str(int(time.time()*1000)),"title":dream_title.strip(),"reason":dream_reason.strip(),"target":dream_target.strip(),"done":False})
            save(); st.rerun()
    for dream in d.setdefault("dreams",[]):
        with st.container(border=True):
            checked=st.checkbox("Milestone achieved: "+dream.get("title","Untitled"),value=bool(dream.get("done",False)),key="dream_"+dream.get("id",""))
            dream["done"]=checked
            st.write(dream.get("reason",""))
            if dream.get("target"): st.caption("Milestone / target: "+dream["target"])
            if st.button("Delete dream",key="delete_"+dream.get("id","")):
                d["dreams"]=[x for x in d["dreams"] if x.get("id")!=dream.get("id")]; save(); st.rerun()
    save()

if page == "Mistake Book":
    st.header("Mistake Book")
    st.caption("Record the question, the reason for the mistake, the correct method, and a retest date.")
    with st.form("mistake_form",clear_on_submit=True):
        subject=st.selectbox("Subject",["Maths","Science","SST","English","Marathi","Hindi","Sanskrit","AI"])
        question=st.text_input("Question or topic")
        reason=st.text_area("Why did I get it wrong?")
        correction=st.text_area("Correct method / key learning")
        retest=st.text_input("Retest date (optional)")
        if st.form_submit_button("Add mistake") and question.strip():
            d.setdefault("mistakes",[]).append({"id":"mistake_"+str(int(time.time()*1000)),"subject":subject,"question":question.strip(),"reason":reason.strip(),"correction":correction.strip(),"retest":retest.strip(),"fixed":False})
            save(); st.rerun()
    for mistake in d.setdefault("mistakes",[]):
        with st.container(border=True):
            st.subheader(mistake.get("subject","")+" — "+mistake.get("question",""))
            st.write("**Reason:** "+mistake.get("reason",""))
            st.write("**Correct method:** "+mistake.get("correction",""))
            if mistake.get("retest"): st.caption("Retest: "+mistake["retest"])
            mistake["fixed"]=st.checkbox("Retested and corrected",value=bool(mistake.get("fixed",False)),key="fixed_"+mistake.get("id",""))
    save()

if page == "Daily Discipline":
    st.header("Daily Discipline")
    st.caption("Build consistency, not guilt. Tick honestly.")
    items=[("morning","Started with a clear plan"),("maths","Completed daily Maths practice"),("revision","Revised an earlier topic"),("focus","Completed a distraction-free focus block"),("mistakes","Reviewed or corrected a mistake"),("tomorrow","Prepared tomorrow's first task")]
    for key,label in items:
        val=st.checkbox(label,value=bool(d.setdefault("discipline",{}).get(key,False)),key="discipline_"+key)
        if val != bool(d["discipline"].get(key,False)): d["discipline"][key]=val; save()
    st.subheader("Weekly reflection")
    reflection=st.text_area("What worked, what distracted you, and what will you change?",value=d.get("notes",""),key="discipline_reflection")
    if reflection != d.get("notes",""): d["notes"]=reflection; save()
    st.markdown("**STAY FOCUSED. STAY DISCIPLINED. WORK HARD. 100% IS THE GOAL.**")

if page == "Progress & Backup":
    st.header("Progress and backup")
    st.write("Progress is saved in a local JSON file while the host retains it. Some hosts reset local files during restarts or redeploys, so download backups regularly.")
    st.download_button("Download progress backup",json.dumps(d,ensure_ascii=False,indent=2),file_name="mission100-progress.json",mime="application/json",type="primary")
    uploaded=st.file_uploader("Restore a previous JSON backup",type=["json"])
    if uploaded and st.button("Restore backup"):
        try:
            incoming=json.loads(uploaded.getvalue().decode("utf-8"))
            if isinstance(incoming,dict) and "done" in incoming and "cover" in incoming:
                st.session_state.data=incoming; d=incoming; save(); st.success("Backup restored."); st.rerun()
            else: st.error("This does not look like a Mission 100 backup.")
        except Exception as e: st.error("Could not read backup: "+str(e))
    st.subheader("Syllabus totals")
    for subject,chapters in syllabus.items():
        count=sum(bool(d["cover"].get(subject+"_"+str(i))) for i in range(len(chapters)))
        st.write(subject+": "+str(count)+" / "+str(len(chapters)))
    st.caption("Checklists and XP are self-reported. They organize work but cannot verify mastery or guarantee exam marks.")
