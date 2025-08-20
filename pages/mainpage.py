# main_page.py
import streamlit as st
import json, os, base64, uuid, re

# ---------------- Utils ----------------
def _parse_todo_lines(text: str) -> list[str]:
    if not text:
        return []
    parts = re.split(r"[\n,;]+", text)
    parts = [re.sub(r"^\s*[-*•\d\.\)]\s*", "", p).strip() for p in parts]
    return [p for p in parts if p]

def _to_data_uri(path: str) -> str:
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")

# -------------- Load user_data ----------
if "user_data" not in st.session_state:
    if os.path.exists("user_data.json"):
        with open("user_data.json", "r", encoding="utf-8") as f:
            st.session_state.user_data = json.load(f)
    else:
        st.session_state.user_data = {
            "todo": "오늘 공부하기\n내일 밥먹기",
            "memo": "중간고사 다음 주!",
            "study_hour": 1,
            "study_minute": 30,
            "dark_mode": False
        }
ud = st.session_state.user_data

# defaults
ud.setdefault("active_char", "rabbit")
ud.setdefault("owned_hats", [])
ud.setdefault("equipped_hat", None)
ud.setdefault("study_hour", ud.get("study_hour", 0))
ud.setdefault("study_minute", ud.get("study_minute", 0))

# migrate todo -> todo_items
if "todo_items" not in ud or not isinstance(ud["todo_items"], list):
    ud["todo_items"] = [{"id": str(uuid.uuid4()), "text": t, "done": False}
                        for t in _parse_todo_lines(ud.get("todo", ""))]

# draft/preview (편집 모드용)
if "todo_draft" not in st.session_state:
    st.session_state.todo_draft = "\n".join([i["text"] for i in ud["todo_items"]]) or ud.get("todo", "")
if "todo_preview" not in st.session_state:
    st.session_state.todo_preview = [{"id": str(uuid.uuid4()), "text": t}
                                     for t in _parse_todo_lines(st.session_state.todo_draft)]

# -------------- Theme -------------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = ud.get("dark_mode", False)

if st.session_state.dark_mode:
    bg_color = "#1C1C1E"; font_color = "#F2F2F2"
    card_bg = "#2C2C2E"; nav_bg = "#2C2C2E"
    dark_orange = "#FF9330"; label_color = "white"
else:
    bg_color = "#FAFAFA"; font_color = "#333"
    card_bg = "white"; nav_bg = "rgba(255,255,255,0.9)"
    dark_orange = "#FF9330"; label_color = font_color

st.set_page_config(layout="wide", page_title="딸깍공 메인페이지", initial_sidebar_state="collapsed")

# -------------- Assets ------------------
def _resolve_assets_root():
    here = os.path.dirname(__file__)
    for p in [
        os.path.abspath(os.path.join(here, "assets")),
        os.path.abspath(os.path.join(here, "..", "assets")),
    ]:
        if os.path.isdir(p): return p
    return os.path.abspath(os.path.join(here, "assets"))
ASSETS_ROOT = _resolve_assets_root()

def get_char_image_uri(char_key: str, hat_id: str | None = None) -> str:
    keys = [char_key] + (["siba"] if char_key == "shiba" else [])
    cands = []
    if hat_id:
        for k in keys:
            for sep in ["", "_", "-"]:
                cands += [
                    os.path.join(ASSETS_ROOT, "items", "hats", f"{k}{sep}{hat_id}.png"),
                    os.path.join(ASSETS_ROOT, "characters", f"{k}{sep}{hat_id}.png"),
                ]
    for k in keys:
        cands.append(os.path.join(ASSETS_ROOT, "characters", f"{k}.png"))
    for p in cands:
        if os.path.exists(p): return _to_data_uri(p)
    return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'><text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text></svg>"

def current_avatar_uri() -> str:
    char_key = ud.get("active_char", "rabbit")
    hat_id = ud.get("equipped_hat")
    return get_char_image_uri(char_key, hat_id) if (hat_id and hat_id in ud.get("owned_hats", [])) else get_char_image_uri(char_key)

# -------------- Styles ------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
:root {{ --right-col-offset: -28px; }}

html, body {{ background-color:{bg_color}; color:{font_color}; font-family:'Noto Sans KR', sans-serif; zoom:1.10; margin:0; }}
.stApp {{ background-color:{bg_color}; }}
.block-container {{ padding-top:0 !important; }}
.container {{ max-width:1200px; margin:auto; padding:40px; }}
a {{ text-decoration:none !important; color:{font_color}; }}

/* ===== 사이드바/툴바 완전 숨김 ===== */
[data-testid="stSidebar"], [data-testid="stSidebarNav"], [data-testid="stToolbar"] {{ display: none !important; }}

