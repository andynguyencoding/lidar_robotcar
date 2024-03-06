import numpy as np
import pygame as pg
import csv

COLOR_INACTIVE = pg.Color('red')
COLOR_ACTIVE = pg.Color('green')


class Observable:
    def __init__(self):
        self.observers = []

    def add_observer(self, observer):
        self.observers.append(observer)

    def remove_observer(self, observer):
        self.observers.remove(observer)

    def notify_observers(self):
        for observer in self.observers:
            observer.update(self)


class Observer:
    def update(self, observable):
        pass


class InputBox(Observable):

    def __init__(self, x, y, w, h, font, text=''):
        super().__init__()
        self.rect = pg.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text = text
        self.font = font
        self.txt_surface = self.font.render(text, True, self.color)
        self.active = False
        self._value = ''

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
        if event.type == pg.KEYDOWN:
            if self.active:
                if event.key == pg.K_RETURN:
                    self._value = self.text
                    self.notify_observers()
                    self.text = ''
                elif event.key == pg.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = self.font.render(self.text, True, self.color)

    def set_text(self, text):
        self.text = text
        self.txt_surface = self.font.render(self.text, True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width() + 10)
        self.rect.w = width

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        # Blit the rect.
        pg.draw.rect(screen, self.color, self.rect, 2)


class DataManager(Observer):
    def __init__(self, in_file, out_file, w_mode=True):
        super().__init__()
        self.infile = open(in_file, 'r')
        self.lines = self.infile.readlines()
        self._pointer = 0
        self._read_pos = -1
        self.outfile = open(out_file, 'w', newline='')
        self.writer = csv.writer(self.outfile)
        self.w_mode = w_mode
        # current line
        self._line = ''
        # current dataframe
        self._lidar_dataframe = []

    @property
    def dataframe(self):
        if self._read_pos < self._pointer:
            self._line = self.lines[self._pointer].rstrip()
            self._lidar_dataframe = self._line.split(',')
            self._read_pos = self._pointer
        return self._lidar_dataframe

    @property
    def pointer(self):
        return self._pointer

    @property
    def read_pos(self):
        return self._read_pos

    def has_next(self):
        return self._pointer < len(self.lines)

    def next(self):
        self._pointer += 1
        return self._lidar_dataframe

    def write_line(self):
        if self.w_mode:
            self.writer.writerow(self._lidar_dataframe)

    def update(self, observable):
        if isinstance(observable, InputBox):
            self._lidar_dataframe[360] = observable.value


def main():
    font = pg.font.Font(None, 32)
    screen = pg.display.set_mode((640, 480))
    clock = pg.time.Clock()
    input_box1 = InputBox(100, 100, 140, 32, font)
    input_box2 = InputBox(100, 300, 140, 32, font)
    input_boxes = [input_box1, input_box2]
    done = False

    while not done:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                done = True
            for box in input_boxes:
                box.handle_event(event)

        for box in input_boxes:
            box.update()

        screen.fill((30, 30, 30))
        for box in input_boxes:
            box.draw(screen)

        pg.display.flip()
        clock.tick(30)


def get_augmented_data():
    data_manager = DataManager('./data/run2/out.txt', './data/run2/augmented_out.txt')
    augmented_data = []
    while data_manager.has_next():
        data = data_manager.dataframe
        augmented_data = np.zeros_like(data)
        for i in range(360):
            augmented_data[359 - i] = data[i]
        augmented_data[360] = 0 - float(data[360])

        data_manager.writer.writerow(augmented_data)

        data_manager.next()
    return augmented_data


if __name__ == '__main__':
    # pg.init()
    # main()
    # pg.quit()
    get_augmented_data()
