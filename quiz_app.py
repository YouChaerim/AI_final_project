import streamlit as st
import configparser
import openai
import json
import re

# === API 키 불러오기 ===
config = configparser.ConfigParser()
config.read("config.ini")
api_key = config.get("openai", "api_key")
client = openai.OpenAI(api_key=api_key)

# === 페이지 설정 ===
st.set_page_config(page_title="GPT 퀴즈 생성기", layout="centered")
st.title("📘 GPT 기반 복습 퀴즈 생성기")
st.markdown("학습 내용을 입력하면 다양한 유형의 퀴즈를 생성하고 채점할 수 있어요!")

# === 세션 상태 초기화 ===
for key in [
    "quiz_data", "user_answers", "confirmed_answers",
    "wrong_indices", "chat_logs", "summary_log", "graded"
]:
    if key not in st.session_state:
        if key == "quiz_data":
            st.session_state[key] = []
        elif key == "graded":
            st.session_state[key] = False
        else:
            st.session_state[key] = {}

# === GPT 퀴즈 생성 함수 (정교 파싱) ===
def generate_quiz(content):
    system_prompt = (
        "너는 똑똑한 선생님이야. 학습 내용을 바탕으로 8문제 퀴즈를 JSON 배열 형식으로 생성해줘.\n"
        "- 각 문제에 type, question, options(객관식/OX), answer, explanation 포함\n"
        "- JSON 배열만 반환해줘."
    )
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": content}
        ],
        temperature=0.7
    )
    raw = resp.choices[0].message.content.strip()

    # 1) '['부터 ']'까지 추출
    m = re.search(r'\[.*\]', raw, re.S)
    if not m:
        st.error("❌ 응답에서 JSON 배열을 찾지 못했습니다.")
        st.text_area("📝 GPT 원문 응답", raw, height=300)
        return []
    json_text = m.group(0)

    # 2) JSON 파싱
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON 파싱 실패: {e}")
        st.text_area("📝 파싱 대상 텍스트", json_text, height=300)
        return []

    # 3) 리스트 안 문자열 요소가 dict 형태면 다시 파싱
    clean_list = []
    for el in data:
        if isinstance(el, dict):
            clean_list.append(el)
        elif isinstance(el, str):
            try:
                parsed = json.loads(el)
                if isinstance(parsed, dict):
                    clean_list.append(parsed)
            except:
                continue

    # 4) OX 문제 기본 options 보정
    for q in clean_list:
        if q.get("type") == "OX" and not q.get("options"):
            q["options"] = ["O", "X"]

    return clean_list

# === 학습 요약 함수 ===
def summarize_content(content):
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "아래 내용을 3~5줄로 요약해줘."},
            {"role": "user",   "content": content}
        ]
    )
    return resp.choices[0].message.content.strip()

# === 오답 피드백 함수 ===
def ask_gpt_about_wrong(problem, user_answer):
    prompt = (
        f"문제: {problem['question']}\n"
        f"정답: {problem['answer']}\n"
        f"내가 작성한 오답: {user_answer}\n"
        "왜 틀렸는지 쉽게 설명해줘."
    )
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "너는 친절한 선생님이야."},
            {"role": "user",   "content": prompt}
        ]
    )
    return resp.choices[0].message.content.strip()

# === 답변 요약 함수 ===
def summarize_answer(answer):
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "아래 내용을 최대 2문장으로 요약해줘."},
            {"role": "user",   "content": answer}
        ]
    )
    return resp.choices[0].message.content.strip()

# === 퀴즈 출력 함수 ===
def show_quiz():
    for idx, quiz in enumerate(st.session_state.quiz_data):
        st.markdown(f"### 문제 {idx+1} ({quiz.get('type','')})")
        st.markdown(f"**{quiz.get('question','')}**")

        if idx not in st.session_state["confirmed_answers"]:
            with st.form(key=f"form_{idx}"):
                qtype = quiz.get("type")
                if qtype == "객관식":
                    ui = st.radio("선택지", quiz.get("options", []), key=f"input_{idx}")
                elif qtype == "OX":
                    ui = st.radio("선택지", ["O","X"], key=f"input_{idx}")
                else:
                    ui = st.text_input("정답 입력", key=f"input_{idx}")
                sb = st.form_submit_button("정답 제출")
                if sb:
                    st.session_state["user_answers"][idx]      = ui
                    st.session_state["confirmed_answers"][idx] = True
                    st.rerun()
        else:
            st.success(f"입력한 답: {st.session_state['user_answers'][idx]}")

