import tkinter as tk
import time

import PIL

import consts
from consts import morse_code_english_dict
from consts import language_letters_count_dict
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
import math
from PIL import ImageTk, Image


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

            # print(left_eye_ear)
            # print(right_eye_ear)
            # print()

            return [left_eye_ear < 0.18, right_eye_ear < 0.18]

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
    def __init__(self, morse_code_language_dict, language_letters_count_dict):
        self.morse_code_language_dict = morse_code_language_dict
        self.language_letters_count_dict = language_letters_count_dict
        self.screen = tk.Tk()
        self.screen.state("zoomed")
        self.screen.title("BlinkGate")
        self.screen.iconphoto(False, tk.PhotoImage(file="images/visible.png"))
        self.open_eye_image = ImageTk.PhotoImage(Image.open("images/visible.png").resize((100, 100)))
        self.closed_eye_image = ImageTk.PhotoImage(Image.open("images/hidden.png").resize((100, 100)))
        self.change_camera_frame_image = 0

        self.morse_code_table_frame = tk.Frame(self.screen)
        self.camera_frame = tk.Frame(self.screen)
        self.left_eye_frame = tk.Frame(self.camera_frame)
        self.right_eye_frame = tk.Frame(self.camera_frame)
        self.translation_frame = tk.Frame(self.screen)
        self.morse_code_frame = tk.Frame(self.translation_frame)
        self.text_frame = tk.Frame(self.translation_frame)

        self.morse_code_letters_table = tk.Text(self.morse_code_table_frame, width=12, state="disabled", font=("Courier New", 20))
        self.morse_code_numbers_and_symbols_table = tk.Text(self.morse_code_table_frame, width=12, state="disabled", font=("Courier New", 20))
        self.camera_image = tk.Label(self.camera_frame)
        self.left_eye_image = tk.Label(self.left_eye_frame, image=self.open_eye_image)
        self.dot = tk.Label(self.left_eye_frame, text=".", font=("Courier New", 20))
        self.right_eye_image = tk.Label(self.right_eye_frame, image=self.open_eye_image)
        self.dash = tk.Label(self.right_eye_frame, text="-", font=("Courier New", 20))
        self.morse_code = tk.Text(self.morse_code_frame, state="disabled", font=("Courier New", 20))
        self.text = tk.Text(self.text_frame, state="disabled", font=("Courier New", 20))

        self.morse_code_letters_table.pack(side="left", fill="y")
        self.morse_code_numbers_and_symbols_table.pack(side="right", fill="y")
        self.camera_image.pack(side="bottom")
        self.morse_code.pack(fill="both", expand=True)
        self.left_eye_image.pack(side="bottom", padx=50, pady=50)
        self.dot.pack(side="top")
        self.right_eye_image.pack(side="bottom", padx=50, pady=50)
        self.dash.pack(side="top")
        self.text.pack(fill="both", expand=True)

        self.morse_code_table_frame.pack(side="left", fill="y")
        self.left_eye_frame.pack(side="left")
        self.right_eye_frame.pack(side="right")
        self.camera_frame.pack(side="left")
        self.morse_code_frame.pack_propagate(False)
        self.text_frame.pack_propagate(False)
        self.morse_code_frame.pack(side="top", fill="both", expand=True)
        self.text_frame.pack(side="bottom", fill="both", expand=True)
        self.translation_frame.pack(side="left", fill="both", expand=True)

    def fill_morse_code_tables(self):
        self.morse_code_letters_table.configure(state="normal")

        for i in range(1, self.language_letters_count_dict[self.morse_code_language_dict["language"]] + 1):
            key = list(self.morse_code_language_dict.keys())[i]
            self.morse_code_letters_table.insert("end", f"{self.morse_code_language_dict[key]} -> {key}\n")

        self.morse_code_letters_table.configure(state="disabled")

        self.morse_code_numbers_and_symbols_table.configure(state="normal")

        for i in range(self.language_letters_count_dict[self.morse_code_language_dict["language"]] + 1, len(self.morse_code_language_dict)):
            key = list(self.morse_code_language_dict.keys())[i]
            self.morse_code_numbers_and_symbols_table.insert("end", f"{self.morse_code_language_dict[key]} {bool(len(key)) * '->'} {key}\n")

        self.morse_code_numbers_and_symbols_table.configure(state="disabled")

    def change_camera_frame(self, frame):
        self.camera_image.configure(image=frame)

    def change_eye_ions(self, eyes):
        self.left_eye_image.configure(image={True: self.closed_eye_image, False: self.open_eye_image}[eyes[0]])
        self.right_eye_image.configure(image={True: self.closed_eye_image, False: self.open_eye_image}[eyes[1]])

    def draw_eyes(self, image, face_landmarker_result, left_eye, right_eye, color):
        if len(face_landmarker_result.face_landmarks) != 0:
            fl = face_landmarker_result.face_landmarks[0]
            h, w = image.shape[:2]

            # for i in left_eye + right_eye:
            #     lm = fl[i]
            #     x, y = int(lm.x * w), int(lm.y * h)
            #     cv2.circle(image, (x, y), 2, color, -1)

            for eye in [left_eye, right_eye]:
                for i in range(len(eye)):
                    p1 = fl[eye[i]]
                    p2 = fl[eye[(i + 1) % len(eye)]]

                    x1, y1 = int(p1.x * w), int(p1.y * h)
                    x2, y2 = int(p2.x * w), int(p2.y * h)

                    cv2.line(image, (x1, y1), (x2, y2), color, 1)

        return image

    def add_morse_code(self, morse_code, separator):
        self.morse_code.configure(state="normal")
        self.morse_code.insert("end", separator + morse_code)
        self.morse_code.see("end")
        self.morse_code.configure(state="disabled")

    def add_text(self, letter, separator):
        self.text.configure(state="normal")
        self.text.insert("end", separator + letter)
        self.text.see("end")
        self.text.configure(state="disabled")

    def replace_text(self, letter):
        if letter != self.text.get("end-2c"):
            self.text.configure(state="normal")
            self.text.delete("end-2c")
            self.text.insert("insert", letter)
            self.text.see("end")
            self.text.configure(state="disabled")
            print(self.text.get("end-2c"))


