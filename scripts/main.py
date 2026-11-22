import consts
from controller import Controller


if __name__ == "__main__":
    controller = Controller(consts.languages, consts.language_letters_count_dict, consts.languages_names, consts.LEFT_EYE, consts.RIGHT_EYE)
    controller.main()
    controller.view.screen.mainloop()