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

# ====== 메인페이지 스타일 그대로 적용 (헤더 기준) ======
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');

html, body {{
    font-family: 'Noto Sans KR', sans-serif;
    background-color: #FAFAFA;
    color: #333;
    zoom: 1.10;
    margin: 0;
}}
.stApp {{ background-color: #FAFAFA; }}
.block-container {{ padding-top: 0 !important; }}
.container {{ max-width: 1200px; margin: auto; padding: 40px; }}

a {{ text-decoration: none !important; color: #333; }}

/* ===== 상단 네비게이션 바 ===== */
.top-nav {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    margin-top: -40px !important;
    background-color: rgba(255,255,255,0.9);
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}}
.nav-left {{ display: flex; align-items: center; gap: 60px; }}
.top-nav .nav-left > div:first-child a {{
    color: #000 !important;
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
    color: #000 !important;
    transition: all 0.2s ease;
}}
.nav-menu div:hover a {{
    color: #FF9330 !important;
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
/* ── 아래 기존 카드/아이콘 스타일은 유지 ── */
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
    background-color: #fff;
    box-shadow: 1px 1px 10px rgba(0,0,0,0.04);
    transition: all 0.2s ease-in-out;
}}
.icon-card:hover {{
    background-color: #f9f9f9;
    transform: scale(1.04);
}}
.icon-card img {{
    height: 88px;
    margin-bottom: 16px;
}}
.icon-card div {{
    font-size: 17px;
    font-weight: 500;
    color: #111;
}}
[data-testid="collapsedControl"],
[data-testid="stSidebar"] {{
    display: none !important;
}}
header [data-testid="stDeployButton"],
header [data-testid="baseButton-headerMenu"],
header > div:first-child {{
    display: none !important;
}}
</style>
""", unsafe_allow_html=True)

# ✅ 컨테이너 시작
st.markdown('<div class="container">', unsafe_allow_html=True)

# ✅ (메인페이지와 100% 동일하게) 상단 네비게이션 바
st.markdown("""
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

# ✅ 아이콘 카드 3개 정중앙 정렬 (기존 그대로)
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
