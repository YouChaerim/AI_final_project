import cv2
import numpy as np
import time
from EyeControl import detect_blink
from YawnControl import detect_yawn

def yolo_detect_face(frame):
    h, w, _ = frame.shape
    return [(int(w*0.3), int(h*0.2), int(w*0.7), int(h*0.8))]

def clamp(x, minimum, maximum):
    return max(minimum, min(x, maximum))

def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    blink_count = 0
    yawn_count = 0
    last_blink = False
    last_yawn = False

    start_time = time.time()
    last_minute = int(start_time // 60)
    blinks_per_minute = []
    current_minute_blinks = 0

    attention = 100
    close_start = None
    closed_frames = 0

    FPS = cap.get(cv2.CAP_PROP_FPS) or 30

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        faces = yolo_detect_face(frame)
        for (x1, y1, x2, y2) in faces:
            face_roi = frame[y1:y2, x1:x2]

            # 1. 눈 깜빡임 분석 (깜빡임: 감았다가 떴을 때 0.1~0.3초, 졸음: 0.5초 이상 감음)
            roi_eye, is_blink = detect_blink(face_roi)

            if is_blink:
                if close_start is None:
                    close_start = time.time()
                closed_frames += 1
            else:
                if close_start is not None:
                    close_duration = time.time() - close_start
                    # 졸음 기준: 눈 감은 시간 0.5초 이상
                    if close_duration >= 0.5:
                        attention -= 5
                    # 깜빡임 카운트(눈 감은 시간 0.1~0.3초)
                    elif 0.1 <= close_duration <= 0.3:
                        blink_count += 1
                        current_minute_blinks += 1
                    close_start = None
                    closed_frames = 0
            last_blink = is_blink

            # 2. 하품 감지
            roi_yawn, is_yawning, yawn_ratio = detect_yawn(face_roi)
            if is_yawning and not last_yawn:
                yawn_count += 1
                attention -= 2
            last_yawn = is_yawning

            # 시각화는 하품 기준 이미지
            face_result = roi_yawn
            frame[y1:y2, x1:x2] = face_result

            # 얼굴 박스
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)

        # 분당 깜빡임 카운트 감점
        now = time.time()
        cur_minute = int(now // 60)
        if cur_minute != last_minute:
            blinks_per_minute.append(current_minute_blinks)
            if len(blinks_per_minute) > 2:
                recent_blinks = sum(blinks_per_minute[-2:]) / 2
            else:
                recent_blinks = current_minute_blinks

            # 표 기준: 5회 미만/25회 초과 → 감점
            if recent_blinks < 5 or recent_blinks > 25:
                attention -= 2
            current_minute_blinks = 0
            last_minute = cur_minute

        # 집중도 clamp
        attention = clamp(attention, 0, 100)

        # 집중도 %만 화면에 표시
        cv2.putText(frame, f'Attention: {attention:.0f}%', (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 200, 255), 4)

        cv2.imshow('Attention Analysis', frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
