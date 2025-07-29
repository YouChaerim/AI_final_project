import mediapipe as mp
import numpy as np
import cv2

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

MOUTH_LANDMARKS = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]

def detect_yawn(image):
    '''
    입력: image (BGR numpy array)
    출력: (윤곽선/수치 표시된 이미지, is_yawning (bool), ratio (float))
    '''
    h, w, _ = image.shape
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(img_rgb)
    is_yawning = False
    ratio = 0.0

    if result.multi_face_landmarks:
        for landmarks in result.multi_face_landmarks:
            # --- 입 중앙 상하좌우 ---
            top = landmarks.landmark[13]
            bottom = landmarks.landmark[14]
            left = landmarks.landmark[78]
            right = landmarks.landmark[308]

            top_y = int(top.y * h)
            bottom_y = int(bottom.y * h)
            left_x = int(left.x * w)
            right_x = int(right.x * w)
            mouth_open = abs(bottom_y - top_y)
            mouth_width = abs(right_x - left_x)
            ratio = mouth_open / (mouth_width + 1e-6)
            is_yawning = ratio > 0.55

            # --- 입 윤곽선 폴리라인 ---
            mouth_points = np.array([
                (int(landmarks.landmark[i].x * w), int(landmarks.landmark[i].y * h))
                for i in MOUTH_LANDMARKS
            ], np.int32)
            cv2.polylines(image, [mouth_points], isClosed=True, color=(255, 0, 255), thickness=2)

            # --- (선택) 중앙 세로선/가로선 시각화 ---
            cv2.line(image, ((left_x+right_x)//2, top_y), ((left_x+right_x)//2, bottom_y), (255,0,0), 2)
            cv2.line(image, (left_x, (top_y+bottom_y)//2), (right_x, (top_y+bottom_y)//2), (0,255,0), 2)
            
            # (Yawn Ratio 텍스트는 main.py에서 그림)
            break

    return image, is_yawning, ratio
