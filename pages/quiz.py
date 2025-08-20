# pages/quiz_page.py  (파일명은 현재 페이지 이름에 맞게 사용하세요)
# -*- coding: utf-8 -*-
import streamlit as st
import openai
import json
import os
import re
import base64
from dotenv import load_dotenv

# === 다크모드 불러오기 ===
if "user_data" not in st.session_state:
    if os.path.exists("user_data.json"):
        with open("user_data.json", "r", encoding="utf-8") as f:
            st.session_state.user_data = json.load(f)
    else:
        st.session_state.user_data = {"dark_mode": False}

# 캐릭터 헤더용 기본 키 보강
ud = st.session_state.user_data
ud.setdefault("active_char", "rabbit")   # bear/cat/rabbit/shiba
ud.setdefault("owned_hats", [])          # 예: ["cap"]
ud.setdefault("equipped_hat", None)      # 예: "cap"

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = ud.get("dark_mode", False)

# === 페이지 설정 ===
st.set_page_config(page_title="딸깍공 퀴즈", layout="wide", initial_sidebar_state="collapsed")

# === 테마 색상 지정 (공통 헤더 규격에 맞춤) ===
if st.session_state.dark_mode:
    bg_color = "#1C1C1E"; font_color = "#F2F2F2"
    nav_bg = "#2C2C2E"; card_bg = "#2C2C2E"; hover_bg = "#3A3A3C"
    dark_orange = "#FF9330"; label_color = "white"
    nav_link = "#F2F2F2"  # 공통 헤더 메뉴 링크 색
else:
    bg_color = "#FAFAFA"; font_color = "#333"
    nav_bg = "rgba(255,255,255,0.9)"; card_bg = "white"; hover_bg = "#F5F5F5"
    dark_orange = "#FF9330"; label_color = font_color
    nav_link = "#000"      # 공통 헤더 메뉴 링크 색

# === 아바타 이미지 헬퍼 ===
def _resolve_assets_root():
    here = os.path.dirname(__file__)
    cands = [
        os.path.abspath(os.path.join(here, "assets")),
        os.path.abspath(os.path.join(here, "..", "assets")),
    ]
    for p in cands:
        if os.path.isdir(p):
            return p
    return cands[0]

ASSETS_ROOT = _resolve_assets_root()

def _to_data_uri(path: str) -> str:
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")

def get_char_image_uri(char_key: str, hat_id: str | None = None) -> str:
    """
    전용 파일 우선 탐색:
      - assets/items/hats/{char}{sep}{hat_id}.png
      - assets/characters/{char}{sep}{hat_id}.png
      - assets/characters/{char}.png
    sep ∈ {"", "_", "-"}  /  'shiba'는 'siba'도 자동 지원
    """
    keys = [char_key] + (["siba"] if char_key == "shiba" else [])
    cands = []
    if hat_id:
        for k in keys:
            for sep in ["", "_", "-"]:
                cands += [
                    os.path.join(ASSETS_ROOT, "items", "hats", f"{k}{sep}{hat_id}.png"),
                    os.path.join(ASSETS_ROOT, "characters", f"{k}{sep}{hat_id}.png"),
                ]
    for k in keys:
        cands.append(os.path.join(ASSETS_ROOT, "characters", f"{k}.png"))

    for p in cands:
        if os.path.exists(p):
            return _to_data_uri(p)

    return "data:image/svg+xml;utf8," \
           "<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'><text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text></svg>"

def current_avatar_uri() -> str:
    char_key = ud.get("active_char", "rabbit")
    hat_id = ud.get("equipped_hat")
    if hat_id and (hat_id in ud.get("owned_hats", [])):
        return get_char_image_uri(char_key, hat_id)
    return get_char_image_uri(char_key)

# === CSS 스타일 (공통 헤더 규격) ===
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');

html, body {{
    font-family: 'Noto Sans KR', sans-serif;
    background-color: {bg_color};
    color: {font_color};
    zoom: 1.10;  /* 공통 */
    margin: 0;
}}
.stApp {{ background-color: {bg_color}; }}
.block-container {{ padding-top: 0 !important; }}
.container {{ max-width: 1200px; margin: auto; padding: 40px; }}
a {{ text-decoration: none !important; color: {font_color}; }}

header, [data-testid="stSidebar"], [data-testid="stToolbar"], #MainMenu {{ display: none !important; }}
.stApp > header, .stApp > div:first-child {{
    margin-top: 0 !important;
    padding-top: 0 !important;
}}

