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

if "study_hour" not in st.session_state.user_data:
    st.session_state.user_data["study_hour"] = 0
if "study_minute" not in st.session_state.user_data:
    st.session_state.user_data["study_minute"] = 0

# ====== 다크모드 설정 불러오기 ======
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = st.session_state.user_data.get("dark_mode", False)

# ====== 테마 색상 설정 ======
if st.session_state.dark_mode:
    bg_color = "#1C1C1E"; font_color = "#F2F2F2"
    card_bg = "#2C2C2E"; hover_bg = "#3A3A3C"
    nav_bg = "#2C2C2E"; dark_orange = "#FF9330"; label_color = "white"
else:
    bg_color = "#FAFAFA"; font_color = "#333"
    card_bg = "white"; hover_bg = "#F5F5F5"
    nav_bg = "rgba(255, 255, 255, 0.9)"; dark_orange = "#FF9330"; label_color = font_color

st.set_page_config(
    layout="wide",
    page_title="딸깍공 메인페이지",
    initial_sidebar_state="collapsed"
)

# ====== 스타일 지정 ======
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
    margin-top: -40px !important;
    background-color: {nav_bg};
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    position: relative;
}}
.nav-left {{ display: flex; align-items: center; gap: 60px; }}
.top-nav .nav-left > div:first-child a {{ color: #000 !important; font-size: 28px; font-weight: bold; }}
.nav-menu {{ display: flex; gap: 36px; font-size: 18px; font-weight: 600; }}
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
.stLoginBtn button {{
    font-size: 17px !important;
    font-weight: 600 !important;
    color: #FFA500 !important;
    background: white !important;
    border-radius: 18px !important;
    padding: 8px 22px !important;
    border: 1.5px solid #FFA500 !important;
    transition: background 0.15s, color 0.15s;
    box-shadow: 0 1px 4px rgba(255,165,0,0.03);
    height: 36px;
    margin-left: 18px;
}}
.stLoginBtn button:hover {{
    background: #FFF5E5 !important;
    color: #FF9330 !important;
}}
.main-box {{
    background-color: {dark_orange};
    border-radius: 14px;
    padding: 90px 0 140px 0;   /* 높이 키움: 위, 아래 패딩 조절 */
    text-align: center;
    color: white;
    font-size: 36px;
    font-weight: bold;
    margin-bottom: 16px;
}}
.main-btn {{
    margin-top: 30px;
    padding: 16px 40px;
    background: white;
    color: black;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    font-size: 22px;
}}
.right-card {{
    background: {card_bg};
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 14px;
    font-size: 17px;
    color: {font_color};
}}
header {{ display: none !important; }}
::selection {{ background: #FF9330; color: white; }}
label, .stTextInput label, .stTextArea label, .stSelectbox label {{
    color: {label_color} !important; font-weight: 600;
}}
/* 버튼 간격 살짝 띄우기 */
.button-row > div {{ padding-right: 6px !important; }}
</style>
""", unsafe_allow_html=True)

# ====== 본문 컨테이너 시작 ======
st.markdown('<div class="container">', unsafe_allow_html=True)

# ====== 네비게이션 바 ======
st.markdown(f"""
<div class="top-nav">
  <div class="nav-left">
    <div><a href="/" target="_self">🐾 딸깍공</a></div>
    <div class="nav-menu">
      <div><a href="/" target="_self">메인페이지</a></div>
      <div><a href="/main" target="_self">공부 시작</a></div>
      <div><a href="/ocr_paddle" target="_self">필기</a></div>
      <div><a href="/folder_page" target="_self">저장폴더</a></div>
      <div><a href="/quiz" target="_self">퀴즈</a></div>
      <div><a href="/report" target="_self">리포트</a></div>
      <div><a href="/ranking" target="_self">랭킹</a></div>
    </div>
  </div>
  <div class="profile-group">
    <div class="profile-icon" title="내 프로필"></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ====== 네비게이션 바 오른쪽 끝에 Streamlit 버튼 ======
nav_login = st.container()
with nav_login:
    st.markdown(
        "<div class='stLoginBtn' style='position: absolute; top: 26px; right: 50px; z-index: 10;'></div>",
        unsafe_allow_html=True,
    )
    login_btn_col = st.columns([10, 1])[1]
    with login_btn_col:
        if st.button("로그인", key="go_login", help="로그인 페이지로 이동", use_container_width=True):
            st.switch_page("pages/9_login.py")

# ----- 메인 콘텐츠 -----
col1, col2 = st.columns([2.5, 1])
with col1:
    st.markdown(f"""
    <div class="main-box">
      오늘 공부 시작하기<br>
      <a href="/main" target="_self">
        <button class="main-btn">공부 시작</button>
      </a>
    </div>
    """, unsafe_allow_html=True)

with col2:
    if not st.session_state.get("edit_mode", False):
        st.markdown(
            f"<div class='right-card'>📌 <b>오늘 할 일</b><br>{st.session_state.user_data['todo']}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='right-card'>🗓 <b>빠른 메모</b><br>{st.session_state.user_data['memo']}</div>",
            unsafe_allow_html=True
        )
        h, m = st.session_state.user_data["study_hour"], st.session_state.user_data["study_minute"]
        st.markdown(
            f"<div class='right-card'>⏰ <b>오늘 공부시간</b><br>{h}시간 {m}분</div>",
            unsafe_allow_html=True
        )
        # "변경하기"와 "투두리스트" 버튼을 한 줄에 옆으로 배치
        btn_col1, btn_col2 = st.columns([1, 1])
        with btn_col1:
            if st.button("✏️ 변경하기", use_container_width=True):
                st.session_state.edit_mode = True
                st.rerun()
        with btn_col2:
            if st.button("🗒️ 투두리스트", use_container_width=True, help="투두리스트로 이동"):
                st.switch_page("/투두리스트")
    else:
        with st.form("save_form"):
            todo = st.text_area("📝 오늘 할 일", value=st.session_state.user_data["todo"])
            memo = st.text_area("🗒 빠른 메모", value=st.session_state.user_data["memo"])
            hour = st.selectbox("공부 시간(시간)", list(range(0,13)), index=st.session_state.user_data["study_hour"])
            minute = st.selectbox("공부 시간(분)", list(range(0,61)), index=st.session_state.user_data["study_minute"])
            if st.form_submit_button("저장하기"):
                st.session_state.user_data.update({
                    "todo": todo,
                    "memo": memo,
                    "study_hour": hour,
                    "study_minute": minute
                })
                with open("user_data.json", "w", encoding="utf-8") as f:
                    json.dump(st.session_state.user_data, f, ensure_ascii=False, indent=2)
                st.session_state.edit_mode = False
                st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

if st.button("🌗 다크모드 전환", key="dark_toggle"):
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.session_state.user_data["dark_mode"] = st.session_state.dark_mode
    with open("user_data.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.user_data, f, ensure_ascii=False, indent=2)
    st.rerun()
