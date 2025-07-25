import streamlit as st
import openai
import json
import os
import re
from dotenv import load_dotenv

# === 페이지 설정 & 기본 UI 숨기기 ===
st.set_page_config(page_title="딸깍공 퀴즈", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
/* 사이드바, 토글, 기본 헤더, Deploy 숨기기 */
[data-testid="stSidebar"], button[title="사이드바 토글"],
header, #MainMenu {
    display: none !important;
}
/* 상단 여백 제거 */
.block-container, .stApp > div:first-child {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

/* 글로벌 폰트 & 배경 */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body {
    font-family: 'Noto Sans KR', sans-serif;
    background-color: #FAFAFA;
    color: #333;
    margin: 0;
}

/* 커스텀 헤더 */
.custom-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 40px;
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    position: sticky;
    top: 0;
    z-index: 1000;
}
.custom-header .logo {
    font-size: 24px;
    font-weight: bold;
}
.custom-header nav {
    display: flex;
    gap: 24px;
    font-size: 18px;
    font-weight: 600;
}
.custom-header nav a {
    color: #333;
    text-decoration: none;
    transition: color 0.2s;
}
.custom-header nav a.active,
.custom-header nav a:hover {
    color: #FF9330;
}

/* 퀴즈 컨테이너 */
.container {
    max-width: 700px;
    margin: 20px auto 60px auto;
    padding: 30px 40px;
    background-color: white;
    border-radius: 18px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.12);
}

/* 폼 & 버튼 */
.stTextArea>div>textarea {
    height: 200px !important;
    width: 100% !important;
    border-radius: 10px !important;
    border: 1.8px solid #ccc !important;
    padding: 10px !important;
    font-size: 16px;
}
.stSelectbox > div, .stSlider > div {
    min-width: 150px;
}
.stButton>button {
    background-color: #FF9330;
    color: white;
    font-weight: 700;
    padding: 12px 36px;
    border-radius: 12px;
    font-size: 18px;
    margin-top: 20px;
}
.stButton>button:hover {
    background-color: #e07e22;
}

/* 문제 텍스트 */
.quiz-question {
    font-size: 20px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# === 커스텀 헤더 ===
st.markdown("""
<div class="custom-header">
  <div class="logo">🐾 딸깍공</div>
  <nav>
    <a href="/mainpage" target="_self">메인페이지</a>
    <a href="/공부_시작" target="_self">공부 시작</a>
    <a href="/필기" target="_self">필기</a>
    <a href="/저장폴더" target="_self">저장폴더</a>
    <a href="/퀴즈" target="_self" class="active">퀴즈</a>
    <a href="/리포트" target="_self">리포트</a>
    <a href="/랭킹" target="_self">랭킹</a>
  </nav>
</div>
""", unsafe_allow_html=True)

# === OpenAI 키 로드 ===
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("❌ OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다.")
    st.stop()
client = openai.OpenAI(api_key=api_key)

# === 세션 초기화 ===
for key in ["quiz_data", "user_answers", "confirmed", "wrong_indices", "chat_logs",
            "summary_log", "graded", "current_question"]:
    if key not in st.session_state:
        if key == "quiz_data":
            st.session_state[key] = []
        elif key == "graded":
            st.session_state[key] = False
        elif key in ["user_answers", "confirmed", "wrong_indices", "chat_logs"]:
            st.session_state[key] = {}
        elif key == "summary_log":
            st.session_state[key] = ""
        else:
            st.session_state[key] = 0

# === GPT 퀴즈 생성 함수 (타입 필터 + JSON 파싱) ===
def generate_quiz(content, count, qtype):
    type_clause = ""
    if qtype != "모든 유형":
        type_clause = f"- 모든 문제 유형은 '{qtype}'로 구성해줘.\n"
    system_prompt = (
        "너는 똑똑한 선생님이야. 학습 내용을 바탕으로 "
        f"{count}문제 퀴즈를 JSON 배열로 생성해줘.\n"
        f"{type_clause}"
        "각 문제에 반드시 type, question, options(객관식/OX), answer, explanation 포함.\n"
        "JSON 배열만 반환해줘."
    )
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user",  "content":content}
        ],
        temperature=0.7
    )
    raw = resp.choices[0].message.content.strip()

    # JSON 배열만 추출
    m = re.search(r'\[.*\]', raw, re.S)
    if not m:
        st.error("❌ JSON 배열을 찾지 못했습니다.")
        st.text_area("📝 GPT 원문", raw, height=200)
        return []
    arr = m.group(0)

    # 파싱
    try:
        data = json.loads(arr)
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON 파싱 실패: {e}")
        st.text_area("📝 파싱 텍스트", arr, height=200)
        return []

    # 리스트 내 문자열 요소 파싱
    clean = []
    for el in data:
        if isinstance(el, dict):
            clean.append(el)
        elif isinstance(el, str):
            try:
                d2 = json.loads(el)
                if isinstance(d2, dict):
                    clean.append(d2)
            except:
                continue

    # OX 기본 옵션
    for q in clean:
        if q.get("type") == "OX" and not q.get("options"):
            q["options"] = ["O", "X"]

    return clean

