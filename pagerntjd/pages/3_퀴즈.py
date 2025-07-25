import streamlit as st
import configparser
import openai
import json
import os

# --- 이전에 사용하셨던 CSS 스타일 ---
custom_css = """
<style>
/* 전체 폰트 및 배경 */
body, .css-18e3th9 {
    font-family: 'Noto Sans KR', sans-serif;
    background-color: #fff;
    color: #333;
}

/* 최대 너비 박스 중앙 정렬 */
.main .block-container {
    max-width: 960px;
    padding-top: 20px;
    padding-bottom: 40px;
}

/* 사이드바 숨기기 */
[data-testid="stSidebar"] {
    display: none;
}
button[title="사이드바 토글"] {
    display: none;
}

/* 오른쪽 상단 메뉴 숨기기 (Deploy 버튼 포함) */
header > div:first-child {
    display: none !important;
}

/* 페이지 좌측 여백 최소화 */
.main > div:first-child {
    padding-left: 0rem;
}

/* 상단 네비게이션 바 스타일 */
.navbar {
    display: flex;
    align-items: center;
    gap: 24px;
    padding: 12px 20px;
    border-bottom: 1px solid #eee;
    font-weight: 600;
    font-size: 16px;
    font-family: 'Noto Sans KR', sans-serif;
    margin-bottom: 40px;
}
.navbar .logo {
    font-weight: 700;
    font-size: 26px;
    color: #FF6600;
    user-select: none;
}
.navbar a {
    color: #222;
    text-decoration: none;
    cursor: pointer;
    transition: color 0.2s ease;
}
.navbar a:hover, .navbar a.active {
    color: #FF6600;
}

/* 퀴즈 박스 */
.quiz-container {
    width: 520px;
    margin: 0 auto 40px auto;
    border: 2px solid #FF6600;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 12px rgb(255 102 0 / 0.2);
}

/* 헤더 바 */
.quiz-header {
    background: linear-gradient(90deg, #FF7F00, #E65C00);
    color: white;
    text-align: center;
    font-size: 28px;
    font-weight: 700;
    padding: 16px 0;
    user-select: none;
}

/* 문제 번호 및 질문 */
.quiz-question {
    text-align: center;
    font-size: 18px;
    padding: 20px 16px 8px;
    user-select: none;
}

/* 객관식 선택지 그리드 */
.options-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px 18px;
    padding: 0 20px 20px;
}

/* 각 선택지 박스 */
.option-btn {
    border: 1.5px solid #eee;
    border-radius: 12px;
    background: #fefefe;
    padding: 14px 12px;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.3s ease, border-color 0.3s ease;
    user-select: none;
    display: flex;
    align-items: center;
    gap: 12px;
}
.option-btn:hover {
    background-color: #fff3e6;
    border-color: #ff8c33;
}
.option-label {
    color: #FF6600;
    font-weight: 700;
    font-size: 18px;
    user-select: none;
}

/* 다음 버튼 */
.next-btn-container {
    text-align: center;
    padding: 0 0 24px;
}
.next-btn {
    background-color: #FF6600;
    border: none;
    border-radius: 12px;
    color: white;
    font-size: 20px;
    font-weight: 700;
    padding: 12px 64px;
    cursor: pointer;
    transition: background-color 0.25s ease;
    user-select: none;
}
.next-btn:hover {
    background-color: #cc5200;
}

/* 기타 폼 요소 스타일 */
.stRadio > div {
    margin-left: 0 !important;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 네비게이션 바 (공지 삭제됨) ---
nav_html = """
<div class="navbar">
    <div class="logo">딸깍공</div>
    <a href="/mainpage">메인페이지</a>
    <a href="/공부_시작" class="active">공부 시작</a>
    <a href="/필기">필기</a>
    <a href="/저장폴더">저장폴더</a>
    <a href="/퀴즈">퀴즈</a>
    <a href="/리포트">리포트(피드백)</a>
