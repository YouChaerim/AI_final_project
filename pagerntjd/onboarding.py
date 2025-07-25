# pages/onboarding.py
import streamlit as st

# ===== 페이지 설정 =====
st.set_page_config(layout="centered", page_title="딸깍공 온보딩")

# ===== 기본 UI 숨기기 =====
st.markdown("""
<style>
[data-testid="stSidebar"],
[data-testid="stSidebarNav"],
[data-testid="stToolbar"] {
    display: none !important;
}
.block-container {
    padding-top: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ===== 글로벌 폰트 & 배경 =====
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body {
    font-family: 'Noto Sans KR', sans-serif;
    background-color: #FFF8F0;
}
</style>
""", unsafe_allow_html=True)

# ===== 헤더 · 카드 · 버튼 스타일 =====
st.markdown("""
<style>
.title {
    font-size: 28px;
    font-weight: bold;
    text-align: center;
    margin-top: 40px;
    margin-bottom: 20px;
    color: #222;
}
.card-container {
    display: flex;
    justify-content: center;
    gap: 36px;
    margin: 20px 0 20px 0;
}
.card {
    background-color: white;
    border-radius: 18px;
    padding: 30px 20px;
    width: 280px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    text-align: center;
}
.circle {
    background-color: #FFA741;
    color: white;
    border-radius: 50%;
    width: 36px;
    height: 36px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    margin-bottom: 14px;
}
.card-title {
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 8px;
}
.card-desc {
    font-size: 16px;
    color: #666;
    line-height: 1.6;
}
.start-btn {
    display: flex;
    justify-content: center;
    margin-top: 30px;
}
.start-btn a {
    text-decoration: none;
}
button.start {
    background-color: #FFA741;
    border: none;
    padding: 18px 48px;
    border-radius: 14px;
    font-size: 22px;
    font-weight: bold;
    color: white;
    cursor: pointer;
    transition: 0.2s;
}
button.start:hover {
    background-color: #FF9329;
}
</style>
""", unsafe_allow_html=True)

# ===== 온보딩 콘텐츠 =====
st.markdown('<div class="title">🐾 딸깍공에 오신 걸 환영해요!</div>', unsafe_allow_html=True)
st.markdown("""
<div class="card-container">
  <div class="card">
    <div class="circle">1</div>
    <div class="card-title">공부 목표 설정</div>
    <div class="card-desc">목표를 도달하며<br>성취감을 느껴요!</div>
  </div>
  <div class="card">
    <div class="circle">2</div>
    <div class="card-title">뽀모도로 기법 체험</div>
    <div class="card-desc">25분 공부하고 5분 쉬며<br>몰입해요!</div>
  </div>
  <div class="card">
    <div class="circle">3</div>
    <div class="card-title">피드백리포트 받아보기</div>
    <div class="card-desc">리포트를 보며<br>공부 패턴을 분석해요!</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ===== 시작하기 버튼 (같은 탭 이동) =====
st.markdown("""
<div class="start-btn">
  <a href="/mainpage" target="_self">
    <button class="start">시작하기</button>
  </a>
</div>
""", unsafe_allow_html=True)
