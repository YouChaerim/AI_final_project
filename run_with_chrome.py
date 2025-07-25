import subprocess
import webbrowser
import time
import os

# 크롬 브라우저 경로 설정 (Windows 기준)
CHROME_PATH = "C:/Program Files/Google/Chrome/Application/chrome.exe %s"

def open_chrome():
    time.sleep(2)  # Streamlit 서버가 열릴 때까지 대기
    webbrowser.get(CHROME_PATH).open("http://localhost:8501")

if __name__ == "__main__":
    # Streamlit 앱 실행 (파일 이름을 ocr_gpt_app.py 또는 실제 파일명으로)
    subprocess.Popen(["streamlit", "run", "ocr_paddle_summary_web.py"], shell=True)
    open_chrome()
