import streamlit as st
import configparser
import openai
import json

# ✅ API 키 불러오기
config = configparser.ConfigParser()
config.read("config.ini")
api_key = config.get("openai", "api_key")
client = openai.OpenAI(api_key=api_key)

st.set_page_config(page_title="GPT 퀴즈 생성기", layout="centered")
st.title("📘 GPT 기반 복습 퀴즈 생성기")
st.markdown("학습 내용을 입력하면 다양한 유형의 퀴즈를 생성하고 채점할 수 있어요!")

# ✅ 세션 상태 초기화
for key in ["quiz_data", "user_answers", "confirmed_answers", "wrong_indices", "chat_logs", "summary_log", "graded"]:
    if key not in st.session_state:
        st.session_state[key] = [] if "data" in key else (False if key == "graded" else {})

# ✅ GPT 퀴즈 생성 함수
def generate_quiz(content):
    system_prompt = (
        "너는 똑똑한 선생님이야. 학습 내용을 바탕으로 다양한 퀴즈를 JSON 형식으로 생성해줘.\n"
        "- 총 8문제, 유형은 OX, 객관식, 주관식, 빈칸 중 랜덤하게 구성\n"
        "- 문제 유형은 균등하지 않아도 되고 자유롭게 구성 가능함\n"
        "- 각 문제는 다음 항목을 포함해야 함:\n"
        "  - type: 'OX' | '객관식' | '주관식' | '빈칸'\n"
        "  - question: 질문 내용\n"
        "  - options: (객관식, OX일 때만) 선택지 리스트\n"
        "  - answer: 정답 (문자열 또는 리스트)\n"
        "  - explanation: 해설 (왜 정답인지 설명)\n"
        "  - example: 예시 또는 배경 설명 (선택사항)\n"
        "JSON 배열로만 반환해줘. 설명문은 절대 포함하지 마."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            temperature=0.7
        )
        return json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        st.error(f"❌ 퀴즈 생성 실패: {e}")
        return []

# ✅ 학습 요약
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

# ✅ GPT 오답 피드백
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

# ✅ GPT 답변 요약
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

# ✅ 퀴즈 출력
def show_quiz():
    for idx, quiz in enumerate(st.session_state.quiz_data):
        st.markdown(f"### 문제 {idx + 1} ({quiz['type']})")
        st.markdown(f"**{quiz['question']}**")

        key_input = f"input_{idx}"
        key_form = f"form_{idx}"

        if idx not in st.session_state.confirmed_answers:
            with st.form(key=key_form):
                if quiz["type"] == "객관식":
                    user_input = st.radio("선택지", quiz.get("options", []), key=key_input)
                elif quiz["type"] == "OX":
                    user_input = st.radio("선택지", ["O", "X"], key=key_input)
                else:
                    user_input = st.text_input("정답 입력", key=key_input)
                submitted = st.form_submit_button("정답 제출")
                if submitted:
                    st.session_state.user_answers[idx] = user_input
                    st.session_state.confirmed_answers[idx] = True
                    st.rerun()
        else:
            st.success(f"입력한 답: {st.session_state.user_answers[idx]}")

# ✅ 채점
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

# ✅ GPT 피드백 대화
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

# ✅ 사용자 입력
quiz_type = st.selectbox("문제 유형", ["모든 유형", "OX", "객관식", "주관식", "빈칸"])
quiz_count = st.slider("출제할 퀴즈 개수", 4, 10, 8)
content = st.text_area("✍️ 학습 내용을 입력하세요", height=200)

if st.button("🧠 퀴즈 생성하기"):
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
                st.rerun()

# ✅ 실행 흐름
if st.session_state.get("summary_log"):
    st.info(f"📚 학습 요약:\n\n{st.session_state.summary_log}")

if st.session_state.quiz_data:
    show_quiz()

    if len(st.session_state.confirmed_answers) == len(st.session_state.quiz_data):
        if st.button("✅ 전체 채점"):
            grade_quiz()
            st.session_state.graded = True

    if st.session_state.graded:
        wrong_gpt_chat()


####asdasdsad