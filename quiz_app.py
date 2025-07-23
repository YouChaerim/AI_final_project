import streamlit as st
from dotenv import load_dotenv
import os
import openai
import json

# ✅ OpenAI API 키 로드
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)

st.set_page_config(page_title="GPT 퀴즈 생성기", layout="centered")
st.title("📘 GPT 기반 자동 퀴즈 생성기")
st.markdown("입력한 학습 내용을 분석해 자동으로 다양한 퀴즈를 생성하고 채점합니다!")

# 🔹 세션 상태 초기화
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = []
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "confirmed_answers" not in st.session_state:
    st.session_state.confirmed_answers = {}
if "wrong_indices" not in st.session_state:
    st.session_state.wrong_indices = []

# ✅ GPT로 퀴즈 생성
def generate_quiz(content):
    system_prompt = (
        "너는 똑똑한 선생님이야. 아래의 학습 내용을 바탕으로 다음과 같은 퀴즈를 만들어줘:\n"
        "- 서로 다른 주제의 OX, 객관식, 주관식, 빈칸 문제를 각각 1개씩 (총 4문제)\n"
        "- 문제 내용은 서로 겹치지 않고 다양하게 구성해줘\n"
        "- 문제별 해설은 충분히 구체적으로 작성해줘 (왜 정답이 맞는지 논리적으로 설명)\n"
        "- JSON 배열 형태로 아래와 같이 응답해줘:\n"
        "[\n"
        "  {\"type\": \"OX\", \"question\": \"...\", \"answer\": \"...\", \"explanation\": \"...\"},\n"
        "  {\"type\": \"객관식\", \"question\": \"...\", \"options\": [\"1\", \"2\", \"3\", \"4\"], \"answer\": \"...\", \"explanation\": \"...\"},\n"
        "  {\"type\": \"주관식\", \"question\": \"...\", \"answer\": \"...\", \"explanation\": \"...\"},\n"
        "  {\"type\": \"빈칸\", \"question\": \"...\", \"answer\": \"...\", \"explanation\": \"...\"}\n"
        "]\n"
        "JSON 외의 다른 설명은 절대 포함하지 마!"
    )
    user_prompt = f"학습 내용:\n{content}"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # ✅ 무료 모델
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)
    except Exception as e:
        st.error(f"❌ 퀴즈 생성 실패: {e}")
        return []

# ✅ 퀴즈 UI 렌더링
def show_quiz(quiz_list):
    for idx, quiz in enumerate(quiz_list):
        st.subheader(f"문제 {idx + 1} ({quiz['type']})")
        st.markdown(f"**{quiz['question']}**")

        key_input = f"input_{idx}"
        key_button = f"button_{idx}"

        if idx not in st.session_state.confirmed_answers:
            if quiz["type"] == "객관식":
                user_input = st.radio("선택지", quiz["options"], key=key_input)
            else:
                user_input = st.text_input("정답 입력", key=key_input, on_change=None)

            if st.button(f"문제 {idx + 1} 확인", key=key_button):
                st.session_state.user_answers[idx] = user_input
                st.session_state.confirmed_answers[idx] = True
                st.rerun()
        else:
            user_answer = st.session_state.user_answers[idx]
            st.success(f"입력한 답: {user_answer}")

# ✅ 채점 함수
def grade_quiz():
    wrongs = []
    st.subheader("📊 채점 결과")
    for i, quiz in enumerate(st.session_state.quiz_data):
        user_answer = st.session_state.user_answers.get(i, "")
        is_correct = str(user_answer).strip() == str(quiz["answer"]).strip()
        result = "✅ 정답" if is_correct else "❌ 오답"
        st.markdown(f"**문제 {i + 1}: {result}**")
        st.markdown(f"- 질문: {quiz['question']}")
        if quiz["type"] == "객관식":
            st.markdown(f"- 선택지: {', '.join(quiz['options'])}")
        st.markdown(f"- 정답: **{quiz['answer']}**")
        st.markdown(f"- 해설: {quiz['explanation']}")
        st.markdown("---")
        if not is_correct:
            wrongs.append(i)
    st.session_state.wrong_indices = wrongs

# ✅ 오답 다시 풀기
def retry_wrong():
    retry = [st.session_state.quiz_data[i] for i in st.session_state.wrong_indices]
    st.session_state.quiz_data = retry
    st.session_state.user_answers = {}
    st.session_state.confirmed_answers = {}
    st.session_state.wrong_indices = []
    st.rerun()

# ✅ 학습 내용 입력
user_input = st.text_area("✍️ 학습 내용을 입력하세요", height=200)

if st.button("🧠 퀴즈 생성하기"):
    if not user_input.strip():
        st.warning("내용을 입력해주세요.")
    else:
        with st.spinner("GPT가 퀴즈를 생성 중입니다..."):
            quiz_data = generate_quiz(user_input)
            if quiz_data:
                st.session_state.quiz_data = quiz_data
                st.session_state.user_answers = {}
                st.session_state.confirmed_answers = {}
                st.session_state.wrong_indices = []
                st.rerun()

# ✅ 퀴즈 보여주기 및 채점
if st.session_state.quiz_data:
    show_quiz(st.session_state.quiz_data)

    if len(st.session_state.confirmed_answers) == len(st.session_state.quiz_data):
        if st.button("✅ 전체 채점"):
            grade_quiz()
    else:
        st.info("모든 문제를 완료 후 채점할 수 있습니다.")

if st.session_state.wrong_indices:
    if st.button("🔁 오답만 다시 풀기"):
        retry_wrong()
