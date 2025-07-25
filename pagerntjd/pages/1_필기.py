import streamlit as st
import os
import base64

# ✅ 페이지 설정
st.set_page_config(page_title="딸깍공 - 필기", layout="wide", initial_sidebar_state="collapsed")

# ✅ Base64 이미지 로더 함수
def load_base64(filename):
    ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
    path = os.path.join(ASSETS_DIR, filename)
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ✅ 스타일 (네비게이션 → 같은 탭 이동용 onclick)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');

html, body {
    font-family: 'Noto Sans KR', sans-serif;
    background-color: #FAFAFA;
    color: #333;
    zoom: 1.10;
    margin-top: 0px;
}
.stApp { background-color: #FAFAFA; }
.block-container { padding-top: 0rem !important; }
.container { max-width: 1200px; margin: auto; padding: 0px 40px 40px 40px; }

/* 링크 밑줄 제거 */
a { text-decoration: none !important; }

/* 헤더 영역 */
.top-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    margin-top: 8px;
    background-color: rgba(255,255,255,0.9);
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.nav-left { display: flex; align-items: center; gap: 60px; }
.nav-menu { display: flex; gap: 36px; font-size: 18px; font-weight: 600; }
.nav-menu .nav-item {
    color: #333;
    cursor: pointer;
    transition: color 0.2s ease;
}
.nav-menu .nav-item:hover,
.nav-menu .active {
    color: #FF9330;
}
.profile-group { display: flex; gap: 16px; align-items: center; }
.profile-icon {
    background-color: #888;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    cursor: pointer;
}

/* 카드 UI */
.icon-container {
    display: flex;
    justify-content: center;
    gap: 70px;
    margin-top: 80px;
}
.icon-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 240px;
    height: 240px;
    border: 1px solid #eee;
    border-radius: 20px;
    padding: 22px;
    background-color: #fff;
    box-shadow: 1px 1px 10px rgba(0,0,0,0.04);
    cursor: pointer;
    transition: all 0.2s ease-in-out;
}
.icon-card:hover {
    background-color: #f9f9f9;
    transform: scale(1.04);
}
.icon-card img {
    height: 88px;
    margin-bottom: 16px;
}
.icon-card div {
    font-size: 17px;
    font-weight: 500;
    color: #111;
}

/* 상단 UI 완전 제거 */
[data-testid="collapsedControl"],
[data-testid="stSidebar"] {
    display: none !important;
}
header [data-testid="stDeployButton"],
header [data-testid="baseButton-headerMenu"],
header > div:first-child {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ✅ 컨테이너 시작
st.markdown('<div class="container">', unsafe_allow_html=True)

# ✅ 헤더 영역 (onclick 으로 같은 탭에서 이동)
st.markdown("""
<div class="top-nav">
    <div class="nav-left">
        <div style="font-size:28px; font-weight:bold;" onclick="window.location.href='/mainpage'">
            🐾 딸깍공
        </div>
        <div class="nav-menu">
            <div class="nav-item" onclick="window.location.href='/mainpage'">메인페이지</div>
            <div class="nav-item" onclick="window.location.href='/공부_시작'">공부 시작</div>
            <div class="nav-item active" onclick="window.location.href='/필기'">필기</div>
            <div class="nav-item" onclick="window.location.href='/저장폴더'">저장폴더</div>
            <div class="nav-item" onclick="window.location.href='/퀴즈'">퀴즈</div>
            <div class="nav-item" onclick="window.location.href='/리포트'">리포트</div>
            <div class="nav-item" onclick="window.location.href='/랭킹'">랭킹</div>
        </div>
    </div>
    <div class="profile-group">
        <div class="profile-icon" title="내 프로필"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ✅ 카드 UI
st.markdown(f"""
<div class="icon-container">
    <div class="icon-card" onclick="window.location.href='/필기인식'">
        <img src="data:image/png;base64,{load_base64('pen.png')}">
        <div>PDF인식(요약)</div>
    </div>
    <div class="icon-card" onclick="window.location.href='/저장폴더'">
        <img src="data:image/png;base64,{load_base64('icon_folder.png')}">
        <div>폴더</div>
    </div>
    <div class="icon-card" onclick="window.location.href='/퀴즈'">
        <img src="data:image/png;base64,{load_base64('quiz.png')}">
        <div>퀴즈</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ✅ 컨테이너 종료
st.markdown("</div>", unsafe_allow_html=True)
