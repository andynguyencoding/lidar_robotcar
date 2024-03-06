from motormodule import Motor
from joystickmodule import get_joystick
from lidar_control import LidarControl
from mldriver import predict_dir

motor = Motor(3, 5, 7, 15, 13, 11)
metrics = {'turn': 0.0, 'speed': 0.0}
lidarControl = None
recording = False
auto = False

while True:
    joystick = get_joystick()
    if joystick['b'] == 1:
        if lidarControl is None:
            lidarControl = LidarControl(port='/dev/ttyUSB0', metrics=metrics)
            lidarControl.start()
            recording = True
        print('Button b pressed')
    elif joystick['a'] == 1:
        recording = False
        lidarControl.stop_record()
        lidarControl = None
        print('Button a pressed')
    elif joystick['L2'] == 1:
        print('L2 pressed! RobotCar in self-driving mode!')
        if lidarControl is None:
            lidarControl = LidarControl(port='/dev/ttyUSB0', metrics=metrics)
            lidarControl.start()
        auto = True
    elif joystick['R2'] == 1:
        print('R2 pressed! RobotCar in manual mode!')
        auto = False
        lidarControl.stop()
        lidarControl = None
    elif joystick['x'] == 1:
        recording = False
        if lidarControl is not None:
            lidarControl.stop_record()
            lidarControl = None
        break

    speed = 0 - joystick['hat1']  # Reverse the sign, depend on the joystick specs
    turn = joystick['hat0']
    if joystick['axis1'] != 0:
        speed = joystick['axis1']
    if joystick['axis0'] != 0:
        turn = joystick['axis0']

    metrics['speed'] = speed
    metrics['turn'] = turn

    if recording:  # When in recording data mode
        lidarControl.record_line()
    elif auto:  # When in auto mode
        measure = lidarControl.read_line()
        speed = -0.9
        turn = predict_dir(measure)

    if abs(speed) < 0.1 and abs(turn) < 0.1:
        motor.stop()
    else:
        motor.move(speed, turn, 0)
