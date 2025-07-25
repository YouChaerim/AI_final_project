import cv2
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,                   # 한 번에 한 명만 분석
    refine_landmarks=True,
    min_detection_confidence=0.3,
    min_tracking_confidence=0.3
)

LEFT_EYE = [33, 133, 153, 144, 163, 7]
RIGHT_EYE = [362, 263, 383, 373, 390, 249]
blink_threshold = 15  # 👈 환경에 따라 조정 필요 (면적 기준값)

def detect_blink(image):
    '''
    [입력]
        image : BGR 형식의 numpy 배열 (스트림릿 프레임)
    [출력]
        눈 깜빡임 표시, 윤곽선 시각화가 추가된 이미지(numpy)
    '''
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)      # mediapipe는 RGB 사용
    results = face_mesh.process(rgb)                  # 얼굴 랜드마크 추출

    if results.multi_face_landmarks:                  # 얼굴이 검출된 경우
        for face_landmarks in results.multi_face_landmarks:
            # 왼쪽/오른쪽 눈 윤곽 좌표 계산 (픽셀 단위)
            left_eye_points = np.array([
                (face_landmarks.landmark[i].x * image.shape[1],
                 face_landmarks.landmark[i].y * image.shape[0]) for i in LEFT_EYE
            ], np.int32)
            right_eye_points = np.array([
                (face_landmarks.landmark[i].x * image.shape[1],
                 face_landmarks.landmark[i].y * image.shape[0]) for i in RIGHT_EYE
            ], np.int32)

            # 눈 영역의 면적 계산
            left_eye_area = cv2.contourArea(left_eye_points)
            right_eye_area = cv2.contourArea(right_eye_points)

            # ---- [깜빡임 인식] ----
            if left_eye_area < blink_threshold or right_eye_area < blink_threshold:
                cv2.putText(image, "Blink", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)  # 빨간색
            else:
                cv2.putText(image, "Open", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)   # 초록색

            # ---- [눈 경계 표시(윤곽선)] ----
            cv2.polylines(image, [left_eye_points], isClosed=True, color=(0, 255, 0), thickness=1)
            cv2.polylines(image, [right_eye_points], isClosed=True, color=(0, 255, 0), thickness=1)
    return image
