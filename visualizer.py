import pygame
import math
from pginput import InputBox, DataManager

# constant based on lidar resolution
LIDAR_RESOLUTION = 360
# Constant screen width
SCREEN_WIDTH = 800
# Selected positions in a frame (result of the Sklearn SelectKBest function)
DECISIVE_FRAME_POSITIONS = [24, 29, 31, 35, 38, 39, 40, 41, 42, 43, 44, 45, 47, 50, 54, 55, 57, 302,
                            304, 312, 314, 315, 316, 318, 319, 321, 324, 326, 328, 330]


def run(highlight_frames = True):
    data_manager = DataManager('./data/run2/out.txt', 'data/run2/_out.txt', False)
    pygame.init()
    clock = pygame.time.Clock()
    # Set up the drawing window
    screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_WIDTH])
    # Set up the font
    font = pygame.font.Font(None, 32)
    # FONT = pygame.font.Font(None, 32)

    input_box1 = InputBox(350, 650, 140, 32, font)
    input_box2 = InputBox(350, 700, 140, 32, font)
    input_boxes = [input_box1, input_box2]
    input_box1.add_observer(data_manager)

    running = True
    paused = False
    inspect_mode = True
    distances = []

    while data_manager.has_next():
        if inspect_mode:
            paused = True
        # Did the user click the window close button?
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                    # print('PAUSE STATUS: {}'.format(paused))
                elif event.key == pygame.K_i:
                    """
                    Press 'i' keyboard will turn on inspection mode,
                    which run frame by frame
                    """
                    inspect_mode = not inspect_mode
                    # print('INSPECT MODE: {}'.format(inspect_mode))
                elif event.key == pygame.K_q:
                    running = False
            elif event.type == pygame.QUIT:
                # Press 'X' button on window will close the program
                running = False

            # handle input box event
            for box in input_boxes:
                box.handle_event(event)

        if not running:
            break
        if data_manager.read_pos < data_manager.pointer:
            distances = data_manager.dataframe
        if len(distances) == LIDAR_RESOLUTION + 1:  # One more column, the last column contain TURN value
            # Fill the background with white
            screen.fill((250, 250, 250))

            for x in range(LIDAR_RESOLUTION):
                # depend on the average distance, divide distance with a constant for better view
                # provide zoom in/out effect
                a = float(distances[x]) / 3.5

                if x in DECISIVE_FRAME_POSITIONS and highlight_frames:
                    # draw line to the point
                    pygame.draw.line(screen, (255, 0, 255), (SCREEN_WIDTH / 2, SCREEN_WIDTH / 2),
                                     (math.cos(x / 180 * math.pi) * a + SCREEN_WIDTH / 2,
                                      math.sin(x / 180 * math.pi) * a + SCREEN_WIDTH / 2), 2)

                    # Draw the important point with RED color
                    pygame.draw.circle(screen, (255, 0, 0),
                                       (math.cos(x / 180 * math.pi) * a + SCREEN_WIDTH / 2,
                                        math.sin(x / 180 * math.pi) * a + SCREEN_WIDTH / 2),
                                       3)
                else:
                    # Draw the ordinary point with BLACK color
                    pygame.draw.circle(screen, (0, 0, 0),
                                       (math.cos(x / 180 * math.pi) * a + SCREEN_WIDTH / 2,
                                        math.sin(x / 180 * math.pi) * a + SCREEN_WIDTH / 2),
                                       2)

                # Draw the opposite (augmented value)
                # pygame.draw.circle(screen, (255, 100, 100),
                #                    (math.cos(x / 180 * math.pi) * a + SCREEN_WIDTH / 2,
                #                     -math.sin(x / 180 * math.pi) * a + SCREEN_WIDTH / 2),
                #                    2)

            # draw input boxes on screen
            if not input_box1.active:
                input_box1.set_text(distances[360])
            for box in input_boxes:
                box.update()
            for box in input_boxes:
                box.draw(screen)

            # Render the text
            text = font.render("line: {}, turn: {:.2f}".format(
                data_manager.read_pos, float(distances[360])), True, (0, 255, 255))
            # Blit the text to the screen
            screen.blit(text, (350, 600))

            # draw the car
            pygame.draw.circle(screen, (252, 132, 3), (SCREEN_WIDTH / 2, SCREEN_WIDTH / 2), 12)
            pygame.draw.line(screen, (0, 0, 255), (SCREEN_WIDTH / 2, SCREEN_WIDTH / 2),
                             (SCREEN_WIDTH / 2 + 40, SCREEN_WIDTH / 2), 3)
            # Use convention: Full LEFT/RIGHT TURN = 45 degree (Pi/4)
            x = math.cos(float(distances[360]) * math.pi / 4) * 40
            y = math.sin(float(distances[360]) * math.pi / 4) * 40
            pygame.draw.line(screen, (0, 255, 0), (SCREEN_WIDTH / 2, SCREEN_WIDTH / 2),
                             (SCREEN_WIDTH / 2 + x, SCREEN_WIDTH / 2 + y), 3)
            # Flip the display
            pygame.display.flip()
            clock.tick(10)

            if not paused:  # Moving to the next lidar scan cycle
                print('Not Paused')
                # write current line to file
                data_manager.write_line()
                # move to the next lidar data frame
                data_manager.next()
                # reset input value
                input_box1.value = ''

    pygame.quit()


if __name__ == '__main__':
    run(True)
