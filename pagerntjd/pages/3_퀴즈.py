import streamlit as st
import openai
import json
import os
import re
from dotenv import load_dotenv

# === 페이지 설정 ===
st.set_page_config(page_title="딸깍공 퀴즈", layout="wide", initial_sidebar_state="collapsed")

# === CSS 스타일 ===
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body {
    font-family: 'Noto Sans KR', sans-serif;
    background-color: #FAFAFA;
    color: #333;
    zoom: 1.05;
    margin: 0;
}
.stApp { background-color: #FAFAFA; }
.block-container { padding-top: 0 !important; }
.container { max-width: 1200px; margin: auto; padding: 40px; }
a { text-decoration: none !important; color: #333; }

.top-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    margin-top: -40px !important;
    background-color: rgba(255, 255, 255, 0.9);
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.nav-left { display: flex; align-items: center; gap: 60px; }
.top-nav .nav-left > div:first-child a {
    color: #000 !important;
    font-size: 28px;
    font-weight: bold;
}
.nav-menu {
    display: flex;
    gap: 36px;
    font-size: 18px;
    font-weight: 600;
}
.nav-menu div a {
    color: #000 !important;
    transition: all 0.2s ease;
}
.nav-menu div:hover a {
    color: #FF9330 !important;
}
.profile-group {
    display: flex; gap: 16px; align-items: center;
}
.profile-icon {
    background-color: #888;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    cursor: pointer;
}
header, #MainMenu, [data-testid="stSidebar"], button[title="사이드바 토글"] {
    display: none !important;
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
</style>
""", unsafe_allow_html=True)

# === 컨테이너 시작 ===
st.markdown('<div class="container">', unsafe_allow_html=True)

# === 네비게이션 바 ===
st.markdown("""
<div class="top-nav">
  <div class="nav-left">
    <div><a href="/mainpage" target="_self">🐾 딸깍공</a></div>
    <div class="nav-menu">
      <div><a href="/mainpage" target="_self">메인페이지</a></div>
      <div><a href="/공부_시작" target="_self">공부 시작</a></div>
      <div><a href="/필기" target="_self">필기</a></div>
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
