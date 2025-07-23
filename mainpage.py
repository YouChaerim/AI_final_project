import streamlit as st

# ====== 세션 상태 ======
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

def toggle_dark_mode():
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

# ====== 테마 설정 ======
if st.session_state.dark_mode:
    bg_color = "#1c1c1e"
    font_color = "#f2f2f7"
    card_bg = "#2c2c2e"
    hover_bg = "#3a3a3c"
    nav_bg = "#2c2c2e"
    dark_orange = "#FF9330"
else:
    bg_color = "#FAFAFA"
    font_color = "#333"
    card_bg = "white"
    hover_bg = "#F5F5F5"
    nav_bg = "rgba(255, 255, 255, 0.9)"
    dark_orange = "#FF9330"

# ====== 페이지 설정 ======
st.set_page_config(layout="wide", page_title="딸깍공 메인페이지", initial_sidebar_state="expanded")

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
    overflow: hidden;
}}
.block-container {{
    padding-top: 0rem !important;
}}
.container {{
    max-width: 1200px;
    margin: auto;
    padding: 0px 40px 40px 40px;
}}
a {{ text-decoration: none !important; color: inherit; }}

.top-nav {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px 0; margin-top: 0px;
    background-color: {nav_bg};
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}}
.nav-left {{ display: flex; align-items: center; gap: 60px; }}
.nav-menu {{
    display: flex; gap: 36px; font-size: 18px; font-weight: 600;
    font-family: 'Noto Sans KR', sans-serif; color: {font_color};
}}
.nav-menu div {{ padding-bottom: 10px; }}
.nav-menu div a {{ color: {font_color}; transition: all 0.2s ease; }}
.nav-menu div:hover a {{ color: #FF9330; }}
.profile-group {{ display: flex; gap: 16px; align-items: center; }}
.profile-icon {{
    background-color: #ccc; width: 36px; height: 36px; border-radius: 50%; cursor: pointer;
}}
.main-box {{
    background-color: {dark_orange}; border-radius: 14px; padding: 40px 0;
    text-align: center; color: white; font-size: 28px; font-weight: bold;
    margin-bottom: 16px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}}
.main-btn {{
    margin-top: 24px; padding: 12px 32px; background: white; color: black;
    font-weight: bold; border-radius: 8px; font-size: 17px; border: none;
    transition: background 0.2s;
}}
.main-btn:hover {{ background-color: #f0f0f0; color: #FF9330; cursor: pointer; }}
.right-card {{
    background: {card_bg}; border-radius: 10px; padding: 18px 20px; margin-bottom: 14px;
    font-size: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); color: {font_color};
}}
.icon-grid {{
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 12px; margin-top: 0px;
}}
.icon-box {{
    background: {card_bg}; border-radius: 10px; padding: 14px 8px; text-align: center;
    font-size: 17px; color: {font_color}; font-weight: 500;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03); height: 70px;
    display: flex; flex-direction: column; justify-content: center;
    transition: all 0.2s ease;
}}
.icon-box:hover {{
    background-color: {hover_bg}; font-weight: 600; cursor: pointer;
}}
.toggle-btn {{
    position: fixed; bottom: 12px; right: 12px;
    background: #444; color: white; font-size: 13px;
    padding: 6px 12px; border-radius: 20px;
    cursor: pointer; opacity: 0.9;
}}
.toggle-btn:hover {{ background: #666; }}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="container">', unsafe_allow_html=True)

# ====== 네비게이션 바 ======
st.markdown(f"""
<div class="top-nav">
    <div class="nav-left">
        <div style="font-size: 28px; font-weight: bold; color: {font_color};">🐾 딸깍공</div>
        <div class="nav-menu">
            <div><a href="#">메인페이지</a></div>
            <div><a href="#">공부 시작</a></div>
            <div><a href="#">필기</a></div>
            <div><a href="#">저장폴더</a></div>
            <div><a href="#">퀴즈</a></div>
            <div><a href="#">리포트</a></div>
            <div><a href="#">랭킹</a></div>
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
        <div><button class="main-btn">공부 시작</button></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="icon-grid">
        <div class="icon-box">✏️<br>필기</div>
        <div class="icon-box">📁<br>저장폴더</div>
        <div class="icon-box">❓<br>퀴즈</div>
        <div class="icon-box">📄<br>리포트</div>
        <div class="icon-box">📊<br>랭킹</div>
        <div class="icon-box">🗒️<br>투두리스트</div>
        <div class="icon-box">📒<br>메모장</div>
        <div class="icon-box" onclick="window.location.reload()">🌗<br>다크모드</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="right-card"><b>📝 오늘 할 일</b><br>☑ 수학 예제 풀기<br>☑ 영단어 암기</div>
    <div class="right-card"><b>🗒 빠른 메모</b><br>중간고사 다음 주!</div>
    <div class="right-card"><b>🏅 최근 랭킹</b><br>user123 · 5위</div>
    <div class="right-card"><b>⏱ 오늘 공부시간</b><br>2시간</div>
    """, unsafe_allow_html=True)

# ====== 컨테이너 종료 ======
st.markdown("</div>", unsafe_allow_html=True)

# ====== 다크모드 하단 버튼 ======
st.markdown(f"""
<div class="toggle-btn" onclick="window.location.href='?dark_mode={'false' if st.session_state.dark_mode else 'true'}'">
🌗 다크모드 (하단 토글)
</div>
""", unsafe_allow_html=True)