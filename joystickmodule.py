import pygame
from time import sleep

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"  # fool the system to think it has a video

pygame.init()
controller = pygame.joystick.Joystick(0)
controller.init()
buttons = {'y': 0, 'b': 0, 'a': 0, 'x': 0,
           'L1': 0, 'R1': 0, 'L2': 0, 'R2': 0,
           'select': 0, 'start': 0, 'j1': 0, 'j2': 0, 'home': 0,
           'axis0': 0., 'axis1': 0., 'axis2': 0., 'axis3': 0.,
           'hat0': 0., 'hat1': 0.}
axes = [0., 0., 0., 0.]


def get_joystick(name=''):
    global buttons
    # retrieve any events ...
    for event in pygame.event.get():  # Analog Sticks
        if event.type == pygame.JOYHATMOTION:
            buttons['hat0'], buttons['hat1'] = event.value
            # print('hat0: {}, hat1: {}'.format(hat0, hat1))
        if event.type == pygame.JOYAXISMOTION:
            axes[event.axis] = round(event.value, 2)
        elif event.type == pygame.JOYBUTTONDOWN:  # When button pressed
            # print(event.dict, event.joy, event.button, 'PRESSED')
            for x, (key, val) in enumerate(buttons.items()):
                if x < 13:
                    if controller.get_button(x):
                        buttons[key] = 1
        elif event.type == pygame.JOYBUTTONUP:  # When button released
            # print(event.dict, event.joy, event.button, 'released')
            for x, (key, val) in enumerate(buttons.items()):
                if x < 13:
                    if event.button == x:
                        buttons[key] = 0

    # to remove element 2 since axis numbers are 0 1 3 4
    buttons['axis0'], buttons['axis1'], buttons['axis2'], buttons['axis3'] = \
        [axes[0], axes[1], axes[2], axes[3]]
    if name == '':
        return buttons
    else:
        return buttons[name]


def main():
    while True:
        joystick = get_joystick() # To get all values
        for k,v in joystick.items():
            if v != 0:
                print('k {}, v {}'.format(k,v))
        sleep(0.1)
        # print(get_joystick('start'))  # To get a single value
        sleep(0.1)


if __name__ == '__main__':
    main()