/* ===== 상단 네비게이션 바 (공통 헤더) ===== */
.top-nav {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;                 /* 공통: 상단 패딩 */
    margin-top: 40px !important;     /* 공통: 위치 */
    background-color: {nav_bg};
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}}
.nav-left {{ display: flex; align-items: center; gap: 60px; }}  /* 공통 간격 */
.top-nav .nav-left > div:first-child a {{
    color: #000 !important;          /* 공통: 로고 텍스트 색 고정 */
    font-size: 28px;                 /* 공통 크기 */
    font-weight: bold;               /* 공통 볼드 */
}}
.nav-menu {{
    display: flex;
    gap: 36px;                       /* 공통 간격 */
    font-size: 18px;
    font-weight: 600;
}}
.nav-menu div a {{
    color: {nav_link} !important;    /* 라이트/다크 연동 */
    transition: all 0.2s ease;
}}
.nav-menu div:hover a {{ color: {dark_orange} !important; }}

/* 우측 프로필(동그라미도 살짝 왼쪽으로) */
.profile-group {{ display: flex; gap: 16px; align-items: center; margin-right: 12px; }}
.profile-icon {{
    width: 36px; height: 36px; border-radius: 50%;
    background: linear-gradient(135deg,#DDEFFF,#F8FBFF);
    overflow: hidden; display: flex; align-items: center; justify-content: center;
    box-shadow: 0 1px 2px rgba(0,0,0,0.06);
}}
.profile-icon img {{ width: 100%; height: 100%; object-fit: contain; image-rendering: auto; }}

/* 버튼 톤(기존 유지) */
.stButton>button {{
    background-color: {dark_orange};
    color: white;
    font-weight: 700;
    padding: 12px 36px;
    border-radius: 12px;
    font-size: 18px;
    margin-top: 20px;
}}
.stButton>button:hover {{ filter: brightness(0.95); }}

/* 다크모드 입력 필드 톤 (있으면 적용) */
{'''
[data-baseweb="select"] > div,
input[type="number"],
textarea,
input[type="text"] {
    background-color: #2C2C2E !important;
    color: #FFFFFF !important;
    border: 1px solid #555 !important;
}
''' if st.session_state.dark_mode else ''}

</style>
""", unsafe_allow_html=True)

# === 네비게이션 바 (헤더는 컨테이너 밖) ===
header_avatar_uri = current_avatar_uri()
st.markdown(f"""
<div class="top-nav">
  <div class="nav-left">
    <div><a href="/mainpage" target="_self">🐾 딸깍공</a></div>
    <div class="nav-menu">
      <div><a href="/mainpage" target="_self">메인페이지</a></div>
      <div><a href="/main" target="_self">공부 시작</a></div>
      <div><a href="/ocr_paddle" target="_self">PDF요약</a></div>
      <div><a href="/folder_page" target="_self">저장폴더</a></div>
      <div><a href="/quiz" target="_self">퀴즈</a></div>
      <div><a href="/report" target="_self">리포트</a></div>
      <div><a href="/ranking" target="_self">랭킹</a></div>
    </div>
  </div>
  <div class="profile-group">
    <div class="profile-icon" title="내 캐릭터"><img src="{header_avatar_uri}" alt="avatar"/></div>
  </div>
</div>
""", unsafe_allow_html=True)

# === 컨테이너 시작 (본문은 헤더와 분리) ===
st.markdown('<div class="container">', unsafe_allow_html=True)

# === OpenAI API 준비 ===
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("❌ OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다.")
    st.stop()
client = openai.OpenAI(api_key=api_key)

# === 세션 초기화 ===
for key in ["quiz_data", "user_answers", "confirmed", "wrong_indices", "chat_logs", "summary_log", "graded"]:
    if key not in st.session_state:
        st.session_state[key] = {} if key in ["user_answers", "confirmed", "wrong_indices", "chat_logs"] else [] if key == "quiz_data" else "" if key == "summary_log" else False

# === GPT 퀴즈 생성 함수 ===
def generate_quiz(content, count, qtype):
    if qtype != "모든 유형":
        type_clause = f"- 모든 문제 유형은 '{qtype}'로 구성해줘.\n"
    else:
        type_clause = "- 문제 유형은 객관식, 주관식, OX, 빈칸 중에서 무작위로 다양하게 섞어 구성해줘.\n"

    system_prompt = (
        f"너는 똑똑한 선생님이야. 학습 내용을 바탕으로 {count}문제 퀴즈를 JSON 배열로 생성해줘.\n"
        f"{type_clause}"
        "각 문제는 다음 항목을 포함해야 해: type, question, options (객관식/OX), answer, explanation.\n"
        "type은 '객관식', 'OX', '주관식', '빈칸' 중 하나로 설정해줘.\n"
        "JSON 배열만 반환해줘. 다른 설명은 하지 마.\n"
    )

    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ],
        temperature=0.7
    )
    raw = resp.choices[0].message.content.strip()
    m = re.search(r'\[.*\]', raw, re.S)
    if not m:
        st.error("❌ JSON 배열을 찾지 못했습니다.")
        st.text_area("📝 GPT 원문", raw, height=200)
        return []
    try:
        data = json.loads(m.group(0))
        return [d if isinstance(d, dict) else json.loads(d) for d in data if isinstance(d, (dict, str))]
    except Exception as e:
        st.error(f"❌ JSON 파싱 실패: {e}")
        return []

# === 요약 함수 ===
def summarize_content(text):
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "아래 내용을 3~5줄로 요약해줘."},
            {"role": "user", "content": text}
        ]
    )
    return resp.choices[0].message.content.strip()

# === 오답 해설 요청 ===
def ask_about_wrong(q, ua):
    prompt = f"문제: {q['question']}\n정답: {q['answer']}\n내 답: {ua}\n왜 틀렸는지 쉽게 설명해줘."
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "친절한 선생님이 되어 설명해줘."},
            {"role": "user", "content": prompt}
        ]
    )
    return resp.choices[0].message.content.strip()

# === 퀴즈 생성 폼 ===
with st.form("quiz_form"):
    quiz_type = st.selectbox("문제 유형", ["모든 유형", "OX", "객관식", "주관식", "빈칸"])
    quiz_count = st.number_input("출제할 퀴즈 개수", min_value=1, max_value=10, value=8, step=1)
    content = st.text_area("✍️ 학습 내용을 입력하세요", height=200)
    go = st.form_submit_button("🧠 퀴즈 생성하기")

if go:
    if content.strip():
        st.session_state.summary_log = summarize_content(content)
        st.session_state.quiz_data = generate_quiz(content, quiz_count, quiz_type)
        st.session_state.user_answers = {}
        st.session_state.graded = False

# === 요약 출력 ===
if st.session_state.summary_log:
    st.info(f"📚 학습 요약:\n\n{st.session_state.summary_log}")

# === 전체 문제 출력 ===
def show_all_questions():
    st.subheader("📝 퀴즈 문제")
    for i, q in enumerate(st.session_state.quiz_data):
        st.markdown(f"**{i+1}. {q['question']}**")
        q_type = q.get("type", "").strip()
        if q_type in ["객관식", "OX"] and "options" in q:
            st.session_state.user_answers[i] = st.radio(
                f"선택지 중 정답을 고르세요 (문제 {i+1})",
                q["options"],
                key=f"answer_{i}",
                index=0 if f"answer_{i}" not in st.session_state else
                q["options"].index(st.session_state.user_answers.get(i, q["options"][0]))
            )
        else:
            st.session_state.user_answers[i] = st.text_input(
                f"정답을 입력하세요 (문제 {i+1})",
                key=f"answer_{i}",
                value=st.session_state.user_answers.get(i, "")
            )

    if st.button("✅ 전체 채점하기"):
        st.session_state.graded = True

# === 채점 ===
def grade_and_feedback():
    st.subheader("📊 채점 결과")
    for idx, q in enumerate(st.session_state.quiz_data):
        ua = str(st.session_state.user_answers.get(idx, "")).strip()
        ans = q["answer"]
        correct = (ua in ans) if isinstance(ans, list) else (ua == str(ans).strip())
        st.write(f"문제 {idx+1}: {'✅ 정답' if correct else '❌ 오답'}")
        if not correct:
            expl = ask_about_wrong(q, ua)
            st.write(f"🧠 해설: {expl}")

# === 문제 or 결과 출력 ===
if st.session_state.quiz_data and not st.session_state.graded:
    show_all_questions()
elif st.session_state.graded:
    grade_and_feedback()

# === 컨테이너 종료 ===
st.markdown('</div>', unsafe_allow_html=True)
