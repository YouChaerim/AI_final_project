import streamlit as st
import os
import base64
import json

# ✅ 다크모드 상태 불러오기
if "user_data" not in st.session_state:
    if os.path.exists("user_data.json"):
        with open("user_data.json", "r", encoding="utf-8") as f:
            st.session_state.user_data = json.load(f)
    else:
        st.session_state.user_data = {"dark_mode": False}

# 캐릭터 헤더용 기본 키 보강
ud = st.session_state.user_data
ud.setdefault("active_char", "rabbit")   # bear/cat/rabbit/shiba
ud.setdefault("owned_hats", [])          # 예: ["cap"]
ud.setdefault("equipped_hat", None)      # 예: "cap"

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = ud.get("dark_mode", False)

# ✅ 테마 색상 지정
if st.session_state.dark_mode:
    bg_color = "#1C1C1E"; font_color = "#F2F2F2"
    card_bg = "#2C2C2E"; hover_bg = "#3A3A3C"
    nav_bg = "#2C2C2E"; dark_orange = "#FF9330"; label_color = "white"
else:
    bg_color = "#FAFAFA"; font_color = "#333"
    card_bg = "white"; hover_bg = "#F5F5F5"
    nav_bg = "rgba(255, 255, 255, 0.9)"; dark_orange = "#FF9330"; label_color = font_color

# ✅ 페이지 설정
st.set_page_config(page_title="딸깍공 - 필기", layout="wide", initial_sidebar_state="collapsed")

# ✅ Base64 이미지 로더 함수
def load_base64(filename):
    ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
    path = os.path.join(ASSETS_DIR, filename)
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# === 헤더 아바타 헬퍼 ===
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

def get_char_image_uri(char_key: str, hat_id: str | None = None) -> str:
    """
    전용 파일 우선 탐색:
      - assets/items/hats/{char}{sep}{hat_id}.png
      - assets/characters/{char}{sep}{hat_id}.png
      - assets/characters/{char}.png
    sep ∈ {"", "_", "-"}  /  'shiba'는 'siba'도 자동 지원
    """
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
        if os.path.exists(p):
            return _to_data_uri(p)

    # fallback
    return "data:image/svg+xml;utf8," \
           "<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'><text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text></svg>"

def current_avatar_uri() -> str:
    char_key = ud.get("active_char", "rabbit")
    hat_id = ud.get("equipped_hat")
    if hat_id and (hat_id in ud.get("owned_hats", [])):
        return get_char_image_uri(char_key, hat_id)
    return get_char_image_uri(char_key)

# ✅ 스타일 + 상단 하얀줄 제거 + 헤더 아바타/이동
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');

html, body {{
    font-family: 'Noto Sans KR', sans-serif;
    background-color: {bg_color};
    color: {font_color};
    zoom: 1.10;
    margin: 0;
}}
.stApp {{ background-color: {bg_color}; }}
.block-container {{ padding-top: 0 !important; }}
.container {{ max-width: 1200px; margin: auto; padding: 40px; }}
a {{ text-decoration: none !important; color: {font_color}; }}

/* ===== 상단 네비게이션 바 ===== */
.top-nav {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    margin-top: -40px !important;
    background-color: {nav_bg};
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}}
.nav-left {{ display: flex; align-items: center; gap: 60px; }}
.top-nav .nav-left > div:first-child a {{
    color: {font_color} !important;
    font-size: 28px;
    font-weight: bold;
    display: flex;
    align-items: center;
    gap: 6px;
}}
.nav-menu {{
    display: flex;
    gap: 36px;
    font-size: 18px;
    font-weight: 600;
}}
.nav-menu div a {{
    color: {font_color} !important;
    transition: all 0.2s ease;
}}
.nav-menu div:hover a {{
    color: {dark_orange} !important;
}}

/* ✅ 헤더 오른쪽 동그라미 자체를 살짝 왼쪽으로 */
.profile-group {{ display: flex; gap: 16px; align-items: center; margin-right: 12px; }}
.profile-icon {{
    width: 36px; height: 36px; border-radius: 50%;
    background: linear-gradient(135deg,#DDEFFF,#F8FBFF);
    overflow: hidden; display: flex; align-items: center; justify-content: center;
    box-shadow: 0 1px 2px rgba(0,0,0,0.06);
}}
.profile-icon img {{ width: 100%; height: 100%; object-fit: contain; image-rendering: auto; }}

/* 아이콘 카드 스타일 */
.icon-row {{
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 80px;
    margin-top: 80px;
}}
.icon-card {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 240px;
    height: 240px;
    border: 1px solid #eee;
    border-radius: 20px;
    padding: 22px;
    background-color: {card_bg};
    box-shadow: 1px 1px 10px rgba(0,0,0,0.04);
    transition: all 0.2s ease-in-out;
}}
.icon-card:hover {{
    background-color: {hover_bg};
    transform: scale(1.04);
}}
.icon-card img {{
    height: 88px;
    margin-bottom: 16px;
}}
.icon-card div {{
    font-size: 17px;
    font-weight: 500;
    color: {font_color};
}}

/* ✅ 상단 흰줄 제거 핵심 */
header, .st-emotion-cache-18ni7ap, .st-emotion-cache-6qob1r {{
    display: none !important;
}}
.stApp > header, .stApp > div:first-child {{
    margin-top: 0 !important;
    padding-top: 0 !important;
}}
[data-testid="collapsedControl"], [data-testid="stSidebar"] {{
    display: none !important;
}}
</style>
""", unsafe_allow_html=True)

# ✅ 컨테이너 시작
st.markdown('<div class="container">', unsafe_allow_html=True)

# ✅ 상단 네비게이션 바 (캐릭터 아바타 적용)
header_avatar_uri = current_avatar_uri()
st.markdown(f"""
<div class="top-nav">
  <div class="nav-left">
    <div>
      <a href="/" target="_self">🐾 딸깍공</a>
    </div>
    <div class="nav-menu">
      <div><a href="/"   target="_self">메인페이지</a></div>
      <div><a href="/main"   target="_self">공부 시작</a></div>
      <div><a href="/ocr_paddle"       target="_self">PDF요약</a></div>
      <div><a href="/folder_page"   target="_self">저장폴더</a></div>
      <div><a href="/quiz"       target="_self">퀴즈</a></div>
      <div><a href="/report"     target="_self">리포트</a></div>
      <div><a href="/ranking"       target="_self">랭킹</a></div>
    </div>
  </div>
  <div class="profile-group">
    <div class="profile-icon" title="내 캐릭터">
      <img src="{header_avatar_uri}" alt="avatar"/>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ✅ 아이콘 카드
st.markdown(f"""
<div class="icon-row">
    <a href="/writing_recognition" target="_self" style="text-decoration: none;">
        <div class="icon-card">
            <img src="data:image/png;base64,{load_base64('pen.png')}">
            <div>PDF인식(요약)</div>
        </div>
    </a>
    <a href="/folder_page" target="_self" style="text-decoration: none;">
        <div class="icon-card">
            <img src="data:image/png;base64,{load_base64('icon_folder.png')}">
            <div>폴더</div>
        </div>
    </a>
    <a href="/quiz" target="_self" style="text-decoration: none;">
        <div class="icon-card">
            <img src="data:image/png;base64,{load_base64('quiz.png')}">
            <div>퀴즈</div>
        </div>
    </a>
</div>
""", unsafe_allow_html=True)

# ✅ 컨테이너 종료
st.markdown("</div>", unsafe_allow_html=True)
