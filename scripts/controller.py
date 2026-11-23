import os
from pathlib import Path
import gtts
import playsound3
import cv2
import mediapipe as mp
from PIL import ImageTk, Image
from model import Model
from view import View

# Controller class connecting the other two classes together
class Controller:
    def __init__(self, left_eye, right_eye):
        self.languages = {}
        self.language_letter_count_dict = {}
        self.languages_names = {}

        languages_directory = Path("../resources/languages")

        for file_path in languages_directory.iterdir():
            if file_path.is_file():
                content = file_path.read_text(encoding="utf-8")
                current_language = eval(content)
                self.languages[current_language["name"]] = current_language["language"]
                self.language_letter_count_dict[current_language["name"]] = current_language["letter_count"]
                self.languages_names[current_language["name"]] = current_language["abbreviation"]

        if not list(self.languages_names.keys()):
            exit(0)

        default_language = list(self.languages_names.keys())[0]

        if list(self.languages_names.keys()).count("English"):
            default_language = "English"

        self.left_eye = left_eye
        self.right_eye = right_eye
        self.view = View(self.languages[default_language], list(self.languages_names.keys()), default_language, self.language_letter_count_dict[default_language], self.reset, self.change_language)
        self.model = Model(self.languages[default_language], self.process_signal)
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
        print(1)
        self.model.language = language
        self.view.change_language(self.languages[self.model.language], self.language_letter_count_dict[self.model.language])
        self.view.fill_morse_code_tables()
        self.model.change_language(self.languages[self.model.language])
        self.reset()

    def change_fps(self, *args):
        self.view.change_fps()

    def replace_text(self, letter):
        self.view.replace_text(letter)
        self.model.replace_text(letter)

    def add_text(self, letter, separator):
        self.view.add_text(letter)

        if separator == " " and self.view.audio.get():
            self.say_word(self.model.word)

        self.model.add_text(letter, separator)

    def say_word(self, word):
        word = word.lower()
        audio_obj = gtts.gTTS(text=word, lang=self.languages_names[self.model.language])
        audio_obj.save("../audio/audio.mp3")
        playsound3.playsound(os.path.abspath("../audio/audio.mp3"), block=False)