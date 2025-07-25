# -*- coding: utf-8 -*- (유니코드로 수정 2025/07/25)
import streamlit as st
import numpy as np
import os
import re
import json5
import cv2
from PIL import Image
from openai import OpenAI
from paddleocr import PaddleOCR
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
from dotenv import load_dotenv  # ✅ 추가(2025/07/25)

# ===== ✅ .env에서 환경변수 불러오기 =====
load_dotenv(dotenv_path="C:/Users/user/Desktop/최종파일/AI_final_project/.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ===== 페이지 기본 설정 =====
st.set_page_config(page_title="📄 OCR + GPT 요약/퀴즈 생성기", layout="centered")

# ✅ file_uploader key 초기값 설정 (최초 1회만)
if "file_key" not in st.session_state:
    st.session_state.file_key = "uploader_1"

# ✅ 완전한 새로고침(2025/07/25 수정)
st.markdown("<div style='text-align:right'>", unsafe_allow_html=True)
if st.button("🔄 전체 새로고침", key="refresh_all"):
    keys_to_clear = [
        "uploaded_file", "ocr_result_text", "summary_text", "quiz_content_input",
        "summary", "summary_log", "quiz_data", "user_answers",
        "confirmed_answers", "wrong_indices", "chat_logs", "graded"
    ]
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]
    st.session_state.file_key = "uploader_" + str(np.random.randint(100000))
    st.session_state.quiz_content_input = ""
    st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

# ===== ✅ OpenAI 클라이언트 캐싱 함수 =====
@st.cache_resource
def get_openai_client():
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")  # ✅ 함수 안에서 직접 불러오기

    if not api_key or api_key.lower() == "sorry":
        st.error("❌ .env에서 유효한 OpenAI API 키를 불러올 수 없습니다.")
        st.stop()

    return OpenAI(api_key=api_key)

# ✅ OpenAI 클라이언트 생성
client = get_openai_client()

# ===== OpenAI 및 OCR 캐싱 =====
@st.cache_resource
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")  # ✅ .env에서 API 키 불러오기(2025/07/25)
    if not api_key:
        st.error("❌ .env 파일에서 OpenAI API 키를 찾을 수 없습니다.")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()

@st.cache_resource
def get_ocr():
    return PaddleOCR(
        use_textline_orientation=True,     # ✅ 최신 파라미터
        lang='korean',
        text_det_box_thresh=0.2,
        text_det_unclip_ratio=2.0,
        ocr_version='PP-OCRv3'   
    )
ocr = get_ocr()  # ✅ 최초 1회만 로드되고, 이후 재사용됨

# ===== 유틸 함수 =====
def extract_pdf_text_if_possible(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    except:
        return ""

def crop_image(image_np, coords):
    coords = np.array(coords).reshape(-1, 2).astype(np.int32)
    x_min, y_min = coords.min(axis=0)
    x_max, y_max = coords.max(axis=0)
    return image_np[y_min:y_max, x_min:x_max]

def safe_load_json5(text):
    try:
        return json5.loads(text)
    except Exception as e:
        st.error(f"❌ JSON 파싱 실패: {e}")
        st.code(text)
        return []

def generate_quiz(content, quiz_count=8):
    prompt = f"""
너는 똑똑한 교육용 선생님이야. 아래의 내용을 바탕으로 다양한 유형의 퀴즈를 JSON 리스트로 만들어줘.

예시:
[
  {{
    "type": "객관식",
    "question": "예시 질문",
    "options": ["A", "B", "C", "D"],
    "answer": "A",
    "explanation": "정답 해설",
    "example": "관련 배경 설명"
  }}
]

- 반드시 'type', 'question', 'answer', 'explanation', 'example' 키를 포함해야 해
- 'options'는 객관식, OX에만 포함되고 주관식/빈칸형은 생략해
- JSON 리스트만 출력하고 절대 설명문 추가하지 마
- 총 {quiz_count}문제
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": content}
            ]
        )

        if not response.choices or not response.choices[0].message.content:
            st.error("❌ GPT 응답이 비어있습니다.")
            return []

        raw = response.choices[0].message.content.strip()

        # ✅ GPT 응답에 ```json 감싸진 경우 제거
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = re.sub(r"^json", "", raw, flags=re.IGNORECASE).strip()

        parsed = safe_load_json5(raw)
        return parsed[:quiz_count] if isinstance(parsed, list) else []

    except Exception as e:
        st.error(f"❌ 퀴즈 생성 실패: {e}")
        return []
        
def summarize_content(content):
    try:
        system = "아래 내용을 3~5줄로 핵심만 요약해줘."
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 또는 "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": content}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"❌ 요약 실패: {e}")
        return "요약 실패"

def ask_gpt_about_wrong(problem, user_answer):
    prompt = f"""문제: {problem['question']}\n정답: {problem['answer']}\n내가 작성한 오답: {user_answer}\n왜 틀렸는지 쉽게 설명해줘."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
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
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": answer}
            ]
        )
        return response.choices[0].message.content.strip()
    except:
        return "요약 실패"

# ===== 탭 구성 =====
tab1, tab2 = st.tabs(["📄 OCR + 요약기", "🧠 GPT 퀴즈 생성기"])

