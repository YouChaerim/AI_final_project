# -*- coding: utf-8 -*- (유니코드로 수정 2025/07/25)
import streamlit as st
import numpy as np
import os, re, time, math
import json5
import cv2
from PIL import Image
from openai import OpenAI
from paddleocr import PaddleOCR
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
from dotenv import load_dotenv

# ===== ✅ .env에서 환경변수 불러오기 =====
load_dotenv(dotenv_path="C:/Users/user/Desktop/최종파일/AI_final_project/.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ===== 페이지 기본 설정 =====
st.set_page_config(
    page_title="📄 OCR + GPT 요약/퀴즈 생성기",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ===== 사이드바 완전 숨기기 =====
st.markdown("""
    <style>
    [data-testid="stSidebar"] {display: none !important;}
    .stTextArea textarea { font-size: 0.95rem; line-height: 1.5; }
    </style>
""", unsafe_allow_html=True)

# ✅ file_uploader key 초기값 설정
if "file_key" not in st.session_state:
    st.session_state.file_key = "uploader_1"

# ✅ 완전 새로고침
st.markdown("<div style='text-align:right'>", unsafe_allow_html=True)
if st.button("🔄 전체 새로고침", key="refresh_all"):
    keys_to_clear = list(st.session_state.keys())
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]
    st.session_state.file_key = "uploader_" + str(np.random.randint(100000))
    st.session_state.quiz_content_input = ""
    st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

# ===== ✅ OpenAI 클라이언트 캐싱 =====
@st.cache_resource
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ .env 파일에서 OpenAI API 키를 찾을 수 없습니다.")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()

# ===== ✅ OCR 캐싱 =====
@st.cache_resource
def get_ocr():
    return PaddleOCR(
        use_textline_orientation=True,   # 최신 파라미터
        lang='korean',
        text_det_box_thresh=0.2,
        text_det_unclip_ratio=2.0,
        ocr_version='PP-OCRv3'
    )
ocr = get_ocr()

# ===== 유틸 =====
def extract_pdf_text_if_possible(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        return "\n".join([(page.extract_text() or "") for page in reader.pages])
    except Exception:
        return ""

def safe_load_json5(text):
    try:
        return json5.loads(text)
    except Exception as e:
        st.error(f"❌ JSON 파싱 실패: {e}")
        st.code(text)
        return []

# === 토큰 보호용 분할 ===
def split_text_by_chars(s: str, max_chars: int):
    paras = re.split(r"\n{2,}", s)
    chunks, buff = [], ""
    for p in paras:
        p = p.strip()
        if not p:
            continue
        if len(buff) + len(p) + 2 <= max_chars:
            buff = (buff + "\n\n" + p).strip()
        else:
            if buff:
                chunks.append(buff)
            if len(p) > max_chars:
                sents = re.split(r"(?<=[.!?。！？])\s+", p)
                cur = ""
                for sent in sents:
                    if len(cur) + len(sent) + 1 <= max_chars:
                        cur = (cur + " " + sent).strip()
                    else:
                        if cur:
                            chunks.append(cur)
                        cur = sent
                if cur:
                    chunks.append(cur)
            else:
                buff = p
    if buff:
        chunks.append(buff)
    return chunks

def gpt_chat(messages, model="gpt-4o-mini", temperature=0.2, max_tokens=None):
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        msg = str(e)
        if "rate_limit_exceeded" in msg or "Request too large" in msg:
            time.sleep(1.2)
        raise

# === 요약 길이 자동 결정(문서 길이 → 목표 줄 수) ===
def target_lines_for_length(n_chars: int) -> int:
    """
    문서 길이에 따라 목표 요약 줄 수를 자동 결정.
    필요하면 구간/값 조정 가능.
    """
    if n_chars < 1500:       # 아주 짧음
        return 4
    elif n_chars < 5000:     # 짧음
        return 6
    elif n_chars < 12000:    # 보통
        return 8
    elif n_chars < 25000:    # 김
        return 10
    elif n_chars < 50000:    # 매우 김
        return 13
    else:                    # 초장문
        return 16

# === 대용량 안전 요약 ===
def summarize_large_text(text, target_lines=8, base_chunk_chars=7000, reduce_chunk_chars=4000):
    """
    1) 본문을 chunk 요약
    2) 부분 요약들을 다시 chunk 요약
    3) 최종 요약으로 축약
    target_lines: 최종 요약 목표 줄 수(자동 결정값 사용)
    """
    if not text or len(text.strip()) == 0:
        return ""

    chunks = split_text_by_chars(text, base_chunk_chars)
    part_summaries = []

    if len(chunks) == 1:
        sys = f"아래 내용을 {max(2, target_lines-1)}~{target_lines+1}줄로 핵심만 간결하게 요약해줘."
        return gpt_chat(
            [{"role": "system", "content": sys},
             {"role": "user", "content": chunks[0]}]
        )

    prog = st.progress(0.0, text="1/3 단계: 부분 요약 중...")
    for i, ck in enumerate(chunks, start=1):
        sys = "아래 텍스트의 핵심 논지/키워드/숫자만 5~7문장으로 요약."
        try:
            ps = gpt_chat(
                [{"role": "system", "content": sys},
                 {"role": "user", "content": ck}]
            )
        except Exception:
            smaller = split_text_by_chars(ck, max(2000, base_chunk_chars // 2))
            local_sum = []
            for sck in smaller:
                ls = gpt_chat(
                    [{"role": "system", "content": sys},
                     {"role": "user", "content": sck}]
                )
                local_sum.append(ls)
            ps = "\n".join(local_sum)
        part_summaries.append(ps)
        prog.progress(i / len(chunks))

    combined = "\n\n".join(part_summaries)
    reduce_chunks = split_text_by_chars(combined, reduce_chunk_chars)
    reduce_summaries = []

    prog = st.progress(0.0, text="2/3 단계: 요약 통합 중...")
    for i, rc in enumerate(reduce_chunks, start=1):
        sys2 = "아래 요약들을 중복 제거하고 핵심만 압축해 4~6문장으로 재요약."
        rs = gpt_chat(
            [{"role": "system", "content": sys2},
             {"role": "user", "content": rc}]
        )
        reduce_summaries.append(rs)
        prog.progress(i / len(reduce_chunks))

    final_source = "\n\n".join(reduce_summaries)
    sys3 = f"전체 내용을 {max(2, target_lines-1)}~{target_lines+1}줄로, 숫자/고유명사 유지하며 최종 요약."
    prog = st.progress(0.0, text="3/3 단계: 최종 요약 정리 중...")
    final = gpt_chat(
        [{"role": "system", "content": sys3},
         {"role": "user", "content": final_source}]
    )
    prog.progress(1.0)
    return final

def summarize_content(content: str):
    """문서 길이를 보고 목표 줄 수를 자동 결정해 요약."""
    if not content or not content.strip():
        return "요약할 내용이 없습니다."
    n = len(content)
    target_lines = target_lines_for_length(n)

    # 사용자가 보이도록 선택된 목표 줄 수 안내(선택)
    st.info(f"📏 문서 길이: 약 {n:,}자 → 목표 요약: **{target_lines}줄**")

    if n <= 5000:
        try:
            sys = f"아래 내용을 {max(2, target_lines-1)}~{target_lines+1}줄로 핵심만 요약해줘."
            return gpt_chat(
                [{"role": "system", "content": sys},
                 {"role": "user", "content": content}]
            )
        except Exception:
            return summarize_large_text(content, target_lines=target_lines)
    else:
        return summarize_large_text(content, target_lines=target_lines)

# === 퀴즈 생성 전 입력 축약 ===
def compact_for_quiz_if_needed(text, max_chars=6000):
    if len(text) <= max_chars:
        return text
    sys = "아래 학습 내용을 퀴즈 생성에 필요한 핵심 개념/정의/수치/관계 위주로 800~1200자로 압축해줘."
    return gpt_chat(
        [{"role": "system", "content": sys},
         {"role": "user", "content": text}]
    )

def generate_quiz(content, quiz_count=8):
    content = compact_for_quiz_if_needed(content, max_chars=6000)

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

- 반드시 'type', 'question', 'answer', 'explanation', 'example' 키 포함
- 'options'는 객관식, OX에만 포함 (주관식/빈칸형 제외)
- JSON 리스트만 출력 (설명문 금지)
- 총 {quiz_count}문제
"""
    try:
        raw = gpt_chat(
            [{"role": "system", "content": prompt},
             {"role": "user", "content": content}],
            model="gpt-4o-mini"
        )
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = re.sub(r"^json", "", raw, flags=re.IGNORECASE).strip()
        parsed = safe_load_json5(raw)
        return parsed[:quiz_count] if isinstance(parsed, list) else []
    except Exception as e:
        st.error(f"❌ 퀴즈 생성 실패: {e}")
        return []

def ask_gpt_about_wrong(problem, user_answer):
    prompt = f"""문제: {problem.get('question','')}
정답: {problem.get('answer','')}
내가 작성한 오답: {user_answer}
왜 틀렸는지 쉽게 설명해줘."""
    return gpt_chat(
        [{"role": "system", "content": "너는 친절한 선생님이야."},
         {"role": "user", "content": prompt}]
    )

def summarize_answer(answer):
    try:
        sys = "아래 내용을 최대 2문장으로 핵심만 요약해줘."
        return gpt_chat(
            [{"role": "system", "content": sys},
             {"role": "user", "content": answer}]
        )
    except:
        return "요약 실패"

# ===== 탭 구성 =====
tab1, tab2 = st.tabs(["📄 PDF요약기", "🧠 퀴즈 생성기"])

with tab1:
    st.header("📄 PDF 요약")
    uploaded_file = st.file_uploader(
        "📤 PDF 또는 이미지 업로드",
        type=["png", "jpg", "jpeg", "pdf"],
        key=st.session_state.file_key
    )

    clean_text = ""
    if uploaded_file:
        is_pdf = (uploaded_file.type == "application/pdf")
        pdf_has_no_text = False

        if is_pdf:
            # 1) 텍스트 레이어 추출
            text = extract_pdf_text_if_possible(uploaded_file)
            if text.strip():
                clean_text = text
                st.success("✅ PDF에서 텍스트 추출 성공")
            else:
                # 2) 스캔 PDF → 이미지 변환 후 OCR
                st.warning("🔎 텍스트 레이어가 없어 보입니다. OCR로 인식합니다.")
                if convert_from_bytes is None:
                    st.error("pdf2image / poppler가 필요합니다. 설치 후 다시 시도하세요.")
                else:
                    images = convert_from_bytes(uploaded_file.read(), dpi=200, fmt='png')
                    ocr_texts = []
                    with st.spinner("OCR 인식 중..."):
                        for i, pil_img in enumerate(images, 1):
                            img_np = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                            result = ocr.ocr(img_np, cls=False)
                            lines = []
                            for det in result:
                                for box, txt in det:
                                    lines.append(txt[0])
                            ocr_texts.append("\n".join(lines))
                            st.write(f"페이지 {i} OCR 완료")
                    clean_text = "\n\n".join(ocr_texts).strip()
                    if clean_text:
                        st.success("✅ OCR 인식 완료")
                    else:
                        pdf_has_no_text = True
                        st.error("❌ OCR로도 텍스트를 추출하지 못했습니다.")
        else:
            # 이미지 파일 OCR
            img = Image.open(uploaded_file).convert("RGB")
            st.image(img, caption="🖼️ 업로드된 이미지", width=600)
            img_np = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            with st.spinner("OCR 인식 중..."):
                result = ocr.ocr(img_np, cls=False)
                lines = []
                for det in result:
                    for box, txt in det:
                        lines.append(txt[0])
                clean_text = "\n".join(lines).strip()
            if clean_text:
                st.success("✅ OCR 인식 완료")
            else:
                st.error("❌ 이미지에서 텍스트를 추출하지 못했습니다.")

        if not pdf_has_no_text and clean_text.strip():
            st.text_area("📝 인식된 텍스트", clean_text, height=250, key="ocr_result_text")
            if st.button("📚 GPT 요약하기"):
                with st.spinner("요약 중... (문서 길이 기반 자동 요약 길이 설정)"):
                    summary = summarize_content(clean_text)  # ← 자동 길이 결정
                    st.session_state.summary = summary
                    st.text_area("📌 요약 결과", summary, height=180, key="summary_text")

with tab2:
    st.header("🧠 퀴즈생성기")

    quiz_count = st.number_input(
        "퀴즈 문제 출제 수는 4개~10개 사이로 사용하세요!",
        min_value=4, max_value=10, value=8, step=1
    )
    content_input = st.text_area(
        "✍️ 학습 내용을 입력하거나 PDF 요약 결과를 사용하세요",
        value=st.session_state.get("quiz_content_input", ""),
        height=200,
        key="quiz_content_input"
    )
    st.markdown("✅ PDF 요약 결과가 있다면 자동으로 그 내용을 사용합니다.")

    if st.button("🧠 퀴즈 생성하기", key="make_quiz"):
        content_to_use = (st.session_state.get("summary", "") or content_input).strip()
        if not content_to_use:
            st.warning("내용을 입력하거나 요약 결과를 생성해주세요.")
        elif len(content_to_use) < 5:
            st.error("❌ 퀴즈를 인식하지 못했습니다.")
        else:
            with st.spinner("GPT가 퀴즈를 생성 중입니다... (장문 자동 압축)"):
                st.session_state.summary_log = summarize_content(content_to_use[:20000])
                st.session_state.quiz_data = generate_quiz(content_to_use, quiz_count)
                st.session_state.user_answers = {}
                st.session_state.wrong_indices = []
                st.session_state.chat_logs = {}
                st.session_state.graded = False

    if st.session_state.get("summary_log"):
        st.info(f"📚 학습 요약:\n\n{st.session_state.summary_log}")

    # ===== 입력 UI =====
    def render_quiz_inputs():
        for idx, quiz in enumerate(st.session_state.quiz_data):
            st.markdown(f"### 문제 {idx + 1} ({quiz.get('type','-')})")
            st.markdown(f"**{quiz.get('question','-')}**")

            qtype = (quiz.get("type") or "").strip()
            key_input = f"input_{idx}"

            if qtype in ["객관식", "OX"]:
                options = quiz.get("options", [])
                if qtype == "OX" and not options:
                    options = ["O", "X"]
                st.session_state.user_answers[idx] = st.selectbox(
                    "정답 선택",
                    options,
                    index=None,
                    placeholder="선택",
                    key=key_input
                )
            else:
                st.session_state.user_answers[idx] = st.text_input("정답 입력", key=key_input)

    # ===== 채점 =====
    def normalize(s):
        if isinstance(s, (list, tuple)):
            return [str(x).strip().lower() for x in s]
        return str(s).strip().lower()

    def is_correct(user, answer):
        u = normalize(user)
        a = normalize(answer)
        if isinstance(a, list):
            return u in a
        return u == a

    if st.session_state.get("quiz_data"):
        render_quiz_inputs()

        if st.button("✅ 전체 채점", key="grade_all"):
            unanswered = [i for i in range(len(st.session_state.quiz_data))
                          if st.session_state.user_answers.get(i, None) in [None, ""]]
            if unanswered:
                st.warning(f"아직 답을 선택/입력하지 않은 문제가 있어요: {', '.join(str(i+1) for i in unanswered)}")
            else:
                st.session_state.wrong_indices = []
                for i, quiz in enumerate(st.session_state.quiz_data):
                    user = st.session_state.user_answers.get(i, "")
                    answer = quiz.get("answer", "")
                    correct = is_correct(user, answer)

                    st.markdown(f"**문제 {i + 1}: {'✅ 정답' if correct else '❌ 오답'}**")
                    st.markdown(f"- 질문: {quiz.get('question', '-')}")
                    if quiz.get("type") in ["객관식", "OX"]:
                        st.markdown(f"- 선택지: {', '.join(quiz.get('options', []))}")
                    st.markdown(f"- 내 답: {user}")
                    st.markdown(f"- 정답: {answer}")
                    st.markdown(f"- 해설: {quiz.get('explanation', '없음')}")
                    st.markdown(f"- 예시: {quiz.get('example', '없음')}")
                    st.markdown("---")

                    if not correct:
                        st.session_state.wrong_indices.append(i)

                st.session_state.graded = True

    # ===== 오답만 GPT에게 질문 =====
    if st.session_state.get("graded") and st.session_state.get("wrong_indices"):
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
                        reply = gpt_chat(
                            [{"role": "system", "content": "친절한 피드백을 제공해줘."}] + chat
                        )
                        chat.append({"role": "assistant", "content": reply})
                        st.session_state.chat_logs[question_key] = chat
                        st.session_state[f"last_reply_{i}"] = reply