class Controller:
    def __init__(self, morse_code_language_dict, language_letters_count_dict, left_eye, right_eye):
        self.morse_code_language_dict = morse_code_language_dict
        self.language_letters_count_dict = language_letters_count_dict
        self.left_eye = left_eye
        self.right_eye = right_eye
        self.model = Model(morse_code_english_dict, self.process_signal)
        self.view = View(self.morse_code_language_dict, self.language_letters_count_dict)
        self.view.fill_morse_code_tables()
        self.frame = None

    def main(self):
        self.frame, rgb_frame = self.model.get_camera_frame()
        self.model.to_signal(rgb_frame)
        self.view.screen.after(10, self.main)

    def process_signal(self, face_landmarker_result, image, timestamp_ms):
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(self.view.draw_eyes(self.frame, face_landmarker_result, self.left_eye, self.right_eye, (0, 255, 0)), cv2.COLOR_BGR2RGB))
        current_camera_frame = ImageTk.PhotoImage(image=(Image.fromarray(image.numpy_view())).transpose(method=Image.FLIP_LEFT_RIGHT))
        self.view.change_camera_frame(current_camera_frame)
        self.view.change_camera_frame_image = current_camera_frame

        eyes = self.model.to_eyes(face_landmarker_result)

        self.view.change_eye_ions(eyes)

        morse_symbol, separator = self.model.to_morse_code(eyes)

        self.view.add_morse_code(morse_symbol, separator)

        morse_letter, separator = self.model.morse_connector(morse_symbol, separator)
        letter, separator = self.model.to_text(morse_letter, separator)

        if separator is None:
            self.view.replace_text(letter)
        else:
            self.view.add_text(letter, separator)

if __name__ == "__main__":
    controller = Controller(morse_code_english_dict, language_letters_count_dict, consts.LEFT_EYE, consts.RIGHT_EYE)
    controller.main()
    controller.view.screen.mainloop()