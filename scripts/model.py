import time
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
import math


# Model class controlling the morse code logic
class Model:
    def __init__(self, morse_code_language_dict, callback):
        self.morse_code_language_dict = morse_code_language_dict
        self.letter = ""
        self.word = ""
        self.prev_eyes = [False, False]
        self.is_eyes_clear = False
        self.prev_time = 0
        self.language = "English"

        self.vc = cv2.VideoCapture(0)
        self.model_path = "../resources/face_landmarker.task"

        self.BaseOptions = mp.tasks.BaseOptions
        self.FaceLandmarker = vision.FaceLandmarker
        self.FaceLandmarkerOptions = vision.FaceLandmarkerOptions
        self.FaceLandmarkerResult = mp.tasks.vision.FaceLandmarkerResult
        self.VisionRunningMode = vision.RunningMode

        self.options = self.FaceLandmarkerOptions(
            base_options=self.BaseOptions(model_asset_path=self.model_path, delegate=None),
            running_mode=self.VisionRunningMode.LIVE_STREAM,
            result_callback=callback
        )

        self.landmarker = self.FaceLandmarker.create_from_options(self.options)
        self.start_time = time.time()
        self.current_separator = 0

    def euclidean_dist(self, a, b):
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

    def get_camera_frame(self):
        success, frame = self.vc.read()

        if not success:
            print("Failed to read frame. There is problem with video input.")

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        return frame, rgb_frame

    def to_signal(self, rgb_frame):
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        frame_timestamp_ms = int((time.time() - self.start_time) * 1000)
        self.landmarker.detect_async(mp_image, frame_timestamp_ms)

    def to_eyes(self, face_landmarker_result):
        if len(face_landmarker_result.face_landmarks) != 0:
            fl = face_landmarker_result.face_landmarks[0]

            left_eye_ear = (self.euclidean_dist(fl[385], fl[380]) + self.euclidean_dist(fl[387], fl[373])) / (2 * self.euclidean_dist(fl[362], fl[263]))
            right_eye_ear = (self.euclidean_dist(fl[160], fl[144]) + self.euclidean_dist(fl[158], fl[153])) / (2 * self.euclidean_dist(fl[33], fl[133]))

            return [left_eye_ear < 0.18, right_eye_ear < 0.18]

        return [False, False]

    def to_morse_code(self, eyes: list[bool]):
        separator = ""
        morse_symbol = ""
        current_time = time.time()

        if self.prev_time:
            if current_time - self.prev_time > 3 and self.current_separator < 2:
                separator = "/ "
                self.current_separator = 2
            elif current_time - self.prev_time > 1 and self.current_separator < 1:
                separator = " "
                self.current_separator = 1


        if eyes == [False, False] and self.prev_eyes[0] != self.prev_eyes[1] and self.is_eyes_clear:
            if current_time - self.prev_time > 0.2:
                if self.prev_eyes[0]:
                    morse_symbol = "."
                else:
                    morse_symbol = "-"

                self.current_separator = 0

                self.prev_time = current_time

        elif eyes != [False, False] and (self.prev_eyes != eyes and self.prev_eyes != [False, False]):
            self.is_eyes_clear = False

        if eyes == [False, False]:
            self.is_eyes_clear = True

        self.prev_eyes = eyes

        return morse_symbol, separator

    def morse_connector(self, morse_symbol, separator):
        if separator == "":
            self.letter += morse_symbol
        else:
            self.letter = morse_symbol

        return self.letter, {"/ ": " ", " ": "", "": None}[separator]

    def to_text(self, morse_letter, separator):
        try:
            return self.morse_code_language_dict[morse_letter], separator
        except KeyError:
            return "#", separator

    def reset(self):
        self.letter = ""
        self.word = ""
        self.prev_eyes = [False, False]
        self.is_eyes_clear = False
        self.prev_time = 0

    def change_language(self, new_morse_code_language_dict):
        self.morse_code_language_dict = new_morse_code_language_dict

    def replace_text(self, letter):
        self.word = self.word[:-1] + letter

    def add_text(self, letter, separator):
        if separator == "":
            self.word += letter
        else:
            self.word = letter