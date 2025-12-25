import tkinter as tk
import time
from consts import morse_code_english_dict


class Model:
    def __init__(self, morse_code_language_dict):
        self.morse_code_language_dict = morse_code_language_dict
        self.last_letter = ""
        self.prev_eyes = [False, False]
        self.prev_prev_eyes = [False, False]
        self.prev_time = time.time()

    def to_morse_code(self, eyes):
        separator = ""
        morse_symbol = ""
        if self.prev_prev_eyes == eyes == [False, False] and self.prev_eyes[0] != self.prev_eyes[1]:
            current_time = time.time()

            if current_time - self.prev_time > 3:
                separator = " / "
            elif current_time - self.prev_time > 1:
                separator = " "

            if self.prev_eyes[0]:
                morse_symbol = "."
            else:
                morse_symbol = "-"

            self.prev_time = current_time

        self.prev_prev_eyes = self.prev_eyes
        self.prev_eyes = eyes

        return morse_symbol, separator

    def morse_connector(self, morse_symbol, separator):
        if separator == "":
            self.last_letter += morse_symbol

            return "", ""
        else:
            return_letter = self.last_letter
            self.last_letter = morse_symbol

            return return_letter, {" / ": " ", " ": ""}[separator]

    def to_text(self, morse_letter, separator):
        return self.morse_code_language_dict[morse_letter], separator


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
        self.morse_code.configure(state="disabled")

    def add_text(self, letter, separator):
        self.text.configure(state="normal")
        self.text.insert("insert", letter + separator)
        self.text.configure(state="disabled")


class Controller:
    def __init__(self):
        self.model = Model(morse_code_english_dict)
        self.view = View()

    def main(self):
        self.view.screen.bind_all("<Left>", self.on_key_press)
        self.view.screen.bind_all("<Right>", self.on_key_press)

        self.view.screen.mainloop()

    def on_key_press(self, event):
        if event.keysym == "Left":
            self.model.to_morse_code([True, False])
        if event.keysym == "Right":
            self.model.to_morse_code([False, True])

        morse_symbol, separator = self.model.to_morse_code([False, False])

        self.view.add_morse_code(morse_symbol, separator)

        morse_letter, separator = self.model.morse_connector(morse_symbol, separator)
        letter, separator = self.model.to_text(morse_letter, separator)

        self.view.add_text(letter, separator)


if __name__ == "__main__":
    controller = Controller()
    controller.main()