</div>
"""
st.markdown(nav_html, unsafe_allow_html=True)

# --- config.ini 로드 및 OpenAI 초기화 ---
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")

config = configparser.ConfigParser()
try:
    with open(CONFIG_PATH, encoding='utf-8') as f:
        config.read_file(f)
except Exception as e:
    st.error(f"❌ config.ini 파일 문제: {e}")
    st.stop()

if not config.has_section("openai"):
    st.error(f"❌ config.ini에 [openai] 섹션이 없습니다!")
    st.stop()

api_key = config.get("openai", "api_key")
client = openai.OpenAI(api_key=api_key)

st.set_page_config(page_title="GPT 퀴즈 생성기", layout="centered")

st.markdown('<div class="quiz-container">', unsafe_allow_html=True)
st.markdown('<div class="quiz-header">퀴즈 풀기</div>', unsafe_allow_html=True)

# --- 세션 상태 초기화 ---
for key in ["quiz_data", "user_answers", "confirmed_answers", "wrong_indices", "chat_logs", "summary_log", "graded", "current_question"]:
    if key not in st.session_state:
        st.session_state[key] = [] if "data" in key else (False if key in ["graded"] else 0 if key=="current_question" else {})

# --- GPT 퀴즈 생성 함수 (엄격 JSON 반환) ---
def generate_quiz(content):
    system_prompt = """
너는 똑똑한 선생님이야. 학습 내용을 바탕으로 다양한 퀴즈를 JSON 배열 형식으로 생성해줘.
- 총 8문제, 유형은 OX, 객관식, 주관식, 빈칸 중 랜덤하게 구성.
- 문제 유형은 균등하지 않아도 되고 자유롭게 구성 가능.
- 각 문제는 반드시 아래 항목 포함:
  - type: 'OX' | '객관식' | '주관식' | '빈칸'
  - question: 질문 내용 (문자열)
  - options: (객관식 또는 OX 문제에만) 선택지 리스트 (문자열 리스트)
  - answer: 정답 (문자열 또는 문자열 리스트)
  - explanation: 해설 (왜 정답인지 설명, 문자열)
  - example: 예시 또는 배경 설명 (선택사항, 문자열)
- JSON 배열 외에 다른 설명, 텍스트, 주석 절대 포함하지 마.
- 반드시 정확한 JSON 배열만 반환하고, 여백, 줄바꿈도 포함해도 괜찮음.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            temperature=0.7
        )
        raw_text = response.choices[0].message.content.strip()
        quiz_json = json.loads(raw_text)
        return quiz_json
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON 파싱 실패: {e}")
        st.text_area("📝 GPT 응답 원문 (디버깅용)", raw_text, height=300)
        return []
    except Exception as e:
        st.error(f"❌ 퀴즈 생성 실패: {e}")
        return []

# --- 요약, 오답 피드백, 문제 표시, 채점, 대화 함수는 이전 코드와 동일 ---

def summarize_content(content):
    try:
        system = "아래 내용을 3~5줄로 요약해줘."
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": content}
            ]
        )
        return response.choices[0].message.content.strip()
    except:
        return "요약 실패"

def ask_gpt_about_wrong(problem, user_answer):
    prompt = f"""문제: {problem['question']}
정답: {problem['answer']}
내가 작성한 오답: {user_answer}
왜 틀렸는지 쉽게 설명해줘."""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "너는 친절한 선생님이야."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def summarize_answer(answer):
    try:
        system = "아래 내용을 최대 2문장으로 핵심만 요약해줘."
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": answer}
            ]
        )
        return response.choices[0].message.content.strip()
    except:
        return "요약 실패"

def show_current_question():
    idx = st.session_state.current_question
    quiz = st.session_state.quiz_data[idx]
    total = len(st.session_state.quiz_data)

    st.markdown(f'<div class="quiz-question">{idx+1} / {total}<br>{quiz["question"]}</div>', unsafe_allow_html=True)

    if quiz["type"] in ["객관식", "OX"]:
        options = quiz.get("options", [])
        selected = st.radio("", options, key="current_answer")
    else:
        selected = st.text_input("정답 입력", key="current_answer")

    if st.button("다음"):
        st.session_state.user_answers[idx] = selected
        st.session_state.confirmed_answers[idx] = True
        if idx + 1 < total:
            st.session_state.current_question += 1
        else:
            st.session_state.graded = True

