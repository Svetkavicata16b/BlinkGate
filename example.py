import time

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
import math


def euclidean_dist(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

vc = cv2.VideoCapture(0)

model_path = "resources/face_landmarker.task"

BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = vision.FaceLandmarker
FaceLandmarkerOptions = vision.FaceLandmarkerOptions
FaceLandmarkerResult = mp.tasks.vision.FaceLandmarkerResult
VisionRunningMode = vision.RunningMode

options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path, delegate=None),
    running_mode=VisionRunningMode.VIDEO
)

landmarker = FaceLandmarker.create_from_options(options)
start_time = time.time()
frame_id = 0

while True:
    success, frame = vc.read()

    if not success:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    timestamp_ms = int((time.time() - start_time) * 1000)

    face_landmarker_result = landmarker.detect_for_video(mp_image, timestamp_ms)

    if len(face_landmarker_result.face_landmarks) != 0:
        fl = face_landmarker_result.face_landmarks[0]
        left_eye_ear = euclidean_dist(fl[374], fl[386]) / euclidean_dist(fl[263], fl[362])
        right_eye_ear = euclidean_dist(fl[145], fl[159]) / euclidean_dist(fl[133], fl[33])

        print(left_eye_ear)
        print(right_eye_ear)
        print()

        if left_eye_ear < 0.15 and right_eye_ear < 0.15:
            break

vc.release()
cv2.destroyAllWindows()
landmarker.close()