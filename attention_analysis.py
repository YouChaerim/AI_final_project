import cv2
import numpy as np
import time

from EyeControl import detect_blink, LEFT_EYE, RIGHT_EYE
from YawnControl import detect_yawn

def yolo_detect_face(frame):
    h, w, _ = frame.shape
    return [(int(w*0.3), int(h*0.2), int(w*0.7), int(h*0.8))]

def main():
    cap = cv2.VideoCapture(0)
    blink_count = 0
    yawn_count = 0
    last_blink = False
    last_yawn = False
    FPS = cap.get(cv2.CAP_PROP_FPS) or 30

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        faces = yolo_detect_face(frame)
        for (x1, y1, x2, y2) in faces:
            face_roi = frame[y1:y2, x1:x2]

            # 1. 눈 깜빡임 분석
            roi_eye, is_blink = detect_blink(face_roi)

            # 2. 하품 감지 (detect_yawn 함수 사용)
            roi_yawn, is_yawning, yawn_ratio = detect_yawn(face_roi)

            # Blink 카운트: True로 바뀔 때만 +1
            if is_blink and not last_blink:
                blink_count += 1
            last_blink = is_blink

            # Yawn 카운트: True로 바뀔 때만 +1
            if is_yawning and not last_yawn:
                yawn_count += 1
            last_yawn = is_yawning

            # ROI에 시각화 반영: 하품 윤곽선 포함
            # 눈과 입 모두 그려진 이미지를 합치고 싶다면 둘 중 하나 선택(여기선 roi_yawn을 사용)
            face_result = roi_yawn

            frame[y1:y2, x1:x2] = face_result

            # 얼굴 박스
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)

            # 하품 ratio 텍스트 (필요시)
            cv2.putText(frame, f'Yawn Ratio: {yawn_ratio:.2f}', (x1, y2+55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,255), 2)

        # 실시간 카운트
        cv2.putText(frame, f'Blinks: {blink_count}', (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,0), 2)
        cv2.putText(frame, f'Yawns: {yawn_count}', (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,100,100), 2)

        cv2.imshow('Attention Analysis', frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
