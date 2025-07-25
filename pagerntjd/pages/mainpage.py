import streamlit as st
import json
import os

# ====== 세션 상태 초기화 ======
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

# ====== 다크모드 설정 불러오기 ======
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = st.session_state.user_data.get("dark_mode", False)

# ====== 테마 색상 설정 ======
if st.session_state.dark_mode:
    bg_color = "#1C1C1E"
    font_color = "#F2F2F2"
    card_bg = "#2C2C2E"
    hover_bg = "#3A3A3C"
    nav_bg = "#2C2C2E"
    dark_orange = "#FF9330"
    label_color = "white"
else:
    bg_color = "#FAFAFA"
    font_color = "#333"
    card_bg = "white"
    hover_bg = "#F5F5F5"
    nav_bg = "rgba(255, 255, 255, 0.9)"
    dark_orange = "#FF9330"
    label_color = font_color

# ====== 페이지 설정 ======
st.set_page_config(layout="wide", page_title="딸깍공 메인페이지", initial_sidebar_state="collapsed")

# ====== 스타일 지정 ======
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');

html, body {{
    background-color: {bg_color};
    color: {font_color};
    font-family: 'Noto Sans KR', sans-serif;
    zoom: 1.10;
    margin-top: 0px;
}}
.stApp {{ background-color: {bg_color}; }}
.block-container {{ padding-top: 0rem !important; }}
.container {{ max-width: 1200px; margin: auto; padding: 0px 40px 40px 40px; }}
a {{ text-decoration: none !important; color: {font_color}; }}

.top-nav {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    margin-top: 8px;
    background-color: {nav_bg};
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}}
.nav-left {{ display: flex; align-items: center; gap: 60px; }}
.nav-menu {{ display: flex; gap: 36px; font-size: 18px; font-weight: 600; }}
.nav-menu div a {{ color: {font_color}; transition: all 0.2s ease; }}
.nav-menu div:hover a {{ color: #FF9330; }}
.profile-group {{ display: flex; gap: 16px; align-items: center; }}
.profile-icon {{ background-color: #888; width: 36px; height: 36px; border-radius: 50%; cursor: pointer; }}

.main-box {{
    background-color: {dark_orange};
    border-radius: 14px;
    padding: 40px 0;
    text-align: center;
    color: white;
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 16px;
}}
.main-btn {{
    margin-top: 24px;
    padding: 12px 32px;
    background: white;
    color: black;
    font-weight: bold;
    border-radius: 8px;
    font-size: 17px;
    border: none;
}}
.right-card {{
    background: {card_bg};
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 14px;
    font-size: 15px;
    color: {font_color};
}}
.icon-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-top: 0px;
}}
.icon-box {{
    background: {card_bg};
    border-radius: 10px;
    padding: 14px 8px;
    text-align: center;
    font-size: 17px;
    color: {font_color};
    font-weight: 500;
    height: 70px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}}
.icon-box:hover {{ background-color: {hover_bg}; cursor: pointer; }}
header {{ display: none !important; }}
::selection {{ background: #FF9330; color: white; }}
label, .stTextInput label, .stTextArea label, .stSelectbox label {{
    color: {label_color} !important;
    font-weight: 600;
}}
</style>
""", unsafe_allow_html=True)

# ====== 본문 컨테이너 시작 ======
st.markdown('<div class="container">', unsafe_allow_html=True)

# ====== 네비게이션 바 ======
st.markdown(f"""
<div class="top-nav">
    <div class="nav-left">
        <div style="font-size: 28px; font-weight: bold;">
            <a href="/mainpage" style="color: {font_color};">🐾 딸깍공</a>
        </div>
        <div class="nav-menu">
            <div><a href="/mainpage">메인페이지</a></div>
            <div><a href="/공부_시작">공부 시작</a></div>
            <div><a href="/필기">필기</a></div>
            <div><a href="/저장폴더">저장폴더</a></div>
            <div><a href="/퀴즈">퀴즈</a></div>
            <div><a href="/리포트">리포트</a></div>
            <div><a href="/랭킹">랭킹</a></div>
        </div>
    </div>
    <div class="profile-group">
        <div class="profile-icon" title="내 프로필"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ====== 메인 콘텐츠 ======
col1, col2 = st.columns([2.5, 1])
with col1:
    st.markdown(f"""
    <div class="main-box">
        오늘 공부 시작하기
        <div><a href="/공부_시작"><button class="main-btn">공부 시작</button></a></div>
    </div>
    <div class="icon-grid">
        <a href="/공부_시작"><div class="icon-box">📖<br>공부 시작</div></a>
        <a href="/필기"><div class="icon-box">✏️<br>필기</div></a>
        <a href="/저장폴더"><div class="icon-box">📁<br>저장폴더</div></a>
        <a href="/퀴즈"><div class="icon-box">❓<br>퀴즈</div></a>
        <a href="/리포트"><div class="icon-box">📄<br>리포트</div></a>
        <a href="/랭킹"><div class="icon-box">📊<br>랭킹</div></a>
        <a href="/투두리스트"><div class="icon-box">🗒️<br>투두리스트</div></a>
        <a href="/메모장"><div class="icon-box">📒<br>메모장</div></a>
        <a href="/색변경"><div class="icon-box">🎨<br><b>색변경</b></div></a>
    </div>
    """, unsafe_allow_html=True)

with col2:
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False

    if not st.session_state.edit_mode:
        st.markdown("<div class='right-card'>📌 <b>오늘 할 일</b><br>" + st.session_state.user_data.get("todo", "") + "</div>", unsafe_allow_html=True)
        st.markdown("<div class='right-card'>🗓 <b>빠른 메모</b><br>" + st.session_state.user_data.get("memo", "") + "</div>", unsafe_allow_html=True)
        hour = int(st.session_state.user_data.get("study_hour", 1))
        minute = int(st.session_state.user_data.get("study_minute", 0))
        st.markdown(f"<div class='right-card'>⏰ <b>오늘 공부시간</b><br>{hour}시간 {minute}분</div>", unsafe_allow_html=True)
        if st.button("✏️ 변경하기"):
            st.session_state.edit_mode = True
            st.rerun()
    else:
        with st.form(key="save_form"):
            todo = st.text_area("📝 오늘 할 일", value=st.session_state.user_data.get("todo", ""))
            memo = st.text_area("🗒 빠른 메모", value=st.session_state.user_data.get("memo", ""))
            hour = st.selectbox("공부 시간(시간)", list(range(0, 13)), index=st.session_state.user_data.get("study_hour", 1))
            minute = st.selectbox("공부 시간(분)", list(range(0, 61)), index=st.session_state.user_data.get("study_minute", 0))
            submitted = st.form_submit_button("저장하기")
            if submitted:
                st.session_state.user_data = {
                    "todo": todo,
                    "memo": memo,
                    "study_hour": hour,
                    "study_minute": minute,
                    "dark_mode": st.session_state.dark_mode
                }
                with open("user_data.json", "w", encoding="utf-8") as f:
                    json.dump(st.session_state.user_data, f, ensure_ascii=False, indent=2)
                st.session_state.edit_mode = False
                st.rerun()

# ====== 컨테이너 종료 ======
st.markdown("</div>", unsafe_allow_html=True)

# ====== 다크모드 토글 버튼 ======
if st.button("🌗 다크모드 전환", key="dark_toggle", help="배경을 어둡게 또는 밝게 전환합니다.", type="primary"):
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.session_state.user_data["dark_mode"] = st.session_state.dark_mode
    with open("user_data.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.user_data, f, ensure_ascii=False, indent=2)
    st.rerun()
