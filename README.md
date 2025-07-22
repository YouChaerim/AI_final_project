# 생성형 AI를 활용한 인공지능 개발 어플리케이션

본 프로젝트는 사용자의 공부 시간과 필기 내용을 데이터화·분석하여,
맞춤형 학습 습관 형성과 학습 효과 극대화를 지원하는 AI 기반 통합 학습 지원 시스템입니다.

웹캠 기반 집중도 분석
- 손글씨 OCR 및 요약/이해도 분석
- 공부 리포트 자동 생성 및 시각화

## Naming
### Feature
### Commit 명명 규칙
feat : 기능 추가 fix : 기능 수정 docs : 문서 수정 delete : 기능 삭제

### Branch
Main Develop

chae : 유채림 yuguemjae : 유금재 JEONGHYEONWOO : 정현우 OhSeokHwan : 오석환

## 📂 프로젝트 파일 구조 및 설명


## 개발 환경 세팅

### 🔸 Anaconda(Conda) 설치

#### [공식 다운로드 아카이브](https://repo.anaconda.com/archive/)

- **Windows:**  
  `Anaconda3-2024.10-1-Windows-x86_64.exe`
- **Mac:**  
  - **Intel:** `Anaconda3-2024.10-1-MacOSX-x86_64.pkg`
  - **Apple Silicon(M1/M2/M3):** `Anaconda3-2024.10-1-MacOSX-arm64.pkg`

### 🔸 Conda 가상환경 생성
```
bash
conda create -n final python=3.10
conda activate final
```

## 설치 명령어
```
pip install streamlit streamlit-webrtc opencv-python
pip install opencv-python mediapipe numpy
```

## 실행 명령어
```
streamlit run main.py
```