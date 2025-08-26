# 생성형 AI를 활용한 인공지능 개발 어플리케이션

사용자의 **공부 시간·행동·필기 데이터를 통합 분석**하여
맞춤형 학습 습관 형성과 학습 효과 극대화를 지원하는 **AI 기반 통합 학습 지원 시스템**입니다.

* **웹캠 기반 집중도 분석 (YOLO)**: 깜빡임/하품/고개 자세·시선 패턴을 실시간 측정
* **손글씨 OCR → 요약/이해도/퀴즈**: PDF/이미지에서 텍스트 추출 후 요약 및 자동 퀴즈 생성
* **RAG 기반 문서 Q\&A**: ChromaDB + OpenAI 임베딩(`text-embedding-3-small`)로 맥락 질의응답
* **포인트/리포트/랭킹**: 공부 시간·활동 기반 포인트 지급, 리포트 자동 생성, 팀 내 랭킹
* **카카오 소셜 로그인 + 세션 유지**: 최초 동의 후 자동 로그인 옵션 제공

---

## Naming

### Commit 명명 규칙 (Conventional Commits 권장)

* `feat:` 기능 추가
* `fix:` 버그 수정
* `docs:` 문서 변경
* `delete:` 파일/기능 제거

### Branch 정책

* `main`: 배포/시연용 안정 브랜치
* `develop`: 통합 개발 브랜치
* 개인 브랜치:

  * `chae` (유채림), `yuguemjae` (유금재), `JEONGHYEONWOO` (정현우), `OhSeokHwan` (오석환)

---

## 개발 환경 세팅

### 1) Anaconda(Conda) 설치

* [공식 다운로드 아카이브](https://repo.anaconda.com/archive/)

  * **Windows:** `Anaconda3-2024.10-1-Windows-x86_64.exe`
  * **Mac(Intel):** `Anaconda3-2024.10-1-MacOSX-x86_64.pkg`
  * **Mac(Apple Silicon M1/M2/M3):** `Anaconda3-2024.10-1-MacOSX-arm64.pkg`

### 2) Conda 가상환경 생성

```bash
conda create -n final python=3.10
conda activate final
```

### 3) 필수 라이브러리 설치

#### 프론트(스트림릿) 측

```bash
pip install -r requirements.txt
```

#### 서버(FastAPI) 측

```bash
pip install -r server/requirements.txt
```

### 4) PDF 처리용 Poppler

**Mac**

```bash
brew install poppler
```

(자동 등록, 별도 PATH 설정 불필요)

**Windows**

1. [Poppler 릴리즈](https://github.com/oschwartz10612/poppler-windows/releases) 다운로드 후 압축 해제
2. `Library\bin` 경로 복사
3. PATH에 추가하거나 파이썬 코드에서:

```python
import os
os.environ["PATH"] += os.pathsep + r"C:\Your\Poppler\Library\bin"
```

### 5) PaddleOCR / PaddlePaddle

```bash
pip install paddleocr paddlepaddle
```

* **Apple Silicon(M1/M2/M3)**: CPU-only 동작(그래픽 가속 미지원), 필요시 Rosetta 터미널에서 설치/실행 권장

---

## ▶ 실행 방법

**터미널 2개**를 사용합니다.

### 1) 백엔드(FastAPI)

```bash
# 프로젝트 루트에서
uvicorn server.app:app --reload --host 0.0.0.0 --port 8080
```

### 2) 프론트(Streamlit)

```bash
# 온보딩+로그인 통합 페이지(권장)
streamlit run onboarding.py
```

---

## 🧩 핵심 기능 요약

1. **집중도 분석(웹캠 + YOLO)**

   * `streamlit-webrtc`로 실시간 스트림 수집
   * 깜빡임/하품/고개 자세 등 이벤트 기반 집중도 스코어링
   * 세션 시작/일시정지/종료, 상태 표시, 포인트 지급 로직 연동

2. **OCR → 요약/퀴즈 생성**

   * `PaddleOCR`로 이미지/PDF 텍스트 추출 (`pdf2image` + `PyPDF2` 병행)
   * `summarizer.py` 요약/키워드/핵심 문장
   * `quiz_generator.py`로 자동 퀴즈(객관식/주관식), 난이도/문항 수 조절, 포인트 베팅

3. **RAG(Q\&A)**

   * `rag_utils.py` + `ChromaDB` + `text-embedding-3-small`
   * 문서/강의노트 업로드 → 벡터화 → 맥락 질의응답

4. **리포트/랭킹**

   * 기간 필터(주/월)별 공부 시간, 집중도 이벤트, 포인트 추이 시각화
   * 팀 내 랭킹/뱃지/히스토리 제공

5. **인증/세션**

   * 카카오 로그인(최초 동의), 재방문 자동 로그인(옵션)
   * `components/header.py` + `auth.py`로 공통 헤더, 세션 유지

---

## 📚 RAG(벡터DB) 준비

* 기본적으로 업로드 시 **임베딩 → 인덱스**가 자동 생성되도록 구성되어 있습니다.
* 초기화/수동 구축이 필요하면(선택):

  1. `.env`의 `CHROMA_DB_PATH` 확인
  2. 초기 임베딩 스크립트(있는 경우) 실행 또는 앱 내 업로드로 구축

> 임베딩 모델은 `text-embedding-3-small`(기본). 변경 시 `.env`의 `EMBEDDING_MODEL` 수정.