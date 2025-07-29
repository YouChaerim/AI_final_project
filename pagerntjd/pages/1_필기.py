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

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = st.session_state.user_data.get("dark_mode", False)

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

# ✅ 스타일 + 상단 하얀줄 제거
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
.profile-group {{
    display: flex; gap: 16px; align-items: center;
}}
.profile-icon {{
    background-color: #888;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    cursor: pointer;
}}

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

# ✅ 상단 네비게이션 바
st.markdown(f"""
<div class="top-nav">
  <div class="nav-left">
    <div>
      <a href="/mainpage" target="_self">🐾 딸깍공</a>
    </div>
    <div class="nav-menu">
      <div><a href="/mainpage"   target="_self">메인페이지</a></div>
      <div><a href="/공부_시작"   target="_self">공부 시작</a></div>
      <div><a href="/필기"       target="_self">필기</a></div>
      <div><a href="/저장폴더"   target="_self">저장폴더</a></div>
      <div><a href="/퀴즈"       target="_self">퀴즈</a></div>
      <div><a href="/리포트"     target="_self">리포트</a></div>
      <div><a href="/랭킹"       target="_self">랭킹</a></div>
    </div>
  </div>
  <div class="profile-group">
    <div class="profile-icon" title="내 프로필"></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ✅ 아이콘 카드
st.markdown(f"""
<div class="icon-row">
    <a href="/필기인식" target="_self" style="text-decoration: none;">
        <div class="icon-card">
            <img src="data:image/png;base64,{load_base64('pen.png')}">
            <div>PDF인식(요약)</div>
        </div>
    </a>
    <a href="/저장폴더" target="_self" style="text-decoration: none;">
        <div class="icon-card">
            <img src="data:image/png;base64,{load_base64('icon_folder.png')}">
            <div>폴더</div>
        </div>
    </a>
    <a href="/퀴즈" target="_self" style="text-decoration: none;">
        <div class="icon-card">
            <img src="data:image/png;base64,{load_base64('quiz.png')}">
            <div>퀴즈</div>
        </div>
    </a>
</div>
""", unsafe_allow_html=True)

# ✅ 컨테이너 종료
st.markdown("</div>", unsafe_allow_html=True)
