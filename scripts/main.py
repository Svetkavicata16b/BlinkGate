import os
import sys
import threading
# import tkinter as tk
import time
import subprocess

import PIL
import customtkinter as tk

import gtts
import playsound3
from PIL.ImageOps import expand

import consts
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
import math
from PIL import ImageTk, Image


class Model:
    def __init__(self, morse_code_language_dict, callback):
        self.morse_code_language_dict = morse_code_language_dict
        self.letter = ""
        self.word = ""
        self.prev_eyes = [False, False]
        self.is_eyes_clear = False
        self.prev_time = 0
        self.language = "english"

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

            if current_time > self.prev_time:
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


class View:
    def __init__(self, morse_code_language_dict, clearing_callback_function, language_callback):
        self.morse_code_language_dict = morse_code_language_dict
        self.language_letters_count = 26
        self.screen = tk.CTk(fg_color="white")
        self.screen.after(0, lambda: self.screen.state('zoomed'))
        self.screen.title("BlinkGate")
        self.open_eye_image = ImageTk.PhotoImage(Image.open("../images/visible.png").resize((100, 100)))
        self.closed_eye_image = ImageTk.PhotoImage(Image.open("../images/hidden.png").resize((100, 100)))
        self.screen.iconphoto(False, self.open_eye_image)
        self.change_camera_frame_image = None
        self.fps = tk.IntVar(self.screen, value=10)
        self.audio = tk.BooleanVar(self.screen, value=False)

        self.morse_code_table_frame = tk.CTkFrame(self.screen, fg_color="transparent")
        self.inside_morse_code_table_frame = tk.CTkFrame(self.morse_code_table_frame, fg_color="transparent")
        self.camera_frame = tk.CTkFrame(self.screen, fg_color="transparent")
        self.fps_frame = tk.CTkFrame(self.camera_frame, fg_color="transparent")
        self.left_eye_frame = tk.CTkFrame(self.camera_frame, fg_color="transparent")
        self.right_eye_frame = tk.CTkFrame(self.camera_frame, fg_color="transparent")
        self.translation_frame = tk.CTkFrame(self.screen, fg_color="transparent")
        self.morse_code_frame = tk.CTkFrame(self.translation_frame, fg_color="transparent")
        self.text_frame = tk.CTkFrame(self.translation_frame, fg_color="transparent")
        self.audio_frame = tk.CTkFrame(self.translation_frame, fg_color="transparent")

        self.languages = tk.CTkOptionMenu(self.morse_code_table_frame, values=["english", "bulgarian"], command=language_callback, font=("Courier New", 20, "bold"), dropdown_font=("Courier New", 20, "bold"))
        self.morse_code_letters_table = tk.CTkTextbox(self.inside_morse_code_table_frame, width=160, state="disabled", font=("Courier New", 20, "bold"))
        self.morse_code_numbers_and_symbols_table = tk.CTkTextbox(self.inside_morse_code_table_frame, width=160, state="disabled", font=("Courier New", 20, "bold"))
        self.fps_label = tk.CTkLabel(self.fps_frame, text=f"FPS: {self.fps.get()}", font=("Courier New", 20, "bold"))
        self.fps_slider = tk.CTkSlider(self.fps_frame, from_=10, to=100, variable=self.fps, width=200)
        self.camera_image = tk.CTkLabel(self.camera_frame, text="")
        self.left_eye_image = tk.CTkLabel(self.left_eye_frame, image=self.open_eye_image, text="")
        self.dot = tk.CTkLabel(self.left_eye_frame, text=".", font=("Courier New", 20))
        self.right_eye_image = tk.CTkLabel(self.right_eye_frame, image=self.open_eye_image, text="")
        self.dash = tk.CTkLabel(self.right_eye_frame, text="-", font=("Courier New", 20))
        self.clear_btn = tk.CTkButton(self.translation_frame, width=320, text="Clear Text", font=("Courier New", 20, "bold"), corner_radius=5, command=clearing_callback_function)
        self.morse_code = tk.CTkTextbox(self.morse_code_frame, state="disabled", font=("Courier New", 20, "bold"))
        self.text = tk.CTkTextbox(self.text_frame, state="disabled", font=("Courier New", 20, "bold"))
        self.audio_checkbox = tk.CTkCheckBox(self.audio_frame, variable=self.audio, onvalue=True, offvalue=False, text="Audio", font=("Courier New", 20, "bold"))

        self.languages.pack(side="top", fill="x")
        self.morse_code_letters_table.pack(side="left", fill="y", padx=(0, 5))
        self.morse_code_numbers_and_symbols_table.pack(side="right", fill="y", padx=(5, 0))
        self.fps_label.pack(side="left", padx=(0, 50))
        self.fps_slider.pack(side="left", pady=20)
        self.camera_image.pack(side="bottom")
        self.left_eye_image.pack(side="bottom", padx=80, pady=30)
        self.dot.pack(side="top")
        self.right_eye_image.pack(side="bottom", padx=80, pady=30)
        self.dash.pack(side="top")
        self.clear_btn.pack(side="top", fill="x")
        self.morse_code.pack(fill="both", expand=True, pady=(0, 5))
        self.text.pack(fill="both", expand=True, pady=(5, 0))
        self.audio_checkbox.pack(pady=10)

        self.inside_morse_code_table_frame.pack(fill="both", expand=True)
        self.morse_code_table_frame.pack(side="left", fill="y", expand=True, padx=(10, 5), pady=10)
        self.fps_frame.pack()
        self.left_eye_frame.pack(side="left")
        self.right_eye_frame.pack(side="right")
        self.camera_frame.pack(side="left", expand=True, padx=(5, 5), pady=10)
        self.morse_code_frame.pack_propagate(False)
        self.text_frame.pack_propagate(False)
        self.morse_code_frame.pack(side="top", fill="both", expand=True)
        self.text_frame.pack(side="top", fill="both", expand=True)
        self.audio_frame.pack()
        self.translation_frame.pack(side="left", fill="y", expand=True, padx=(5, 10), pady=10)

    def fill_morse_code_tables(self):

        self.morse_code_letters_table.configure(state="normal")
        self.morse_code_letters_table.delete(1.0, tk.END)

        for i in range(0, self.language_letters_count):
            key = list(self.morse_code_language_dict.keys())[i]
            self.morse_code_letters_table.insert("end", f"  {self.morse_code_language_dict[key]} {key}\n")

        self.morse_code_letters_table.configure(state="disabled")

        self.morse_code_numbers_and_symbols_table.configure(state="normal")
        self.morse_code_numbers_and_symbols_table.delete(1.0, tk.END)

        for i in range(self.language_letters_count, len(self.morse_code_language_dict)):
            key = list(self.morse_code_language_dict.keys())[i]
            self.morse_code_numbers_and_symbols_table.insert("end", f"  {self.morse_code_language_dict[key]}{bool(len(key)) * ' '}{key}\n")

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

    def clear_morse_code_and_text(self):
        self.morse_code.configure(state="normal")
        self.morse_code.delete("1.0", tk.END)
        self.morse_code.configure(state="disabled")
        self.text.configure(state="normal")
        self.text.delete("1.0", tk.END)
        self.text.configure(state="disabled")

    def change_language(self, new_morse_code_language_dict, new_language_letter_count):
        self.morse_code_language_dict = new_morse_code_language_dict
        self.language_letters_count = new_language_letter_count

    def change_fps(self):
        self.fps_label.configure(text=f"FPS: {self.fps.get()}")


