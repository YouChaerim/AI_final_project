# pages/folder_page.py
# -*- coding: utf-8 -*-
import streamlit as st
import os, json, base64

# ================== 기본 설정 ==================
USER_JSON_PATH = "user_data.json"
SAVE_ROOT = os.path.abspath("saved_files")  # 업로드 저장 루트

st.set_page_config(layout="wide", page_title="딸깍공 저장폴더", initial_sidebar_state="collapsed")

# ================== 유틸 ==================
def load_user_data() -> dict:
    if os.path.exists(USER_JSON_PATH):
        try:
            with open(USER_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "dark_mode": False,
        "active_char": "rabbit",
        "owned_hats": [],
        "equipped_hat": None,
    }

def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)

def save_uploaded_file(folder_name: str, up):
    dst_dir = os.path.join(SAVE_ROOT, folder_name)
    ensure_dir(dst_dir)
    dst_path = os.path.join(dst_dir, up.name)
    with open(dst_path, "wb") as f:
        f.write(up.getbuffer())
    return dst_path

def _resolve_assets_root():
    here = os.path.dirname(__file__)
    cands = [
        os.path.abspath(os.path.join(here, "assets")),
        os.path.abspath(os.path.join(here, "..", "assets")),
    ]
    for p in cands:
        if os.path.isdir(p):
            return p
    return cands[0]

ASSETS_ROOT = _resolve_assets_root()

def _to_data_uri(path: str) -> str:
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")

def get_char_image_uri(char_key: str) -> str:
    p = os.path.join(ASSETS_ROOT, "characters", f"{char_key}.png")
    if os.path.exists(p):
        return _to_data_uri(p)
    return "data:image/svg+xml;utf8," \
           "<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'><text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text></svg>"

# ================== 세션 ==================
if "user_data" not in st.session_state:
    st.session_state.user_data = load_user_data()
u = st.session_state.user_data
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = u.get("dark_mode", False)

header_avatar_uri = get_char_image_uri(u.get("active_char", "rabbit"))

# ================== 스타일 ==================
if st.session_state.dark_mode:
    bg = "#1C1C1E"; fg = "#F2F2F2"; nav_bg = "#2C2C2E"
    card_bg = "#242426"; card_border = "rgba(255,255,255,.06)"
    title_c = "#000000"   # 라벨 검정
    shadow = "rgba(0,0,0,.35)"
else:
    bg = "#F5F5F7"; fg = "#2B2B2E"; nav_bg = "rgba(255,255,255,.9)"
    card_bg = "#FFFFFF"; card_border = "rgba(0,0,0,.06)"
    title_c = "#000000"   # 라벨 검정
    shadow = "rgba(0,0,0,.10)"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800;900&display=swap');
html, body {{ background:{bg}; color:{fg}; font-family:'Noto Sans KR', sans-serif; zoom:1.10; margin:0; }}
.stApp {{ background:{bg}; }}
.block-container {{ padding-top:0 !important; }}
header {{ display:none !important; }}

/* 본문 컨테이너 */
.container {{ max-width:1200px; margin:auto; padding:4px 40px 24px; }}

/* ===== 헤더 (공통 유지) ===== */
a, a:hover, a:focus, a:visited {{ text-decoration:none !important; }}
.top-nav {{
  display:flex; justify-content:space-between; align-items:center;
  padding:12px 0; margin-top:40px !important; background:{nav_bg};
  box-shadow:0 2px 4px rgba(0,0,0,.05);
}}
.nav-left {{ display:flex; align-items:center; gap:60px; }}
.top-nav .nav-left > div:first-child a {{ color:#000 !important; font-size:28px; font-weight:900; }}
.nav-menu {{ display:flex; gap:36px; font-size:18px; font-weight:700; }}
.nav-menu div a {{ color:#000 !important; transition:.2s; }}
.nav-menu div:hover a {{ color:#FF9330 !important; }}
.profile-group {{ display:flex; gap:16px; align-items:center; margin-right:12px; }}
.profile-icon {{
  width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#DDEFFF,#F8FBFF);
  overflow:hidden;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 2px rgba(0,0,0,.06);
}}
.profile-icon img {{ width:100%; height:100%; object-fit:contain; }}

/* ===== 세로 풀폭 카드 리스트 ===== */
.rows {{ display:flex; flex-direction:column; gap:120px; margin-top:12px; }}  /* ← 간격 크게(120px) */
.row-link {{ display:block; padding:4px 0; }}
.row-link + .row-link {{ margin-top:120px; }}                                /* gap 보정 중복적용 */

.row-card {{
  width:100%;
  min-height:220px;            /* 카드 높이 살짝 업 */
  background:{card_bg};
  border:1px solid {card_border};
  border-radius:28px;
  box-shadow:0 12px 30px {shadow}, inset 0 1px 0 rgba(255,255,255,.35);
  display:flex; align-items:center; justify-content:center;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}}
.row-card:hover {{
  transform: translateY(-3px);
  box-shadow:0 18px 40px rgba(0,0,0,.14);
  border-color: rgba(255,147,48,.35);
}}

.row-content {{ display:flex; flex-direction:column; align-items:center; gap:12px; }}
.row-icon img {{ width:84px; height:84px; object-fit:contain; }}
.row-title {{ font-size:22px; font-weight:900; color:{title_c}; letter-spacing:.2px; }}
</style>
""", unsafe_allow_html=True)

# ================== 헤더 (그대로) ==================
st.markdown(f"""
<div class="top-nav">
  <div class="nav-left">
    <div><a href="/" target="_self">🐾 딸깍공</a></div>
    <div class="nav-menu">
      <div><a href="/" target="_self">메인페이지</a></div>
      <div><a href="/main" target="_self">공부 시작</a></div>
      <div><a href="/ocr_paddle" target="_self">PDF 요약</a></div>
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

# ================== 본문 ==================
st.markdown('<div class="container">', unsafe_allow_html=True)

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-body">', unsafe_allow_html=True)

folder_items = [
    {"name": "PDF 폴더", "img": "cute1.png", "link": "/pdf_folder"},
    {"name": "오답 폴더", "img": "cute2.png", "link": "/wrong_folder"},
    {"name": "메모장 폴더", "img": "cute3.png", "link": "/memo_folder"},
]

# 세로 카드 렌더
st.markdown('<div class="rows">', unsafe_allow_html=True)
for folder in folder_items:
    ipath = os.path.join(ASSETS_ROOT, folder["img"])
    if os.path.exists(ipath):
        icon_html = f"<img src='{_to_data_uri(ipath)}'/>"
    else:
        icon_html = "📁"

    st.markdown(
        f"""
        <a class="row-link" href="{folder['link']}" target="_self">
          <div class="row-card">
            <div class="row-content">
              <div class="row-icon">{icon_html}</div>
              <div class="row-title">{folder['name']}</div>
            </div>
          </div>
        </a>
        """,
        unsafe_allow_html=True,
    )
st.markdown("</div>", unsafe_allow_html=True)   # /rows

st.markdown("</div>", unsafe_allow_html=True)  # /panel-body
st.markdown("</div>", unsafe_allow_html=True)  # /panel
st.markdown("</div>", unsafe_allow_html=True)  # /container
