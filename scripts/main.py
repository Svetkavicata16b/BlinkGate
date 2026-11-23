import consts
from controller import Controller


if __name__ == "__main__":
    controller = Controller(consts.LEFT_EYE, consts.RIGHT_EYE)
    controller.main()
    controller.view.screen.mainloop()