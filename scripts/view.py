import customtkinter as tk
import cv2
from PIL import ImageTk, Image


# View class controlling the GUI
class View:
    def __init__(self, morse_code_language_dict, clearing_callback_function, language_callback):
        self.morse_code_language_dict = morse_code_language_dict
        self.language_letters_count = 26
        self.main_color = "#1F883D" # "#16a34a"
        self.hover_color = "#1F793A"
        self.main_bg_color = "#F3F4F6"
        self.main_fg_color = "#F9FAFB"
        self.border_color = "#E5E7EB"
        self.main_font = ("Courier New", 20, "bold")
        self.morse_font = ("Courier New", 20, "bold")
        self.big_font = ("Courier New", 54, "bold")
        self.screen = tk.CTk(fg_color=self.main_bg_color)
        self.open_eye_image = ImageTk.PhotoImage(Image.open("../images/visible.png").resize((100, 100)))
        self.closed_eye_image = ImageTk.PhotoImage(Image.open("../images/hidden.png").resize((100, 100)))
        self.screen.iconbitmap("../images/icon.ico")
        self.screen.after(0, lambda: self.screen.state('zoomed'))
        self.screen.title("BlinkGate")
        self.change_camera_frame_image = None
        self.fps = tk.IntVar(self.screen, value=10)
        self.audio = tk.BooleanVar(self.screen, value=False)

        self.morse_code_table_frame = tk.CTkFrame(self.screen, fg_color="transparent")
        self.inside_morse_code_table_frame = tk.CTkFrame(self.morse_code_table_frame, fg_color="transparent")
        self.camera_frame = tk.CTkFrame(self.screen, fg_color="transparent")
        self.camera_image_frame = tk.CTkFrame(self.camera_frame, fg_color="transparent")
        self.fps_frame = tk.CTkFrame(self.camera_frame, fg_color="transparent")
        self.left_eye_frame = tk.CTkFrame(self.camera_frame, fg_color="transparent")
        self.right_eye_frame = tk.CTkFrame(self.camera_frame, fg_color="transparent")
        self.translation_frame = tk.CTkFrame(self.screen, fg_color="transparent")
        self.morse_code_frame = tk.CTkFrame(self.translation_frame, fg_color=self.main_fg_color, border_color=self.border_color, border_width=2, corner_radius=10)
        self.text_frame = tk.CTkFrame(self.translation_frame, fg_color=self.main_fg_color, border_color=self.border_color, border_width=2, corner_radius=10)
        self.audio_frame = tk.CTkFrame(self.translation_frame, fg_color="transparent")

        self.languages = tk.CTkOptionMenu(self.morse_code_table_frame, values=["English", "Bulgarian"], command=language_callback, font=self.main_font, dropdown_font=self.main_font, fg_color=self.main_color, button_color=self.main_color, button_hover_color=self.hover_color, text_color=self.main_fg_color)
        self.morse_code_letters_table = tk.CTkTextbox(self.inside_morse_code_table_frame, width=160, state="disabled", font=self.morse_font, fg_color=self.main_fg_color, border_color=self.border_color, border_width=2)
        self.morse_code_numbers_and_symbols_table = tk.CTkTextbox(self.inside_morse_code_table_frame, width=160, state="disabled", font=self.morse_font, fg_color=self.main_fg_color, border_color=self.border_color, border_width=2)
        self.fps_label = tk.CTkLabel(self.fps_frame, text=f"FPS: {self.fps.get()}", font=self.main_font)
        self.fps_slider = tk.CTkSlider(self.fps_frame, from_=10, to=100, variable=self.fps, width=200, button_color=self.main_color, button_hover_color=self.hover_color)
        self.camera_image = tk.CTkLabel(self.camera_image_frame, text="")
        self.left_eye_image = tk.CTkLabel(self.left_eye_frame, image=self.open_eye_image, text="")
        self.dot = tk.CTkLabel(self.left_eye_frame, text=".", font=self.big_font)
        self.right_eye_image = tk.CTkLabel(self.right_eye_frame, image=self.open_eye_image, text="")
        self.dash = tk.CTkLabel(self.right_eye_frame, text="-", font=self.big_font)
        self.clear_btn = tk.CTkButton(self.translation_frame, width=320, text="Clear Text", font=self.main_font, fg_color=self.main_color, hover_color=self.hover_color, corner_radius=5, command=clearing_callback_function, text_color=self.main_fg_color)
        self.morse_code_label = tk.CTkLabel(self.morse_code_frame, text="Morse Input", font=self.main_font)
        self.morse_code_separator = tk.CTkFrame(self.morse_code_frame, width=320, height=2, border_color=self.border_color, border_width=2)
        self.morse_code = tk.CTkTextbox(self.morse_code_frame, state="disabled", font=self.main_font, fg_color=self.main_fg_color)
        self.text_label = tk.CTkLabel(self.text_frame, text="Decoded Text", font=self.main_font)
        self.text_separator = tk.CTkFrame(self.text_frame, width=320, height=2, border_color=self.border_color, border_width=2)
        self.text = tk.CTkTextbox(self.text_frame, state="disabled", font=self.main_font, fg_color=self.main_fg_color)
        self.audio_checkbox = tk.CTkCheckBox(self.audio_frame, variable=self.audio, onvalue=True, offvalue=False, text="Audio", font=self.main_font, fg_color=self.main_color, hover_color=self.hover_color)

        self.languages.pack(side="top", fill="x", pady=(0, 9))
        self.morse_code_letters_table.pack(side="left", fill="y", padx=(0, 5))
        self.morse_code_numbers_and_symbols_table.pack(side="right", fill="y", padx=(5, 0))
        self.fps_label.pack(side="left", padx=(0, 50))
        self.fps_slider.pack(side="left", pady=20)
        self.camera_image.pack()
        self.left_eye_image.pack(side="bottom", padx=80, pady=30)
        self.dot.pack(side="top")
        self.right_eye_image.pack(side="bottom", padx=80, pady=30)
        self.dash.pack(side="top")
        self.clear_btn.pack(side="top", fill="x", pady=(0, 5))
        self.morse_code_label.pack(padx=2, pady=2)
        self.morse_code_separator.pack()
        self.morse_code.pack(fill="both", expand=True, padx=5, pady=5)
        self.text_label.pack(padx=2, pady=2)
        self.text_separator.pack()
        self.text.pack(fill="both", expand=True, padx=5, pady=5)
        self.audio_checkbox.pack(pady=10)

        self.inside_morse_code_table_frame.pack(fill="both", expand=True)
        self.morse_code_table_frame.pack(side="left", fill="y", expand=True, padx=(10, 5), pady=10)
        self.fps_frame.pack(side="bottom", pady=20)
        self.camera_image_frame.pack(side="bottom")
        self.left_eye_frame.pack(side="left")
        self.right_eye_frame.pack(side="right")
        self.camera_frame.pack(side="left", expand=True, padx=(5, 5), pady=10)
        self.morse_code_frame.pack_propagate(False)
        self.text_frame.pack_propagate(False)
        self.morse_code_frame.pack(side="top", fill="both", expand=True, pady=(5, 5))
        self.text_frame.pack(side="top", fill="both", expand=True, pady=(5, 0))
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

    def add_text(self, letter):
        self.text.configure(state="normal")
        self.text.insert("end", letter)
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