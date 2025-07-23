# 생성형 AI를 활용한 인공지능 개발 어플리케이션

본 프로젝트는 사용자의 공부 시간과 필기 내용을 데이터화·분석하여,
맞춤형 학습 습관 형성과 학습 효과 극대화를 지원하는 AI 기반 통합 학습 지원 시스템입니다.

* **웹캠 기반 집중도 분석**
* **손글씨 OCR 및 요약/이해도 분석**
* **공부 리포트 자동 생성 및 시각화**

## Naming

### Feature

### Commit 명명 규칙

* feat : 기능 추가
* fix : 기능 수정
* docs : 문서 수정
* delete : 기능 삭제

### Branch

* Main
* Develop
* chae : 유채림
* yuguemjae : 유금재
* JEONGHYEONWOO : 정현우
* OhSeokHwan : 오석환


## 📂 프로젝트 파일 구조 및 설명



## 개발 환경 세팅

### 🔸 Anaconda(Conda) 설치

[공식 다운로드 아카이브](https://repo.anaconda.com/archive/)

* **Windows:**
  `Anaconda3-2024.10-1-Windows-x86_64.exe`
* **Mac:**

  * **Intel:** `Anaconda3-2024.10-1-MacOSX-x86_64.pkg`
  * **Apple Silicon(M1/M2/M3):** `Anaconda3-2024.10-1-MacOSX-arm64.pkg`

### 🔸 Conda 가상환경 생성

```
conda create -n final python=3.10
conda activate final
```

### PDF 처리용 Poppler 설치

#### Mac
```
brew install poppler
```
* 별도의 환경 변수 설정 불필요 (자동 등록)

#### Windows

1. [Poppler 공식 릴리즈](https://github.com/oschwartz10612/poppler-windows/releases)에서 다운로드 후 압축 해제
2. `Library\bin` 폴더 경로를 복사
3. 환경 변수(PATH)에 해당 경로를 추가하거나, 파이썬 코드 상단에 아래와 같이 직접 추가:

   ```
   import os
   os.environ["PATH"] += os.pathsep + r"C:\Your\Poppler\Library\bin"
   ```

   ※ 본인 PC 환경에 맞게 경로 수정
### PaddleOCR 및 PaddlePaddle 설치

#### Mac/Windows 공통

```
pip install paddleocr paddlepaddle
```

* **Apple Silicon(M1/M2/M3) Mac:**

  * 현재 CPU-only(그래픽카드 가속 미지원)
  * 필요 시 Rosetta 터미널에서 설치/실행 권장

## 🔸 필수 라이브러리 설치

`requirements.txt` 파일을 이용하여 필요한 패키지를 한 번에 설치할 수 있습니다.

```
pip install -r requirements.txt
```

### 📦 주요 라이브러리 역할 안내

| 라이브러리           | 역할/설명                                                                                                 |
|----------------------|-----------------------------------------------------------------------------------------------------------|
| **streamlit**        | 파이썬 기반 웹 UI/대시보드 개발 프레임워크. 프로젝트 전반의 웹 인터페이스 구현에 사용                      |
| **streamlit-webrtc** | Streamlit에서 웹캠 등 실시간 비디오/오디오 스트림 기능 제공. 집중도 분석 기능 구현에 필요                  |
| **opencv-python**    | 이미지 및 비디오 처리, 컴퓨터 비전 기능 구현(얼굴/눈 인식, 손글씨 분석 등)                               |
| **mediapipe**        | 실시간 얼굴/손/포즈 인식용 ML 파이프라인. 눈 깜빡임 등 집중도 분석에 활용                                |
| **numpy**            | 다차원 배열 및 과학/수치 연산 라이브러리. 이미지/영상 데이터 처리에 활용                                  |
| **paddleocr**        | PaddlePaddle 기반 OCR(광학 문자 인식) 라이브러리. 한글 포함 손글씨/이미지 텍스트 추출                     |
| **pillow**           | 이미지 로딩 및 저장, 변환 등(PIL 라이브러리. 이미지 파일 처리 및 변환에 사용)                             |
| **pdf2image**        | PDF 파일을 이미지(예: PNG, JPEG)로 변환. 스캔본 PDF 등 비텍스트 PDF의 OCR 처리를 지원                     |
| **PyPDF2**           | PDF 파일에서 텍스트 직접 추출. 텍스트 기반 PDF의 빠른 처리를 위해 사용                                    |
| **openai**           | OpenAI GPT API 호출용 공식 라이브러리. 텍스트 요약, 퀴즈 생성 등 생성형 AI 서비스 구현에 사용              |
| **python-dotenv**    | .env 파일의 환경 변수(API 키 등)를 파이썬에서 쉽게 불러오기 위한 라이브러리                               |

## 실행 명령어

```
streamlit run main.py
streamlit run quiz_app.py
streamlit run ocr_paddle_summary_web.py
```
