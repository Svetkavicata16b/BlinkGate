import tkinter as tk
import time
from consts import morse_code_english_dict
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
import math


class Model:
    def __init__(self, morse_code_language_dict, callback):
        self.morse_code_language_dict = morse_code_language_dict
        self.letter = ""
        self.prev_eyes = [False, False]
        self.is_eyes_clear = False
        self.prev_time = 0

        self.vc = cv2.VideoCapture(0)
        self.model_path = "resources/face_landmarker.task"

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

    def euclidean_dist(self, a, b):
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

    def to_signal(self):
        success, frame = self.vc.read()

        if not success:
            print("Failed to read frame. There is problem with video input.")

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        frame_timestamp_ms = int((time.time() - self.start_time) * 1000)

        self.landmarker.detect_async(mp_image, frame_timestamp_ms)

    def to_eyes(self, face_landmarker_result):
        if len(face_landmarker_result.face_landmarks) != 0:
            fl = face_landmarker_result.face_landmarks[0]

            left_eye_ear = (self.euclidean_dist(fl[385], fl[380]) + self.euclidean_dist(fl[387], fl[373])) / (2 * self.euclidean_dist(fl[362], fl[263]))
            right_eye_ear = (self.euclidean_dist(fl[160], fl[144]) + self.euclidean_dist(fl[158], fl[153])) / (2 * self.euclidean_dist(fl[33], fl[133]))

            # print(left_eye_ear)
            # print(right_eye_ear)
            # print()

            return [left_eye_ear < 0.15, right_eye_ear < 0.15]

        return [False, False]

    def to_morse_code(self, eyes: list[bool]):
        separator = ""
        morse_symbol = ""

        # print([eyes, self.prev_eyes, self.is_eyes_clear])

        if eyes == [False, False] and self.prev_eyes[0] != self.prev_eyes[1] and self.is_eyes_clear:
            current_time = time.time()

            if self.prev_time != 0:
                if current_time - self.prev_time > 3:
                    separator = " / "
                elif current_time - self.prev_time > 1:
                    separator = " "

            if self.prev_eyes[0]:
                morse_symbol = "."
            else:
                morse_symbol = "-"

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

        return self.letter, {" / ": " ", " ": "", "": None}[separator]

    def to_text(self, morse_letter, separator):
        try:
            return self.morse_code_language_dict[morse_letter], separator
        except KeyError:
            return "#", separator


class View:
    def __init__(self):
        self.screen = tk.Tk()
        self.screen.state("zoomed")
        self.screen.title("BlinkGate")
        self.screen.iconphoto(False, tk.PhotoImage(file="images/visible.png"))

        self.morse_code = tk.Text(self.screen, height=1, width=1, state="disabled", font=("Arial", 20))
        self.text = tk.Text(self.screen, height=1, width=1, state="disabled", font=("Arial", 20))
        self.morse_code.pack(fill="both", side="left", expand=True)
        self.text.pack(fill="both", side="right", expand=True)

    def add_morse_code(self, morse_code, separator):
        self.morse_code.configure(state="normal")
        self.morse_code.insert("insert", separator + morse_code)
        self.morse_code.see("end")
        self.morse_code.configure(state="disabled")

    def add_text(self, letter, separator):
        self.text.configure(state="normal")
        self.text.insert("insert", separator + letter)
        self.text.see("end")
        self.text.configure(state="disabled")

    def replace_text(self, letter):
        self.text.configure(state="normal")
        self.text.delete("end-2c")
        self.text.insert("insert", letter)
        self.text.see("end")
        self.text.configure(state="disabled")


class Controller:
    def __init__(self):
        self.model = Model(morse_code_english_dict, self.process_signal)
        self.view = View()

    def main(self):
        self.model.to_signal()
        self.view.screen.after(10, self.main)

    def process_signal(self, face_landmarker_result, image, timestamp_ms):
        eyes = self.model.to_eyes(face_landmarker_result)
        morse_symbol, separator = self.model.to_morse_code(eyes)

        self.view.add_morse_code(morse_symbol, separator)

        morse_letter, separator = self.model.morse_connector(morse_symbol, separator)
        letter, separator = self.model.to_text(morse_letter, separator)

        if separator is None:
            self.view.replace_text(letter)
        else:
            self.view.add_text(letter, separator)

if __name__ == "__main__":
    controller = Controller()
    controller.main()
    controller.view.screen.mainloop()