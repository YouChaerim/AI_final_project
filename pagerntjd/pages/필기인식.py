# pages/필기인식.py
import streamlit as st
import os
import base64
from paddleocr import PaddleOCR
from openai import OpenAI

# ─── 페이지 설정 ───
st.set_page_config(
    page_title="딸깍공 - PDF 인식(요약)",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── 다크모드 상태 가져오기 ───
dark_mode = st.session_state.get("dark_mode", False)

# ─── CSS 스타일 ───
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body {{
    font-family: 'Noto Sans KR', sans-serif;
    background-color: {"#1E1E1E" if dark_mode else "#FAFAFA"};
    color: {"#FFFFFF" if dark_mode else "#333"};
    zoom: 1.05;
    margin: 0;
}}
.stApp {{ background-color: {"#1E1E1E" if dark_mode else "#FAFAFA"}; }}
.block-container {{ padding-top: 0 !important; }}
.container {{ max-width: 1200px; margin: auto; padding: 40px; }}
a {{ text-decoration: none !important; color: {"#FFF" if dark_mode else "#333"}; }}

/* 입력 박스 */
[data-baseweb="select"] > div,
input[type="number"],
textarea,
input[type="text"] {{
    background-color: {"#2C2C2E" if dark_mode else "white"} !important;
    color: #FFFFFF !important;
    border: 1px solid #555 !important;
}}

/* 상단 네비 */
.top-nav {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    margin-top: -40px !important;
    background-color: rgba(255, 255, 255, 0.05);
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}}
.nav-left {{ display: flex; align-items: center; gap: 60px; }}
.top-nav .nav-left > div:first-child a {{
    color: {"#FFF" if dark_mode else "#000"} !important;
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
    color: {"#FFF" if dark_mode else "#000"} !important;
    transition: all 0.2s ease;
}}
.nav-menu div:hover a,
.nav-menu .active a {{
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
header, #MainMenu, [data-testid="stSidebar"], button[title="사이드바 토글"] {{
    display: none !important;
}}
.stButton>button {{
    background-color: #FF9330;
    color: white;
    font-weight: 700;
    padding: 12px 36px;
    border-radius: 12px;
    font-size: 18px;
    margin-top: 20px;
}}
.stButton>button:hover {{ background-color: #e07e22; }}
</style>
""", unsafe_allow_html=True)

# ─── Base64 이미지 로더 ───
def load_base64(filename):
    ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
    path = os.path.join(ASSETS_DIR, filename)
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ─── 상단 네비 ───
st.markdown('<div class="container">', unsafe_allow_html=True)
st.markdown("""
<div class="top-nav">
  <div class="nav-left">
    <div><a href="/mainpage" target="_self">🐾 딸깍공</a></div>
    <div class="nav-menu">
      <div><a href="/mainpage" target="_self">메인페이지</a></div>
      <div><a href="/공부_시작" target="_self">공부 시작</a></div>
      <div class="active"><a href="/필기" target="_self">필기</a></div>
      <div><a href="/저장폴더" target="_self">저장폴더</a></div>
      <div><a href="/퀴즈" target="_self">퀴즈</a></div>
      <div><a href="/리포트" target="_self">리포트</a></div>
      <div><a href="/랭킹" target="_self">랭킹</a></div>
    </div>
  </div>
  <div class="profile-group">
    <div class="profile-icon" title="내 프로필"></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── 본문 기능 ───
st.title("📄 PDF 인식 및 요약")

uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])
if uploaded_file:
    tmp_path = "temp.pdf"
    with open(tmp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    ocr_model = PaddleOCR(use_angle_cls=True, lang="korean")
    ocr_results = ocr_model.ocr(tmp_path, cls=True)
    extracted_text = "\n".join([line[1][0] for page in ocr_results for line in page])

    st.subheader("🔍 인식된 텍스트")
    st.markdown(f"""
    <textarea rows="10" style="
        width: 100%;
        background-color: {'#2C2C2E' if dark_mode else 'white'};
        color: {'white' if dark_mode else 'black'};
        border: 1px solid #555;
        border-radius: 10px;
        padding: 10px;
    " readonly>{extracted_text}</textarea>
    """, unsafe_allow_html=True)

    if st.button("🧠 요약 생성"):
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"다음 텍스트를 요약해주세요:\n{extracted_text}"}],
            temperature=0.5,
        )
        summary = resp.choices[0].message.content
        st.subheader("📌 요약 결과")
        st.write(summary)

# ─── 닫기 ───
st.markdown("</div>", unsafe_allow_html=True)