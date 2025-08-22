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
    panel_bg = "#1F1F22"; panel_shadow = "rgba(0,0,0,.35)"
else:
    bg = "#F5F5F7"; fg = "#2B2B2E"; nav_bg = "rgba(255,255,255,.9)"
    panel_bg = "#FFFFFF"; panel_shadow = "rgba(0,0,0,.08)"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800;900&display=swap');
html, body {{ background:{bg}; color:{fg}; font-family:'Noto Sans KR', sans-serif; zoom:1.10; margin:0; }}
.stApp {{ background:{bg}; }}
.block-container {{ padding-top:0 !important; }}
header {{ display:none !important; }}

/* 본문 컨테이너: 상단 패딩 크게 줄임(24px → 4px) */
.container {{ max-width:1200px; margin:auto; padding:4px 40px 24px; }}

/* 헤더(위치 유지) */
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

/* 패널: 상단 마진 제거(12px → 0px)로 바로 위로 붙게 */
.panel {{
  position: relative;
  background:{panel_bg};
  border-radius:18px;
  box-shadow:0 6px 24px {panel_shadow};
  overflow:hidden;
  margin-top:0px;                 /* ← 여기! */
}}

.panel-head {{
  background: linear-gradient(90deg,#FF9330,#FF7A00);
  color:white; text-align:center; font-size:34px; font-weight:900; padding:18px 20px;
}}
.panel-body {{ padding:24px 36px 20px; }}

/* 카드: 왼쪽 정렬 */
.card {{ text-align:left; }}
.folder-icon img {{ width:108px; height:108px; object-fit:contain; margin-bottom:8px; }}
.folder-title {{ margin: 6px 0 0; font-size:24px; font-weight:900; letter-spacing:.2px; }}

/* 업로더를 '파일 업로드' 버튼처럼 보이게 */
.upload-wrap [data-testid="stFileUploader"] > label,
[data-testid="stFileUploader"] > label {{ display: none !important; }}

.upload-wrap [data-testid="stFileUploader"] section,
.upload-wrap [data-testid="stFileUploader"] > div,
[data-testid="stFileUploader"] section,
[data-testid="stFileUploader"] > div {{
  padding: 0 !important; border: 0 !important; background: transparent !important;
}}

.upload-wrap section[data-testid="stFileUploaderDropzone"],
.upload-wrap div[data-testid="stFileUploaderDropzone"],
section[data-testid="stFileUploaderDropzone"],
div[data-testid="stFileUploaderDropzone"] {{
  position: relative;
  width: 260px; height: 56px;
  margin: 6px 0 0 0 !important;  /* 제목 바로 아래 */
  border: 0 !important; border-radius: 16px;
  background: linear-gradient(90deg,#FF9330,#FF7A00) !important;
  box-shadow: 0 8px 18px rgba(255,147,48,.35);
  cursor: pointer;
}}

.upload-wrap section[data-testid="stFileUploaderDropzone"] *,
.upload-wrap div[data-testid="stFileUploaderDropzone"] *,
section[data-testid="stFileUploaderDropzone"] *,
div[data-testid="stFileUploaderDropzone"] * {{ display: none !important; }}

.upload-wrap section[data-testid="stFileUploaderDropzone"]::before,
.upload-wrap div[data-testid="stFileUploaderDropzone"]::before,
section[data-testid="stFileUploaderDropzone"]::before,
div[data-testid="stFileUploaderDropzone"]::before {{
  content: "파일 업로드";
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 900; font-size: 18px; letter-spacing: .2px;
}}
.upload-wrap section[data-testid="stFileUploaderDropzone"]:hover,
.upload-wrap div[data-testid="stFileUploaderDropzone"]:hover,
section[data-testid="stFileUploaderDropzone"]:hover,
div[data-testid="stFileUploaderDropzone"]:hover {{ filter: brightness(.98); }}

/* 저장 버튼 */
.save-btn > button {{
  width:260px; background:#FF9330 !important; color:white !important;
  border:0; border-radius:14px; font-weight:900; font-size:18px;
  padding:12px 0; box-shadow:0 6px 16px rgba(255,147,48,.35);
}}
.save-row {{ display:flex; justify-content:center; margin-top:14px; }}

/* 스트림릿이 간혹 뿌리는 빈 블럭을 제거해 위 여백 더 줄이기(안전) */
.block-container > div:empty {{ display:none !important; margin:0 !important; padding:0 !important; }}
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
st.markdown('<div class="panel-head">저장 폴더</div>', unsafe_allow_html=True)
st.markdown('<div class="panel-body">', unsafe_allow_html=True)

folder_items = [
    {"name": "PDF 폴더", "img": "cute1.png", "link": "/pdf_folder"},
    {"name": "오답 폴더", "img": "cute2.png", "link": "/wrong_folder"},
    {"name": "메모장 폴더", "img": "cute3.png", "link": "/memo_folder"},
]
cols = st.columns(3)

for i, (col, folder) in enumerate(zip(cols, folder_items)):
    with col:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        # 아이콘 (링크 걸기)
        ipath = os.path.join(ASSETS_ROOT, folder["img"])
        if os.path.exists(ipath):
            st.markdown(
                f"<a href='{folder['link']}' target='_self'>"
                f"<div class='folder-icon'><img src='{_to_data_uri(ipath)}'/></div>"
                f"</a>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<a href='{folder['link']}' target='_self'><div class='folder-icon'>📁</div></a>",
                unsafe_allow_html=True
            )

        # 제목 (링크 걸기)
        st.markdown(
            f"<a href='{folder['link']}' target='_self'>"
            f"<div class='folder-title'>{folder['name']}</div>"
            f"</a>",
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)  # /card

st.markdown("</div>", unsafe_allow_html=True)  # /panel-body
st.markdown("</div>", unsafe_allow_html=True)  # /panel
st.markdown("</div>", unsafe_allow_html=True)  # /container
