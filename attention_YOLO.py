import cv2
import time
import json
import os
from collections import deque
from datetime import datetime
from ultralytics import YOLO

# 사용자 ID 기반 저장 파일
USER_ID = "user01"
USER_DATA_PATH = f"user_yawn_data_{USER_ID}.json"

# YOLO 모델 로드
model = YOLO("runs/detect/train24-mixtrain/weights/best.pt")
YAWN_CLASS_INDEX = 2       # 하품 클래스 인덱스 (yawning)
DROWSY_CLASS_INDEX = 3     # 졸음 클래스 인덱스 (drowsy eyes)

# 사용자 데이터 로딩
def load_user_data():
    if os.path.exists(USER_DATA_PATH):
        with open(USER_DATA_PATH, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ JSON 파일 손상 → 기본값으로 초기화")
    return {
        "threshold_ratio": 0.4, 
        "min_duration_sec": 0.5,
        "avg_yawn_duration": 1.0,
        "yawn_events": [],
        "sleep_events": []
    }

# 사용자 데이터 저장
def save_user_data(data):
    with open(USER_DATA_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

user_data = load_user_data()
yawn_events = user_data.get("yawn_events", [])
sleep_events = user_data.get("sleep_events", [])
# 세션 시작 시 인덱스 기준 저장
initial_yawn_len = len(yawn_events)
initial_sleep_len = len(sleep_events)
BASE_ATTENTION = 100

# 슬라이딩 윈도우 설정
cap = cv2.VideoCapture(0)
FPS = cap.get(cv2.CAP_PROP_FPS) or 30
WINDOW_SECONDS = 3
WINDOW_SIZE = int(FPS * WINDOW_SECONDS)
yawn_window = deque(maxlen=WINDOW_SIZE)
weights = [i / WINDOW_SIZE for i in range(1, WINDOW_SIZE + 1)]

# 졸음 감지용 슬라이딩 윈도우
DROWSY_SECONDS = 2
DROWSY_FRAMES = int(FPS * DROWSY_SECONDS)
drowsy_window = deque(maxlen=DROWSY_FRAMES)

# 개인화된 감지 기준
threshold_ratio = user_data["threshold_ratio"]
min_yawn_duration = int(FPS * user_data["min_duration_sec"])
yawning = False
sleeping = False
yawn_start_time = None
sleep_start_time = None
durations = []

def detect_yawn(result):
    return any(int(box[5]) == YAWN_CLASS_INDEX for box in result.boxes.data)

def detect_drowsy(result):
    return any(int(box[5]) == DROWSY_CLASS_INDEX for box in result.boxes.data)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model.predict(frame, conf=0.5, verbose=False)[0]
    is_yawning = detect_yawn(results)
    is_drowsy = detect_drowsy(results)
    yawn_window.append(is_yawning)
    drowsy_window.append(is_drowsy)

    # 바운딩박스 시각화
    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        conf = float(box.conf[0])
        cls_id = int(box.cls[0])
        label = f"{model.names[cls_id]} {conf:.2f}"
        color = (0, 0, 255) if cls_id == YAWN_CLASS_INDEX else (255, 255, 0) if cls_id == DROWSY_CLASS_INDEX else (0, 255, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2) #제거해도 상관X 
        
    # 실시간 attention 계산은 새롭게 쌓인 이벤트만 대상으로 함
    yawn_count = sum(1 for event in yawn_events[initial_yawn_len:] if event["type"] == "yawn_end")
    sleep_count = sum(1 for event in sleep_events[initial_sleep_len:] if event["type"] in ["end", "drowys_end"])
    attention_score = BASE_ATTENTION - (5 * sleep_count) - (2 * yawn_count)

  

    # 하품 판단
    weighted_sum = sum(w for yawning, w in zip(yawn_window, weights) if yawning)
    weighted_ratio = weighted_sum / sum(weights)

    continuous_count = 0
    for status in reversed(yawn_window):
        if status:
            continuous_count += 1
        else:
            break

    if weighted_ratio > threshold_ratio and continuous_count > min_yawn_duration:
        if not yawning:
            print("🟠 하품 시작")
            yawning = True
            yawn_start_time = time.time()
            yawn_events.append({
                "type": "start",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    else:
        if yawning:
            print("🟢 하품 종료")
            yawning = False
            if yawn_start_time:
                duration = time.time() - yawn_start_time
                durations.append(duration)
                yawn_start_time = None
            yawn_events.append({
                "type": "yawn_end",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "avg_yawn_duration" : round((sum(durations) / len(durations)),2),
                "attention_score" : attention_score
            })

    # 졸음 판단
    if sum(drowsy_window) >= DROWSY_FRAMES * 0.8:
        if not sleeping:
            print("🔴 졸음 감지됨")
            sleeping = True
            sleep_start_time = time.time()
            sleep_events.append({
                "type": "start",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    else:
        if sleeping:
            print("🟢 졸음 해제")
            sleeping = False
            if sleep_start_time:
                sleep_events.append({
                    "type": "drowys_end",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "attention_score": attention_score
                })
                sleep_start_time = None
                
                # 집중도 초기값




    cv2.putText(frame, f"Attention: {attention_score}", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
    # 시각화 텍스트
    status_text = "Yawning" if yawning else "Sleeping" if sleeping else "Awake"
    status_color = (0, 0, 255) if yawning else (255, 255, 0) if sleeping else (0, 255, 0)
    cv2.putText(frame, f"Status: {status_text}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, status_color, 3)
    cv2.imshow("Real-Time Monitor", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

# 평균 하품 시간 저장
if durations:
    avg_duration = sum(durations) / len(durations)
    user_data["avg_yawn_duration"] = round(avg_duration, 2) 

# 사용자 데이터 저장
user_data["threshold_ratio"] = threshold_ratio
user_data["min_duration_sec"] = min_yawn_duration / FPS
user_data["yawn_events"] = yawn_events
user_data["sleep_events"] = sleep_events
save_user_data(user_data)

cap.release()
cv2.destroyAllWindows()
print(f"✅ 사용자 상태 저장 완료: {USER_DATA_PATH}")
