import streamlit as st
from paddleocr import PaddleOCR, draw_ocr
import cv2
import numpy as np
from PIL import Image
import openai
import os

# ✅ OpenAI API 키 (환경변수 또는 직접 입력)
openai.api_key = "open api key"  # 🔒 반드시 자신의 키로 변경

# ✅ OCR 객체 초기화 (한글 인식 최적화)
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='korean',
    ocr_version='PP-OCRv3',
    show_log=False
)

# ✅ Streamlit 설정
st.set_page_config(page_title="한글 손글씨 OCR + 요약", layout="centered")
st.title("✍️ 한글 손글씨 인식 및 요약")

# ✅ 파일 업로드
uploaded_file = st.file_uploader("📤 손글씨 이미지 업로드", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="🖼️ 업로드한 이미지", width=600)

    if st.button("🧠 OCR 실행 및 요약"):
        with st.spinner("🔍 텍스트 인식 중..."):

            # PIL → OpenCV
            img = np.array(image)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            # ✅ 전처리
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (3, 3), 0)
            thresh = cv2.adaptiveThreshold(
                blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 15, 8
            )
            resized = cv2.resize(thresh, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            cv2.imwrite("temp_input.png", resized)

            # ✅ PaddleOCR 실행
            result = ocr.ocr("temp_input.png", cls=True)

            # ✅ 결과 추출
            result_text = ''
            for line in result[0]:
                result_text += line[1][0] + '\n'

            st.subheader("📝 인식된 텍스트")
            st.text_area("OCR 결과", result_text, height=250)

            with open("ocr_result_paddle.txt", "w", encoding="utf-8") as f:
                f.write(result_text)

            st.success("📁 텍스트가 'ocr_result_paddle.txt'로 저장되었습니다.")

        # ✅ GPT 요약
        with st.spinner("✏️ 요약 중입니다..."):
            try:
                prompt = f"다음 내용을 한글로 요약해줘:\n\n{result_text}"
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "너는 한국어 요약 도우미야."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=300
                )
                summary = response["choices"][0]["message"]["content"].strip()
                st.subheader("🧾 요약 결과")
                st.write(summary)

            except Exception as e:
                st.error(f"❌ 요약 중 오류 발생: {str(e)}")