with tab1:
    st.header("📄 OCR 기반 손글씨 인식 및 요약")

    # uploaded_file = st.file_uploader("📤 이미지 또는 PDF 업로드", type=["png", "jpg", "jpeg", "pdf"])
    uploaded_file = st.file_uploader(
    "📤 이미지 또는 PDF 업로드",
    type=["png", "jpg", "jpeg", "pdf"],
    key=st.session_state.file_key  # ✅ 동적으로 바뀌는 key
)

    clean_text = ""

    if uploaded_file:
        is_pdf = uploaded_file.type == "application/pdf"
        if is_pdf:
            text = extract_pdf_text_if_possible(uploaded_file)
            if text.strip():
                clean_text = text
                st.success("✅ PDF에서 텍스트 추출 성공")
            else:
                uploaded_file.seek(0)
                images = convert_from_bytes(uploaded_file.read(), dpi=300)
                st.image(images[0], caption="📄 PDF 첫 페이지", width=600)
        else:
            img = Image.open(uploaded_file).convert("RGB")
            st.image(img, caption="🖼️ 업로드된 이미지", width=600)

        if clean_text == "" and st.button("🔍 OCR 실행"):
            # OCR 처리 로직 여기에 삽입
            pass

        if clean_text.strip():
            st.text_area("📝 인식된 텍스트", clean_text, height=250, key="ocr_result_text")
            if st.button("📚 GPT 요약하기"):
                with st.spinner("요약 중..."):
                    summary = summarize_content(clean_text)
                    st.session_state.summary = summary
                    st.text_area("📌 요약 결과", summary, height=150, key="summary_text")

with tab2:
    st.header("🧠 GPT 기반 퀴즈 생성기")

    quiz_count = st.slider("출제할 퀴즈 개수", 4, 10, 8)
    content_input = st.text_area(
    "✍️ 학습 내용을 입력하거나 OCR 요약 결과를 사용하세요",
    value=st.session_state.get("quiz_content_input", ""),
    height=200,
    key="quiz_content_input"
)

    st.markdown("✅ OCR 요약 결과가 있다면 자동으로 그 내용을 사용합니다.")

    if st.button("🧠 퀴즈 생성하기"):
        content_to_use = st.session_state.get("summary", "").strip() or content_input.strip()
        if not content_to_use:
            st.warning("내용을 입력하거나 요약 결과를 생성해주세요.")
        elif len(content_to_use) < 5:
            st.error("❌ 퀴즈를 인식하지 못했습니다.")
        else:
            with st.spinner("GPT가 퀴즈를 생성 중입니다..."):
                st.session_state.summary_log = summarize_content(content_to_use)
                st.session_state.quiz_data = generate_quiz(content_to_use, quiz_count)
                st.session_state.user_answers = {}
                st.session_state.confirmed_answers = {}
                st.session_state.wrong_indices = []
                st.session_state.chat_logs = {}
                st.session_state.graded = False

    if st.session_state.get("summary_log"):
        st.info(f"📚 학습 요약:\n\n{st.session_state.summary_log}")

    def show_quiz():
        for idx, quiz in enumerate(st.session_state.quiz_data):
            st.markdown(f"### 문제 {idx + 1} ({quiz.get('type', '-')})")
            st.markdown(f"**{quiz.get('question', '-') }**")
            key_input = f"input_{idx}"
            key_form = f"form_{idx}"

            if idx not in st.session_state.get("confirmed_answers", {}):
                with st.form(key=key_form):
                    if quiz.get("type") == "객관식":
                        user_input = st.radio("선택지", quiz.get("options", []), key=key_input)
                    elif quiz.get("type") == "OX":
                        user_input = st.radio("선택지", ["O", "X"], key=key_input)
                    else:
                        user_input = st.text_input("정답 입력", key=key_input)
                    submitted = st.form_submit_button("정답 제출")
                    if submitted:
                        st.session_state.user_answers[idx] = user_input
                        st.session_state.confirmed_answers[idx] = True

            else:
                st.success(f"입력한 답: {st.session_state.user_answers[idx]}")

    if st.session_state.get("quiz_data"):
        show_quiz()

        if st.session_state.get("confirmed_answers") and len(st.session_state.confirmed_answers) == len(st.session_state.quiz_data):
            if st.button("✅ 전체 채점", key="grade_quiz"):
                for i, quiz in enumerate(st.session_state.quiz_data):
                    user = str(st.session_state.user_answers.get(i, "")).strip()
                    answer = quiz.get("answer", "")
                    correct = (user in answer) if isinstance(answer, list) else (user == str(answer).strip())
                    st.markdown(f"**문제 {i + 1}: {'✅ 정답' if correct else '❌ 오답'}**")
                    st.markdown(f"- 질문: {quiz.get('question', '-')}")
                    if quiz.get("type") in ["객관식", "OX"]:
                        st.markdown(f"- 선택지: {', '.join(quiz.get('options', []))}")
                    st.markdown(f"- 정답: {answer}")
                    st.markdown(f"- 해설: {quiz.get('explanation', '없음')}")
                    st.markdown(f"- 예시: {quiz.get('example', '없음')}")
                    st.markdown("---")
                    if not correct:
                        if i not in st.session_state.wrong_indices:
                            st.session_state.wrong_indices.append(i)
                st.session_state.graded = True

        if st.session_state.get("graded"):
            for i in st.session_state.wrong_indices:
                quiz = st.session_state.quiz_data[i]
                user_answer = st.session_state.user_answers[i]
                question_key = quiz.get("question", str(i))

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
                                model="gpt-4o-mini",
                                messages=[{"role": "system", "content": "친절한 피드백을 제공해줘."}] + chat
                            )
                            reply = response.choices[0].message.content.strip()
                            chat.append({"role": "assistant", "content": reply})
                            st.session_state.chat_logs[question_key] = chat
                            st.session_state[f"last_reply_{i}"] = reply



