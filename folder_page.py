import streamlit as st
import os

# ✅ 페이지 설정
st.set_page_config(page_title="딸깍공 - 폴더 저장", layout="wide", initial_sidebar_state="collapsed")

# ✅ 스타일 정의 (중앙정렬 + 확대 + 여백제거 + 메뉴 제거)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');

/* 기본 스타일 */
html, body {
    font-family: 'Noto Sans KR', sans-serif;
    background-color: #FAFAFA;
    color: #333;
    margin: 0;
    zoom: 1; /* 확대 해제 */
}

/* 상단 메뉴, deploy, header 제거 */
header, #MainMenu, footer {
    display: none !important;
}

/* 여백 제거 */
.block-container, .stApp > div:first-child {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

/* 중앙 정렬된 전체 컨테이너 */
.container {
    max-width: 1080px;
    margin: auto;
    padding: 40px 0px 60px 0px;
    display: flex;
    flex-direction: column;
    align-items: center;
}

/* 상단 네비게이션 */
.header-container {
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: white;
    padding: 1.2rem 2rem;
    border-bottom: 1px solid #e0e0e0;
    width: 100%;
}

.logo-text {
    font-size: 30px;
    font-weight: 900;
}

.nav-menu {
    display: flex;
    gap: 2rem;
    font-size: 18px;
    font-weight: 500;
    margin-left: 3rem;
}

.nav-menu a {
    color: #333;
    text-decoration: none !important;
}

/* 폴더 카드 스타일 */
.folder-card {
    background-color: white;
    border-radius: 14px;
    padding: 1.5rem;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
    text-align: center;
    transition: 0.3s ease;
}

.folder-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    transform: translateY(-2px);
}

.folder-title {
    margin-top: 0.8rem;
    font-weight: bold;
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)

# ✅ 상단 헤더
st.markdown("""
<div class="header-container">
    <div class="logo-text">🐾 딸깍공</div>
    <div class="nav-menu">
        <a href="/mainpage" target="_self">메인페이지</a>
        <a href="/공부_시작" target="_self">공부 시작</a>
        <a href="/필기" target="_self">필기</a>
        <a href="/저장폴더" target="_self">저장폴더</a>
        <a href="/퀴즈" target="_self">퀴즈</a>
        <a href="/리포트" target="_self">리포트</a>
        <a href="/랭킹" target="_self">랭킹</a>
    </div>
</div>
""", unsafe_allow_html=True)

# ✅ 세션 초기화
if "folder_data" not in st.session_state:
    st.session_state.folder_data = {
        "필기 폴더": "",
        "오답 폴더": "",
        "리포트 폴더": "",
        "메모장 폴더": ""
    }

# ✅ 중앙정렬 콘텐츠 시작
st.markdown('<div class="container">', unsafe_allow_html=True)
st.markdown("### 📁 저장할 폴더 입력")

# ✅ 폴더 항목 정의
folder_items = [
    {"name": "필기 폴더", "img": "cute1.png"},
    {"name": "오답 폴더", "img": "cute2.png"},
    {"name": "리포트 폴더", "img": "cute3.png"},
    {"name": "메모장 폴더", "img": "cute4.png"},
]

cols = st.columns(4)
for idx, folder in enumerate(folder_items):
    with cols[idx]:
        st.markdown('<div class="folder-card">', unsafe_allow_html=True)
        st.image(f"images/{folder['img']}", width=90)
        st.markdown(f"<div class='folder-title'>{folder['name']}</div>", unsafe_allow_html=True)
        user_input = st.text_input("", value=st.session_state.folder_data[folder["name"]], key=folder["name"])
        st.session_state.folder_data[folder["name"]] = user_input
        st.markdown('</div>', unsafe_allow_html=True)

# ✅ 저장 버튼ㅇㅇㅇㅇ
st.markdown(" ")
if st.button("💾 전체 저장하기"):
    st.success("📁 모든 폴더 내용이 저장되었습니다!")

st.markdown('</div>', unsafe_allow_html=True)
