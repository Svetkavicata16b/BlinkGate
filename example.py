# Example for mediapipe with OpenCV using video

# import time
# import cv2
# import mediapipe as mp
# from mediapipe.tasks.python import vision
# import math
#
#
# def euclidean_dist(a, b):
#     return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
#
# vc = cv2.VideoCapture(0)
#
# model_path = "resources/face_landmarker.task"
#
# BaseOptions = mp.tasks.BaseOptions
# FaceLandmarker = vision.FaceLandmarker
# FaceLandmarkerOptions = vision.FaceLandmarkerOptions
# FaceLandmarkerResult = mp.tasks.vision.FaceLandmarkerResult
# VisionRunningMode = vision.RunningMode
#
# options = FaceLandmarkerOptions(
#     base_options=BaseOptions(model_asset_path=model_path, delegate=None),
#     running_mode=VisionRunningMode.VIDEO
# )
#
# landmarker = FaceLandmarker.create_from_options(options)
# start_time = time.time()
# frame_id = 0
# cv2.namedWindow("preview")
#
# while True:
#     success, frame = vc.read()
#
#     if not success:
#         break
#
#     cv2.imshow("preview", frame)
#     key = cv2.waitKey(20)
#
#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
#
#     timestamp_ms = int((time.time() - start_time) * 1000)
#
#     face_landmarker_result = landmarker.detect_for_video(mp_image, timestamp_ms)
#
#     if len(face_landmarker_result.face_landmarks) != 0:
#         fl = face_landmarker_result.face_landmarks[0]
#         # left_eye_ear = euclidean_dist(fl[374], fl[386]) / euclidean_dist(fl[263], fl[362])
#         # right_eye_ear = euclidean_dist(fl[145], fl[159]) / euclidean_dist(fl[133], fl[33])
#
#         left_eye_ear = (euclidean_dist(fl[385], fl[380]) + euclidean_dist(fl[387], fl[373])) / (2 * euclidean_dist(fl[362], fl[263]))
#         right_eye_ear = (euclidean_dist(fl[160], fl[144]) + euclidean_dist(fl[158], fl[153])) / (2 * euclidean_dist(fl[33], fl[133]))
#
#         print(left_eye_ear)
#         print(right_eye_ear)
#         print()
#
#         if left_eye_ear < 0.1 and right_eye_ear < 0.1:
#             break
#
# vc.release()
# cv2.destroyAllWindows()
# landmarker.close()


# Example for mediapipe with OpenCV using live stream

import time
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
import math


def euclidean_dist(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)



BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = vision.FaceLandmarker
FaceLandmarkerOptions = vision.FaceLandmarkerOptions
FaceLandmarkerResult = mp.tasks.vision.FaceLandmarkerResult
VisionRunningMode = vision.RunningMode


def process_result(face_landmarker_result: FaceLandmarkerResult, image: mp.Image, timestamp_ms: int):
    if len(face_landmarker_result.face_landmarks) != 0:
        fl = face_landmarker_result.face_landmarks[0]

        left_eye_ear = (euclidean_dist(fl[385], fl[380]) + euclidean_dist(fl[387], fl[373])) / (2 * euclidean_dist(fl[362], fl[263]))
        right_eye_ear = (euclidean_dist(fl[160], fl[144]) + euclidean_dist(fl[158], fl[153])) / (2 * euclidean_dist(fl[33], fl[133]))

        print(left_eye_ear)
        print(right_eye_ear)
        print("This is example.py!")
        print()

        if left_eye_ear < 0.1 and right_eye_ear < 0.1:
            exit(0)


vc = cv2.VideoCapture(0)

model_path = "resources/face_landmarker.task"

options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path, delegate=None),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=process_result
)

landmarker = FaceLandmarker.create_from_options(options)
start_time = time.time()
cv2.namedWindow("preview")

while True:
    success, frame = vc.read()

    if not success:
        break

    cv2.imshow("preview", frame)
    key = cv2.waitKey(20)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    frame_timestamp_ms = int((time.time() - start_time) * 1000)

    landmarker.detect_async(mp_image, frame_timestamp_ms)

vc.release()
cv2.destroyAllWindows()
landmarker.close()