def grade_quiz():
    st.subheader("🎯 채점 결과")
    wrongs = []
    for i, quiz in enumerate(st.session_state.quiz_data):
        user = str(st.session_state.user_answers.get(i, "")).strip()
        answer = quiz["answer"]
        correct = user in answer if isinstance(answer, list) else user == str(answer).strip()

        st.markdown(f"**문제 {i + 1}: {'✅ 정답' if correct else '❌ 오답'}**")
        st.markdown(f"- 질문: {quiz['question']}")
        if quiz["type"] in ["객관식", "OX"]:
            st.markdown(f"- 선택지: {', '.join(quiz.get('options', []))}")
        st.markdown(f"- 정답: {answer}")
        st.markdown(f"- 해설: {quiz.get('explanation', '없음')}")
        st.markdown(f"- 예시: {quiz.get('example', '없음')}")
        st.markdown("---")

        if not correct:
            wrongs.append(i)
    st.session_state.wrong_indices = wrongs

def wrong_gpt_chat():
    for i in st.session_state.wrong_indices:
        quiz = st.session_state.quiz_data[i]
        user_answer = st.session_state.user_answers[i]
        question_key = quiz["question"]

        if question_key not in st.session_state.chat_logs:
            reply = ask_gpt_about_wrong(quiz, user_answer)
            st.session_state.chat_logs[question_key] = [{"role": "assistant", "content": reply}]
            st.session_state[f"last_reply_{i}"] = reply

        with st.expander(f"💬 GPT에게 문제 {i+1} 질문하기", expanded=True):
            st.markdown(f"🧠 GPT 답변: {st.session_state[f'last_reply_{i}']}")
            st.markdown(f"📌 요약: {summarize_answer(st.session_state[f'last_reply_{i}'])}")

            with st.form(key=f"form_followup_{i}"):
                key_followup = f"followup_{i}_text"
                user_followup = st.text_input("추가 질문 입력", key=key_followup)
                submitted = st.form_submit_button("질문 보내기")

                if submitted and user_followup.strip():
                    chat = st.session_state.chat_logs[question_key]
                    chat.append({"role": "user", "content": user_followup})

                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "system", "content": "친절한 피드백을 제공해줘."}] + chat
                    )
                    reply = response.choices[0].message.content.strip()
                    chat.append({"role": "assistant", "content": reply})

                    st.session_state.chat_logs[question_key] = chat
                    st.session_state[f"last_reply_{i}"] = reply

            with st.expander("📜 전체 대화 보기", expanded=False):
                for msg in st.session_state.chat_logs[question_key]:
                    who = "🙋 질문" if msg["role"] == "user" else "🧠 답변"
                    st.markdown(f"{who}: {msg['content']}")

# --- 퀴즈 생성 폼 ---
with st.form(key="quiz_form"):
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    quiz_type = st.selectbox("문제 유형", ["모든 유형", "OX", "객관식", "주관식", "빈칸"])
    quiz_count = st.slider("출제할 퀴즈 개수", 1, 10, 8)  # 최소값 1
    content = st.text_area("✍️ 학습 내용을 입력하세요", height=200)
    st.markdown('</div>', unsafe_allow_html=True)

    submit = st.form_submit_button("🧠 퀴즈 생성하기")

if submit:
    if not content.strip():
        st.warning("내용을 입력해주세요.")
    elif len(content.strip()) < 5:
        st.error("❌ 퀴즈를 인식하지 못했습니다.")
    else:
        with st.spinner("GPT가 퀴즈와 요약을 생성 중입니다..."):
            st.session_state.summary_log = summarize_content(content)
            quiz = generate_quiz(content)
            if quiz:
                st.session_state.quiz_data = quiz[:quiz_count]
                st.session_state.user_answers = {}
                st.session_state.confirmed_answers = {}
                st.session_state.wrong_indices = []
                st.session_state.chat_logs = {}
                st.session_state.graded = False
                st.session_state.current_question = 0

# --- 현재 문제 보여주기 ---
if st.session_state.quiz_data and not st.session_state.graded:
    show_current_question()

# --- 채점 및 오답 피드백 보여주기 ---
if st.session_state.graded:
    grade_quiz()
    wrong_gpt_chat()

# --- 학습 요약 보여주기 ---
if st.session_state.get("summary_log"):
    st.info(f"📚 학습 요약:\n\n{st.session_state.summary_log}")