# === 학습 요약 함수 ===
def summarize_content(text):
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role":"system","content":"아래 내용을 3~5줄로 요약해줘."},
            {"role":"user","content":text}
        ]
    )
    return resp.choices[0].message.content.strip()

# === 오답 설명 요청 ===
def ask_about_wrong(q, ua):
    prompt = (
        f"문제: {q['question']}\n정답: {q['answer']}\n내 답: {ua}\n"
        "왜 틀렸는지 쉽게 설명해줘."
    )
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role":"system","content":"친절한 선생님이 되어 설명해줘."},
            {"role":"user",  "content":prompt}
        ]
    )
    return resp.choices[0].message.content.strip()

# === 퀴즈 생성 폼 ===
with st.form("quiz_form"):
    quiz_type  = st.selectbox("문제 유형", ["모든 유형","OX","객관식","주관식","빈칸"])
    quiz_count = st.slider("출제할 퀴즈 개수", 1, 10, 8)
    content    = st.text_area("✍️ 학습 내용을 입력하세요", height=200)
    go         = st.form_submit_button("🧠 퀴즈 생성하기")

if go:
    if not content.strip():
        st.warning("내용을 입력해주세요.")
    else:
        st.session_state.summary_log      = summarize_content(content)
        st.session_state.quiz_data         = generate_quiz(content, quiz_count, quiz_type)
        st.session_state.user_answers      = {}
        st.session_state.confirmed        = {}
        st.session_state.wrong_indices     = {}
        st.session_state.chat_logs         = {}
        st.session_state.graded            = False
        st.session_state.current_question = 0

# --- 학습 요약 표시 ---
if st.session_state.summary_log:
    st.info(f"📚 학습 요약:\n\n{st.session_state.summary_log}")

# === 문제풀이 & 채점 ===
def show_question():
    i = st.session_state.current_question
    q = st.session_state.quiz_data[i]
    st.markdown(f"<div class='quiz-question'><b>{i+1}/{len(st.session_state.quiz_data)}</b>  {q['question']}</div>", unsafe_allow_html=True)
    if q["type"] in ["객관식","OX"]:
        ui = st.radio("", q["options"], key="ans")
    else:
        ui = st.text_input("정답 입력", key="ans")
    if st.button("다음"):
        st.session_state.user_answers[i] = ui
        if i+1 < len(st.session_state.quiz_data):
            st.session_state.current_question += 1
        else:
            st.session_state.graded = True

def grade_and_feedback():
    for idx, q in enumerate(st.session_state.quiz_data):
        ua = str(st.session_state.user_answers.get(idx,"")).strip()
        ans = q["answer"]
        correct = (ua in ans) if isinstance(ans,list) else (ua == str(ans).strip())
        st.write(f"문제 {idx+1}: {'✅' if correct else '❌'}")
        if not correct:
            expl = ask_about_wrong(q, ua)
            st.write(f"🧠 해설: {expl}")

if st.session_state.quiz_data and not st.session_state.graded:
    show_question()
elif st.session_state.graded:
    grade_and_feedback()
