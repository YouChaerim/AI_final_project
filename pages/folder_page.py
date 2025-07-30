import streamlit as st
import os
import json

# ===== 세션 상태 초기화 =====
if "user_data" not in st.session_state:
    if os.path.exists("user_data.json"):
        with open("user_data.json", "r", encoding="utf-8") as f:
            st.session_state.user_data = json.load(f)
    else:
        st.session_state.user_data = {
            "todo": "수학 예제 풀기\n영단어 암기",
            "memo": "중간고사 다음 주!",
            "study_hour": 1,
            "study_minute": 30,
            "dark_mode": False
        }

if "study_hour" not in st.session_state.user_data:
    st.session_state.user_data["study_hour"] = 0
if "study_minute" not in st.session_state.user_data:
    st.session_state.user_data["study_minute"] = 0

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = st.session_state.user_data.get("dark_mode", False)

if st.session_state.dark_mode:
    bg_color = "#1C1C1E"; font_color = "#F2F2F2"
    card_bg = "#2C2C2E"; hover_bg = "#3A3A3C"
    nav_bg = "#2C2C2E"; dark_orange = "#FF9330"; label_color = "white"
else:
    bg_color = "#FAFAFA"; font_color = "#333"
    card_bg = "white"; hover_bg = "#F5F5F5"
    nav_bg = "rgba(255, 255, 255, 0.9)"; dark_orange = "#FF9330"; label_color = font_color

dark_input_css = """
input[type="text"],
textarea,
select,
.stTextInput > div > input {
    background-color: #2C2C2E !important;
    color: white !important;
    border: 1px solid #555 !important;
}
""" if st.session_state.dark_mode else ""

# ===== 페이지 설정 =====
st.set_page_config(
    layout="wide",
    page_title="딸깍공 저장폴더",
    initial_sidebar_state="collapsed"
)

# ===== 헤더/네비바/전체 스타일 (margin-top: 40px) =====
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');

html, body {{
    background-color: {bg_color};
    color: {font_color};
    font-family: 'Noto Sans KR', sans-serif;
    zoom: 1.10;
    margin: 0;
}}
.stApp {{ background-color: {bg_color}; }}
.block-container {{ padding-top: 0 !important; }}
.container {{ max-width: 1200px; margin: auto; padding: 40px; }}
a {{ text-decoration: none !important; color: {font_color}; }}

.top-nav {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    margin-top: 40px !important;  /* ← 더 많이 띄움 */
    background-color: {nav_bg};
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}}
.nav-left {{ display: flex; align-items: center; gap: 60px; }}
.top-nav .nav-left > div:first-child a {{
    color: #000 !important;
    font-size: 28px;
    font-weight: bold;
}}
.nav-menu {{
    display: flex;
    gap: 36px;
    font-size: 18px;
    font-weight: 600;
}}
.nav-menu div a {{
    color: #000 !important;
    transition: all 0.2s ease;
}}
.nav-menu div:hover a {{
    color: #FF9330 !important;
}}
.profile-group {{ display: flex; gap: 16px; align-items: center; }}
.profile-icon {{
    background-color: #888;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    cursor: pointer;
}}

.folder-card {{
    background-color: {card_bg};
    border-radius: 14px;
    padding: 1.5rem;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
    text-align: center;
    transition: 0.3s ease;
    margin-bottom: 1rem;
}}
.folder-card:hover {{
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    transform: translateY(-2px);
}}
.folder-title {{
    margin-top: 0.8rem;
    font-weight: bold;
    font-size: 18px;
}}

header {{ display: none !important; }}
::selection {{ background: #FF9330; color: white; }}
label, .stTextInput label, .stTextArea label, .stSelectbox label {{
    color: {label_color} !important; font-weight: 600;
}}
{dark_input_css}
</style>
""", unsafe_allow_html=True)

# ===== 상단 헤더 (메인페이지와 100% 동일) =====
st.markdown(f"""
<div class="top-nav">
  <div class="nav-left">
    <div style="font-size:28px; font-weight:bold;">
      <a href="/" target="_self">🐾 딸깍공</a>
    </div>
    <div class="nav-menu">
      <div><a href="/"   target="_self">메인페이지</a></div>
      <div><a href="/main"   target="_self">공부 시작</a></div>
      <div><a href="/ocr_paddle"       target="_self">필기</a></div>
      <div><a href="/folder_page"   target="_self">저장폴더</a></div>
      <div><a href="/quiz"       target="_self">퀴즈</a></div>
      <div><a href="/report"     target="_self">리포트</a></div>
      <div><a href="/ranking"       target="_self">랭킹</a></div>
    </div>
  </div>
  <div class="profile-group">
    <div class="profile-icon" title="내 프로필"></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ===== 본문 컨테이너 시작 =====
st.markdown('<div class="container">', unsafe_allow_html=True)

st.subheader("📁 저장할 폴더에 메모를 입력하세요")

folder_items = [
    {"name": "필기 폴더", "img": "cute1.png"},
    {"name": "오답 폴더", "img": "cute2.png"},
    {"name": "리포트 폴더", "img": "cute3.png"},
    {"name": "메모장 폴더", "img": "cute4.png"},
]

if "folder_data" not in st.session_state:
    st.session_state.folder_data = {item["name"]: "" for item in folder_items}

cols = st.columns(4)
assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
for idx, folder in enumerate(folder_items):
    with cols[idx]:
        st.markdown('<div class="folder-card">', unsafe_allow_html=True)
        image_path = os.path.join(assets_dir, folder["img"])
        if os.path.exists(image_path):
            st.image(image_path, width=90)
        else:
            st.warning(f"이미지 없음: {folder['img']}")
        st.markdown(f"<div class='folder-title'>{folder['name']}</div>", unsafe_allow_html=True)
        user_input = st.text_input("", value=st.session_state.folder_data[folder["name"]], key=folder["name"])
        st.session_state.folder_data[folder["name"]] = user_input
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown(" ")
if st.button("💾 전체 저장하기"):
    st.success("📁 모든 폴더 내용이 저장되었습니다!")

st.markdown('</div>', unsafe_allow_html=True)