# === 채점 함수 ===
def grade_quiz():
    st.subheader("🎯 채점 결과")
    wrongs = []
    for i, quiz in enumerate(st.session_state.quiz_data):
        ua  = str(st.session_state["user_answers"].get(i, "")).strip()
        ans = quiz.get("answer", "")
        correct = (ua in ans) if isinstance(ans, list) else (ua == str(ans).strip())
        st.markdown(f"**문제 {i+1}: {'✅ 정답' if correct else '❌ 오답'}**")
        if not correct:
            wrongs.append(i)
    st.session_state["wrong_indices"] = wrongs

# === 오답 GPT 대화 함수 ===
def wrong_gpt_chat():
    for i in st.session_state["wrong_indices"]:
        quiz = st.session_state.quiz_data[i]
        ua   = st.session_state["user_answers"][i]
        key  = quiz.get("question","")
        if key not in st.session_state["chat_logs"]:
            reply = ask_gpt_about_wrong(quiz, ua)
            st.session_state["chat_logs"][key] = [{"role":"assistant","content":reply}]
            st.session_state[f"last_reply_{i}"] = reply

        with st.expander(f"💬 문제 {i+1} 오답 피드백", expanded=True):
            st.markdown(f"🧠 GPT 답변: {st.session_state[f'last_reply_{i}']}")
            st.markdown(f"📌 요약: {summarize_answer(st.session_state[f'last_reply_{i}'])}")
            with st.form(key=f"followup_{i}"):
                uf = st.text_input("추가 질문", key=f"followup_input_{i}")
                sb = st.form_submit_button("질문 보내기")
                if sb and uf.strip():
                    chat = st.session_state["chat_logs"][key]
                    chat.append({"role":"user","content":uf})
                    new_r = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role":"system","content":"친절히 설명해줘."}] + chat
                    )
                    nr = new_r.choices[0].message.content.strip()
                    chat.append({"role":"assistant","content":nr})
                    st.session_state["chat_logs"][key] = chat
                    st.session_state[f"last_reply_{i}"] = nr

        with st.expander("📜 전체 대화 보기", expanded=False):
            for msg in st.session_state["chat_logs"][key]:
                who = "🙋 질문" if msg["role"] == "user" else "🧠 답변"
                st.markdown(f"{who}: {msg['content']}")

# === 사용자 입력 폼 ===
quiz_type  = st.selectbox("문제 유형", ["모든 유형","OX","객관식","주관식","빈칸"])
quiz_count = st.slider("출제할 퀴즈 개수", 4, 10, 8)
content    = st.text_area("✍️ 학습 내용을 입력하세요", height=200)

if st.button("🧠 퀴즈 생성하기"):
    if not content.strip():
        st.warning("내용을 입력해주세요.")
    else:
        st.session_state["summary_log"]       = summarize_content(content)
        lst = generate_quiz(content)
        st.session_state["quiz_data"]         = lst[:quiz_count]
        st.session_state["user_answers"]      = {}
        st.session_state["confirmed_answers"] = {}
        st.session_state["wrong_indices"]     = []
        st.session_state["chat_logs"]         = {}
        st.session_state["graded"]            = False
        st.rerun()

# === 실행 흐름 ===
if st.session_state.get("summary_log"):
    st.info(f"📚 학습 요약:\n\n{st.session_state['summary_log']}")

if st.session_state.quiz_data:
    show_quiz()
    if len(st.session_state["confirmed_answers"]) == len(st.session_state["quiz_data"]):
        if st.button("✅ 전체 채점"):
            grade_quiz()
            st.session_state["graded"] = True

if st.session_state["graded"]:
    wrong_gpt_chat()
