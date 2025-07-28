import pygame
import math
from pginput import InputBox, DataManager

# constant based on lidar resolution
LIDAR_RESOLUTION = 360
# Constant screen width
SCREEN_WIDTH = 800
# Scale factor for distance visualization (will be auto-calculated based on data)
SCALE_FACTOR = 0.25  # Default fallback value
# Target visualization radius (pixels from center)
TARGET_RADIUS = 300  # Use ~300 pixels of the 400 pixel radius available
# Selected positions in a frame (result of the Sklearn SelectKBest function)
DECISIVE_FRAME_POSITIONS = [24, 29, 31, 35, 38, 39, 40, 41, 42, 43, 44, 45, 47, 50, 54, 55, 57, 302,
                            304, 312, 314, 315, 316, 318, 319, 321, 324, 326, 328, 330]


def calculate_scale_factor(data_manager, sample_size=10):
    """
    Analyze sample data to determine optimal scale factor
    """
    global SCALE_FACTOR
    
    # Sample the first few frames to understand data range
    valid_distances = []
    sample_count = 0
    original_pointer = data_manager.pointer
    
    print("Analyzing data to determine optimal scale factor...")
    
    while data_manager.has_next() and sample_count < sample_size:
        distances = data_manager.dataframe
        if len(distances) == LIDAR_RESOLUTION + 1:
            for i in range(LIDAR_RESOLUTION):
                try:
                    distance_value = float(distances[i])
                    if not (math.isinf(distance_value) or math.isnan(distance_value)) and distance_value > 0:
                        valid_distances.append(distance_value)
                except (ValueError, TypeError):
                    continue
        data_manager.next()
        sample_count += 1
    
    # Reset data manager to beginning
    data_manager._pointer = 0
    data_manager._read_pos = -1
    
    if valid_distances:
        # Calculate statistics
        min_dist = min(valid_distances)
        max_dist = max(valid_distances)
        avg_dist = sum(valid_distances) / len(valid_distances)
        
        # Use 90th percentile as effective max to ignore outliers
        valid_distances.sort()
        percentile_90 = valid_distances[int(0.9 * len(valid_distances))]
        
        # Calculate scale factor: target radius / effective max distance
        SCALE_FACTOR = TARGET_RADIUS / percentile_90
        
        print(f"Data analysis complete:")
        print(f"  Distance range: {min_dist:.1f} - {max_dist:.1f} mm")
        print(f"  Average distance: {avg_dist:.1f} mm")
        print(f"  90th percentile: {percentile_90:.1f} mm")
        print(f"  Calculated scale factor: {SCALE_FACTOR:.3f}")
    else:
        print("No valid distance data found, using default scale factor")
    
    return SCALE_FACTOR


def run(data_file=None, highlight_frames=True, show_augmented=False):
    # Default to local data file, but allow external file specification
    if data_file is None:
        data_file = 'data/run1/out1.txt'
    
    data_manager = DataManager(data_file, 'data/run2/_out.txt', False)
    
    # Auto-calculate optimal scale factor based on the data
    calculate_scale_factor(data_manager)
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
    inspect_mode = False  # Start with inspect mode off so it's not paused initially
    augmented_mode = show_augmented  # Flag to show augmented (mirrored) data instead of real data
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
                elif event.key == pygame.K_a:
                    """
                    Press 'a' keyboard will toggle augmented data display,
                    which shows mirrored lidar data for data augmentation
                    """
                    augmented_mode = not augmented_mode
                    print(f'AUGMENTED MODE: {augmented_mode}')
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
                # provide zoom in/out effect using scale_factor
                try:
                    distance_value = float(distances[x])
                    # Skip invalid data points (inf, nan)
                    if math.isinf(distance_value) or math.isnan(distance_value):
                        continue  # Skip this data point and move to the next one
                except (ValueError, TypeError):
                    # Skip non-numeric values (like 'lidar_0', headers, etc.)
                    continue
                a = distance_value * SCALE_FACTOR

                # Choose coordinates based on augmented mode
                if augmented_mode:
                    # Augmented data: mirror horizontally (flip Y coordinate)
                    x_coord = math.cos(x / 180 * math.pi) * a + SCREEN_WIDTH / 2
                    y_coord = -math.sin(x / 180 * math.pi) * a + SCREEN_WIDTH / 2
                else:
                    # Real data: use original coordinates
                    x_coord = math.cos(x / 180 * math.pi) * a + SCREEN_WIDTH / 2
                    y_coord = math.sin(x / 180 * math.pi) * a + SCREEN_WIDTH / 2

                if x in DECISIVE_FRAME_POSITIONS and highlight_frames:
                    # draw line to the point
                    pygame.draw.line(screen, (255, 0, 255), (SCREEN_WIDTH / 2, SCREEN_WIDTH / 2),
                                     (x_coord, y_coord), 2)

                    # Draw the important point with RED color
                    pygame.draw.circle(screen, (255, 0, 0), (x_coord, y_coord), 3)
                else:
                    # Draw the ordinary point with BLACK color
                    pygame.draw.circle(screen, (0, 0, 0), (x_coord, y_coord), 2)

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

            # Render the text - handle non-numeric turn values
            try:
                turn_value = float(distances[360])
                # Show different turn value based on mode
                display_turn = -turn_value if augmented_mode else turn_value
                mode_text = "AUGMENTED" if augmented_mode else "REAL"
                text = font.render("line: {}, turn: {:.2f} [{}]".format(
                    data_manager.read_pos, display_turn, mode_text), True, (0, 255, 255))
            except (ValueError, TypeError):
                # Handle non-numeric turn values (like headers)
                mode_text = "AUGMENTED" if augmented_mode else "REAL"
                text = font.render("line: {}, turn: {} [{}]".format(
                    data_manager.read_pos, distances[360], mode_text), True, (0, 255, 255))
            # Blit the text to the screen
            screen.blit(text, (350, 600))

            # draw the car
            pygame.draw.circle(screen, (252, 132, 3), (SCREEN_WIDTH / 2, SCREEN_WIDTH / 2), 12)
            pygame.draw.line(screen, (0, 0, 255), (SCREEN_WIDTH / 2, SCREEN_WIDTH / 2),
                             (SCREEN_WIDTH / 2 + 40, SCREEN_WIDTH / 2), 3)
            # Use convention: Full LEFT/RIGHT TURN = 45 degree (Pi/4)
            try:
                turn_value = float(distances[360])
                # Flip turn value for augmented data (mirror steering)
                if augmented_mode:
                    turn_value = -turn_value
                x = math.cos(turn_value * math.pi / 4) * 40
                y = math.sin(turn_value * math.pi / 4) * 40
                pygame.draw.line(screen, (0, 255, 0), (SCREEN_WIDTH / 2, SCREEN_WIDTH / 2),
                                 (SCREEN_WIDTH / 2 + x, SCREEN_WIDTH / 2 + y), 3)
            except (ValueError, TypeError):
                # Skip drawing turn direction for non-numeric values
                pass
            # Flip the display - swaps back buffer to front buffer to make all drawings visible
            # This is standard pygame double buffering, not related to data orientation
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
    import sys
    
    # Allow specifying data file as command line argument
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
        print(f"Using data file: {data_file}")
        run(data_file, True)
    else:
        # Default behavior - you can easily change this line to switch data sources
        # Option 1: Local data file
        run('data/run1/out1.txt', True)
        
        # Option 2: External training data file (uncomment to use)
        # run('/home/andy/lidar_training_data/lidar_training_data_20250727_095526.csv', True)