/* Header */
.top-nav {{ display:flex; justify-content:space-between; align-items:center; padding:12px 0; margin-top:-40px !important; background-color:{nav_bg}; box-shadow:0 2px 4px rgba(0,0,0,0.05); }}
.nav-left {{ display:flex; align-items:center; gap:60px; }}
.top-nav .nav-left > div:first-child a {{ color:#000 !important; font-size:28px; font-weight:bold; }}
.nav-menu {{ display:flex; gap:36px; font-size:18px; font-weight:600; }}
.nav-menu div a {{ color:#000 !important; transition:.2s; }}
.nav-menu div:hover a {{ color:#FF9330 !important; }}

/* Profile */
.profile-group {{ display:flex; gap:16px; align-items:center; margin-right:12px; }}
.profile-icon {{ width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,#DDEFFF,#F8FBFF); overflow:hidden; display:flex; align-items:center; justify-content:center; box-shadow:0 1px 2px rgba(0,0,0,0.06); }}
.profile-icon img {{ width:100%; height:100%; object-fit:contain; }}

/* ====== 주황 히어로 ====== */
.main-box {{ background:{dark_orange}; border-radius:14px; padding:90px 0 140px 0; text-align:center; color:#fff; font-size:36px; font-weight:900; margin-bottom:16px; }}
.main-btn {{ margin-top:30px; padding:16px 40px; background:#fff; color:#000; font-weight:800; border:none; border-radius:8px; font-size:22px; }}

/* ===== 공통 카드 - 초밀착 ===== */
div[data-testid="stExpander"] {{ background:#fff; border-radius:10px; border:1px solid #eee; box-shadow:0 1px 2px rgba(0,0,0,0.04); overflow:hidden; margin: 1px 0 !important; }}
div[data-testid="stExpander"] > details {{ padding:0; }}
div[data-testid="stExpander"] .st-expanderHeader, div[data-testid="stExpander"] summary {{ padding:8px 12px !important; font-weight:800; list-style:none; border-bottom:1px solid #f2f2f2; }}
div[data-testid="stExpander"] summary svg {{ display:none; }}
div[data-testid="stExpander"] .st-expanderContent {{ padding: 4px 12px 8px !important; }}
div[data-testid="stExpander"] .stCheckbox {{ margin: 1px 0 !important; }}
div[data-testid="stExpander"] .stCheckbox > label {{ padding: 1px 0 !important; gap: 8px !important; }}
div[data-testid="stExpander"] .stCheckbox p, div[data-testid="stExpander"] .stCheckbox span {{ margin:0 !important; line-height:1.15 !important; }}

/* ===== 오른쪽 열 정렬/간격 ===== */
.right-col-align {{ margin-top: var(--right-col-offset) !important; }}
.tight-stack [data-testid="stExpander"]{{ margin: 1px 0 !important; }}
.tight-stack [data-testid="stElementContainer"]{{ margin-bottom: 4px !important; }}
.tight-stack .stColumns {{ margin: 2px 0 !important; }}
.tight-stack .stButton > button {{ margin-top: 0 !important; }}

@media (max-width: 1200px) {{ .right-col-align {{ margin-top: -18px !important; }} }}
@media (max-width: 1024px) {{ .right-col-align {{ margin-top: -8px !important; }} }}
@media (max-width: 820px) {{ .right-col-align {{ margin-top: 0 !important; }} }}

header {{ display:none !important; }}
::selection {{ background:#FF9330; color:#fff; }}
label, .stTextInput label, .stTextArea label, .stSelectbox label {{ color:{label_color} !important; font-weight:600; }}
</style>
""", unsafe_allow_html=True)

# -------------- Page ---------------
st.markdown('<div class="container">', unsafe_allow_html=True)

# 상단 네비
header_avatar_uri = current_avatar_uri()
st.markdown(f"""
<div class="top-nav">
  <div class="nav-left">
    <div><a href="/mainpage" target="_self">🐾 딸깍공</a></div>
    <div class="nav-menu">
      <div><a href="/mainpage" target="_self">메인페이지</a></div>
      <div><a href="/main" target="_self">공부 시작</a></div>
      <div><a href="/ocr_paddle" target="_self">PDF요약</a></div>
      <div><a href="/folder_page" target="_self">저장폴더</a></div>
      <div><a href="/quiz" target="_self">퀴즈</a></div>
      <div><a href="/report" target="_self">리포트</a></div>
      <div><a href="/ranking" target="_self">랭킹</a></div>
    </div>
  </div>
  <div class="profile-group">
    <div class="profile-icon" title="내 캐릭터"><img src="{header_avatar_uri}" alt="avatar"/></div>
  </div>
</div>
""", unsafe_allow_html=True)

# 로그인 버튼 자리(삭제) → 같은 높이의 공간만 유지
nav_login = st.container()
with nav_login:
    login_btn_col = st.columns([10, 1])[1]
    with login_btn_col:
        # 버튼 대신 동일 높이의 공간(약 40px)만 남겨서 레이아웃 간격 유지
        st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

# 본문 2열
col1, col2 = st.columns([2.5, 1])

with col1:
    # 주황 히어로
    st.markdown(f"""
    <div class="main-box">
      오늘 공부 시작하기<br>
      <a href="/main" target="_self">
        <button class="main-btn">공부 시작</button>
      </a>
    </div>
    """, unsafe_allow_html=True)

    # 주황색 박스 바로 아래: 다크모드 버튼(기존 크기와 비슷하게)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("🌗 다크모드", key="dark_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        ud["dark_mode"] = st.session_state.dark_mode
        with open("user_data.json", "w", encoding="utf-8") as f:
            json.dump(ud, f, ensure_ascii=False, indent=2)
        st.rerun()

with col2:
    # 오른쪽 열: 상단 정렬 + 초밀착
    st.markdown('<div class="right-col-align tight-stack">', unsafe_allow_html=True)

    # ===== 비편집 모드 =====
    if not st.session_state.get("edit_mode", False):
        changed = False
        with st.expander("📌 오늘 할 일", expanded=True):
            for i, item in enumerate(ud["todo_items"]):
                key = f"todo_{item['id']}"
                val = st.checkbox(item["text"], value=item["done"], key=key)
                if val != item["done"]:
                    ud["todo_items"][i]["done"] = val
                    changed = True
        if changed:
            ud["todo"] = "\n".join([t["text"] for t in ud["todo_items"]])
            with open("user_data.json", "w", encoding="utf-8") as f:
                json.dump(ud, f, ensure_ascii=False, indent=2)

        with st.expander("🗓 빠른 메모", expanded=True):
            st.write(ud["memo"])

        with st.expander("⏰ 오늘 공부시간", expanded=True):
            st.write(f"{ud['study_hour']}시간 {ud['study_minute']}분")

        if st.button("✏️ 변경하기", use_container_width=True):
            st.session_state.edit_mode = True
            st.session_state.todo_draft = "\n".join([i["text"] for i in ud["todo_items"]]) or ud.get("todo", "")
            st.session_state.todo_preview = [{"id": str(uuid.uuid4()), "text": t}
                                             for t in _parse_todo_lines(st.session_state.todo_draft)]
            st.rerun()

    # ===== 편집 모드 =====
    else:
        def _on_draft_change():
            st.session_state.todo_preview = [{"id": str(uuid.uuid4()), "text": t}
                                             for t in _parse_todo_lines(st.session_state.todo_draft)]

        st.text_area(
            "📝 오늘 할 일",
            key="todo_draft",
            placeholder="한 줄에 하나씩 입력 (쉼표/엔터/세미콜론 가능)\n예) 오늘 공부하기, 내일 밥먹기",
            height=140,
            on_change=_on_draft_change
        )
        st.caption("입력하면 아래에 미리보기 체크박스가 자동 생성됩니다. 저장 후 메인 화면에서 체크 가능합니다.")

        if st.session_state.todo_preview:
            for p in st.session_state.todo_preview:
                st.checkbox(p["text"], value=False, key=f"pv_{p['id']}", disabled=True)
        else:
            st.caption("미리볼 항목이 없습니다. 내용을 입력하세요.")

        with st.form("save_form"):
            memo = st.text_area("🗓 빠른 메모", value=ud["memo"])
            hour = st.selectbox("공부 시간(시간)", list(range(0,13)), index=ud["study_hour"])
            minute = st.selectbox("공부 시간(분)", list(range(0,61)), index=ud["study_minute"])
            save_clicked = st.form_submit_button("저장하기")

        if save_clicked:
            preview_source = st.session_state.todo_preview or [{"id": str(uuid.uuid4()), "text": t}
                                                               for t in _parse_todo_lines(st.session_state.todo_draft)]
            ud["todo_items"] = [{"id": str(uuid.uuid4()), "text": p["text"], "done": False} for p in preview_source]
            ud["todo"] = "\n".join([t["text"] for t in ud["todo_items"]])
            ud["memo"] = memo
            ud["study_hour"] = hour
            ud["study_minute"] = minute
            with open("user_data.json", "w", encoding="utf-8") as f:
                json.dump(ud, f, ensure_ascii=False, indent=2)
            st.session_state.edit_mode = False
            st.success("저장되었습니다!")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)  # right-col-align 끝

st.markdown("</div>", unsafe_allow_html=True)

# (하단) 다크모드 토글 블록은 제거됨 — 위에서 주황색 박스 바로 아래에 배치됨