class Controller:
    def __init__(self, languages, language_letters_count_dict, languages_names, left_eye, right_eye):
        self.languages = languages
        self.language_letters_count_dict = language_letters_count_dict
        self.languages_names = languages_names
        self.left_eye = left_eye
        self.right_eye = right_eye
        self.view = View(self.languages["english"], self.reset, self.change_language)
        self.model = Model(languages["english"], self.process_signal)
        self.view.fill_morse_code_tables()
        self.frame = None
        self.output_file_path = os.path.abspath("../audio/audio.wav")
        self.view.fps.trace_add("write", self.change_fps)

    def main(self):
        self.frame, rgb_frame = self.model.get_camera_frame()
        self.model.to_signal(rgb_frame)
        self.view.screen.after(1000 // self.view.fps.get(), self.main)

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
            self.replace_text(letter)
        else:
            self.add_text(letter, separator)

    def reset(self):
        self.model.reset()
        self.view.clear_morse_code_and_text()

    def change_language(self, language):
        self.model.language = language
        self.view.change_language(self.languages[self.model.language], self.language_letters_count_dict[self.model.language])
        self.view.fill_morse_code_tables()
        self.model.change_language(self.languages[self.model.language])
        self.reset()

    def change_fps(self, *args):
        self.view.change_fps()

    def replace_text(self, letter):
        self.view.replace_text(letter)
        self.model.replace_text(letter)

    def add_text(self, letter, separator):
        self.view.add_text(letter, separator)

        if separator == " " and self.view.audio.get():
            self.say_word(self.model.word)

        self.model.add_text(letter, separator)

    def say_word(self, word):
        word = word.lower()
        audio_obj = gtts.gTTS(text=word, lang=self.languages_names[self.model.language])
        audio_obj.save("../audio/audio.mp3")
        playsound3.playsound(os.path.abspath("../audio/audio.mp3"), block=False)

    # def say_word(self, word, language):
    #     word = word.lower()
    #     model = os.path.abspath(self.languages_voices[language])
    #
    #     threading.Thread(target=self.play_tts, args=[word, model], daemon=True).start()
    #
    #
    # def play_tts(self, word, model):
    #     cmd = [
    #         "piper.exe",
    #         "--model", model,
    #         "--output_file", self.output_file_path
    #     ]
    #
    #     subprocess.run(
    #         cmd,
    #         input=word.encode("utf-8"),
    #         stdout=subprocess.DEVNULL,
    #         stderr=subprocess.DEVNULL,
    #         creationflags=subprocess.CREATE_NO_WINDOW
    #     )
    #
    #     playsound3.playsound(self.output_file_path, block=False)


if __name__ == "__main__":
    controller = Controller(consts.languages, consts.language_letters_count_dict, consts.languages_names, consts.LEFT_EYE, consts.RIGHT_EYE)
    controller.main()
    controller.view.screen.mainloop()