import streamlit as st
from paddleocr import PaddleOCR
import cv2
import numpy as np
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv
import re
from pdf2image import convert_from_bytes
from PyPDF2 import PdfReader
import os

# 🔐 OpenAI API 키 설정
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)   # ← 요렇게!

# 🧠 PaddleOCR 설정
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='korean',
    det_db_box_thresh=0.2,
    det_db_unclip_ratio=2.0,
    # use_dilation=True,
    ocr_version='PP-OCRv3'
)

# Streamlit 설정
st.set_page_config(page_title="📄 OCR + GPT 요약기", layout="centered")
st.title("✍️ 한글 손글씨 이미지/PDF OCR + GPT 요약")

# 📄 텍스트 기반 PDF 추출 함수
def extract_pdf_text_if_possible(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
        return text
    except Exception:
        return ""

# ✂️ 박스 좌표로 이미지 자르기
def crop_image(image_np, coords):
    coords = np.array(coords).reshape(-1, 2).astype(np.int32)
    x_min = np.min(coords[:, 0])
    y_min = np.min(coords[:, 1])
    x_max = np.max(coords[:, 0])
    y_max = np.max(coords[:, 1])
    return image_np[y_min:y_max, x_min:x_max]

# 📤 파일 업로드
uploaded_file = st.file_uploader("📤 이미지 또는 PDF 업로드", type=["png", "jpg", "jpeg", "pdf"])

if uploaded_file:
    is_pdf = uploaded_file.type == "application/pdf"
    clean_text = ""

    # ✅ 1단계: 텍스트 PDF 여부 확인
    if is_pdf:
        text = extract_pdf_text_if_possible(uploaded_file)
        if text.strip():  # 텍스트가 있으면 OCR 생략
            clean_text = text
            st.success("✅ PDF에서 직접 텍스트 추출 성공 (OCR 생략)")
        else:
            # 텍스트가 없으면 OCR 수행
            uploaded_file.seek(0)
            images = convert_from_bytes(uploaded_file.read(), dpi=300)
            st.image(images[0], caption="📄 PDF 첫 페이지", width=600)
    else:
        img = Image.open(uploaded_file).convert("RGB")
        images = [img]
        st.image(img, caption="🖼️ 업로드된 이미지", width=600)

    # OCR 수행이 필요한 경우
    if clean_text == "" and st.button("🔍 OCR + 요약 실행"):
        full_text = ""

        for idx, image in enumerate(images):
            # 이미지 전처리
            img_np = np.array(image)
            img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
            enhanced = clahe.apply(gray)
            resized = cv2.resize(enhanced, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

            temp_path = f"temp_{idx}.png"
            cv2.imwrite(temp_path, resized)

            result = ocr.ocr(temp_path, det=True, rec=False, cls=True)
            st.write(f"검출된 박스 수: {len(result[0]) if result else 0}")

            for i, line in enumerate(result[0]):
                coords = line[0]
                cropped = crop_image(resized, coords)

                if cropped.size == 0 or cropped.shape[0] < 5 or cropped.shape[1] < 5:
                    continue

                cropped_rgb = cv2.cvtColor(cropped, cv2.COLOR_GRAY2RGB)
                rec_result = ocr.ocr(cropped_rgb, det=False, rec=True, cls=True)

                if rec_result and rec_result[0]:
                    text = rec_result[0][0][0]
                    full_text += text + "\n"

            os.remove(temp_path)

        clean_text = re.sub(r'[^\uAC00-\uD7A3\s\w.,!?()\[\]{}\-]', '', full_text)

        if clean_text.strip() == "":
            st.error("😥 글자를 인식하지 못했습니다. 이미지 해상도나 필기 선명도를 높여보세요.")
        else:
            st.success("✅ OCR 성공. GPT 요약을 시작합니다.")

    # ✅ GPT 요약 실행
    if clean_text.strip():
        st.subheader("📝 인식된 텍스트")
        st.text_area("텍스트", clean_text, height=300)

        with open("ocr_result.txt", "w", encoding="utf-8") as f:
            f.write(clean_text)

        with st.spinner("📚 GPT로 요약 중..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "당신은 손글씨 또는 보고서 내용을 자연스럽게 요약하는 전문가입니다."},
                        {"role": "user", "content": f"다음은 추출된 텍스트입니다. 자연스럽게 요약해줘:\n{clean_text}"}
                    ]
                )
                summary = response.choices[0].message.content.strip()
                st.subheader("📌 요약 결과")
                st.text_area("요약된 텍스트", summary, height=200)

                with open("summary_result.txt", "w", encoding="utf-8") as f:
                    f.write(summary)
                st.success("📄 요약 결과가 'summary_result.txt'에 저장되었습니다.")
            except Exception as e:
                st.error(f"❌ 요약 중 오류 발생:\n\n{e}")
