#!/usr/bin/env python3
"""Records measurements to a given file in csv format. Usage example:

$ ./lidar_control.py out.txt"""
import time

from rplidar import RPLidar

PORT_NAME = '/dev/ttyUSB0'
# constant based on lidar resolution
LIDAR_RESOLUTION = 360


def nvl(value, default):
    return value if value is not None else default


class LidarControl:
    def __init__(self, port=PORT_NAME, path='out.txt', stop_flag=False, metrics=None):
        self.outfile = None
        self.lidar = None
        self.port = port
        self.path = path
        self.stop_flag = stop_flag
        self.metrics = metrics
        if self.metrics is None:
            self.metrics = {'turn': 0.0, 'speed': 0.0}
        self.lidar = RPLidar(self.port)
        self.lidar.get_info()

    def start(self):
        self.outfile = open(self.path, 'w')
        self.lidar.connect()
        self.lidar.start_motor()
        self.lidar.start()

    def record_line(self):
        """
        return a frame scan of 360 data points
        """
        print('Recording\n')
        line = self.lidar.read_single_measure()
        line += ",{:.2f}".format(self.metrics['turn']) + '\n'
        self.outfile.write(line)

        return line

    def read_line(self):
        return self.lidar.read_single_measure()

    def stop_record(self):
        """
        stop recording and write to csv file
        """
        self.stop()
        self.outfile.close()

    def stop(self):
        self.stop_flag = True
        self.lidar.stop()
        self.lidar.disconnect()


if __name__ == '__main__':
    recorder = LidarControl(port='COM6')
    recorder.start()
    for i in range(10):
        time.sleep(0.1)
        print(recorder.record_line())
    recorder.stop_record()
