# pages/필기인식.py
import streamlit as st
import os
import base64
from paddleocr import PaddleOCR
from openai import OpenAI

# ─── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="딸깍공 - PDF 인식(요약)",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── CSS 스타일 (헤더, 사이드바 제거 등) ─────────────────────────────────────────
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
a { text-decoration: none !important; }

.top-nav {
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px 0; margin-top: 8px;
    background-color: rgba(255, 255, 255, 0.9);
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.nav-left { display: flex; align-items: center; gap: 60px; }
.nav-menu { display: flex; gap: 36px; font-size: 18px; font-weight: 600; }
.nav-menu div a { color: #333; transition: all 0.2s ease; }
.nav-menu .active a, .nav-menu div:hover a { color: #FF9330; }
.profile-group { display: flex; gap: 16px; align-items: center; }
.profile-icon {
    background-color: #888;
    width: 36px; height: 36px;
    border-radius: 50%;
    cursor: pointer;
}

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

# ─── Base64 이미지 로더 (헤더 아이콘 등) ────────────────────────────────────────
def load_base64(filename):
    ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
    path = os.path.join(ASSETS_DIR, filename)
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ─── 전체 컨테이너 시작 ─────────────────────────────────────────────────────────
st.markdown('<div class="container">', unsafe_allow_html=True)

# 헤더 영역
st.markdown(f"""
<div class="top-nav">
    <div class="nav-left">
        <div style="font-size: 28px; font-weight: bold;">
            <a href="/mainpage" style="color: #333;">🐾 딸깍공</a>
        </div>
        <div class="nav-menu">
            <div><a href="/mainpage">메인페이지</a></div>
            <div><a href="/공부_시작">공부 시작</a></div>
            <div class="active"><a href="/필기">필기</a></div>
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

# ─── 본문 ──────────────────────────────────────────────────────────────────────
st.title("PDF 인식 및 요약")

uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])
if uploaded_file:
    # 임시 저장
    tmp_path = "temp.pdf"
    with open(tmp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # OCR
    ocr_model = PaddleOCR(use_angle_cls=True, lang="korean")
    ocr_results = ocr_model.ocr(tmp_path, cls=True)
    extracted_text = "\n".join([line[1][0] for page in ocr_results for line in page])

    st.subheader("인식된 텍스트")
    st.text_area("", extracted_text, height=200)

    # 요약 버튼
    if st.button("요약 생성"):
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":f"다음 텍스트를 요약해주세요:\n{extracted_text}"}],
            temperature=0.5,
        )
        summary = resp.choices[0].message.content
        st.subheader("요약 결과")
        st.write(summary)

# ─── 컨테이너 종료 ─────────────────────────────────────────────────────────────
st.markdown("</div>", unsafe_allow_html=True)
