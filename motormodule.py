import RPi.GPIO as GPIO
from time import sleep
import math

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

epsilon = 0.1
turn_rate = math.pi * 1.3


class Motor:
    def __init__(self, EnaA, In1A, In2A, EnaB, In1B, In2B):
        self.EnaA = EnaA
        self.In1A = In1A
        self.In2A = In2A
        self.EnaB = EnaB
        self.In1B = In1B
        self.In2B = In2B
        GPIO.setup(self.EnaA, GPIO.OUT)
        GPIO.setup(self.In1A, GPIO.OUT)
        GPIO.setup(self.In2A, GPIO.OUT)
        GPIO.setup(self.EnaB, GPIO.OUT)
        GPIO.setup(self.In1B, GPIO.OUT)
        GPIO.setup(self.In2B, GPIO.OUT)
        self.pwmA = GPIO.PWM(self.EnaA, 100)
        self.pwmA.start(0)
        self.pwmB = GPIO.PWM(self.EnaB, 100)
        self.pwmB.start(0)

    def move(self, speed=0.5, turn=0.0, t=0):
        axis1, axis2 = turn, speed
        a = int(max(abs(axis1), abs(axis2)) * 100)
        b = 1
        if abs(axis2) >= epsilon:
            b = int(math.atan(abs(axis1) / abs(axis2)) / turn_rate * a)
        if axis2 > epsilon:
            if axis1 < 0 - epsilon:
                outRight = a
                outLeft = b
            elif axis1 > epsilon:
                outLeft = a
                outRight = b
            else:
                outLeft = int(axis2 * 100)
                outRight = outLeft

            self.pwmA.ChangeDutyCycle(int(outLeft))
            self.pwmB.ChangeDutyCycle(int(outRight))
            self.move_dir("DOWN")
        elif axis2 < 0 - epsilon:
            if axis1 < 0 - epsilon:
                outRight = a
                outLeft = b
            elif axis1 > epsilon:
                outLeft = a
                outRight = b
            else:
                outLeft = int(abs(axis2) * 100)
                outRight = outLeft

            self.pwmA.ChangeDutyCycle(outLeft)
            self.pwmB.ChangeDutyCycle(outRight)
            self.move_dir("UP")
        elif abs(axis2) <= epsilon:
            outRight = int(abs(axis1) * 100)
            outLeft = outRight
            self.pwmA.ChangeDutyCycle(outLeft)
            self.pwmB.ChangeDutyCycle(outRight)

            if axis1 > epsilon:
                self.move_dir("LEFT")
            elif axis1 < 0 - epsilon:
                self.move_dir("RIGHT")
            else:
                self.move_dir("STOP")

        sleep(t)

    def move_dir(self, direction):
        if direction == "UP":
            self._motor_out(False, True, False, True)
        elif direction == "DOWN":
            self._motor_out(True, False, True, False)
        elif direction == "LEFT":
            self._motor_out(False, True, True, False)
        elif direction == "RIGHT":
            self._motor_out(True, False, False, True)
        else:
            self._motor_out(False, False, False, False)

    def _motor_out(self, in1, in2, in3, in4):
        GPIO.output(self.In1A, in1)
        GPIO.output(self.In2A, in2)
        GPIO.output(self.In1B, in3)
        GPIO.output(self.In2B, in4)

    def stop(self, t=0):
        self.pwmA.ChangeDutyCycle(0)
        self.pwmB.ChangeDutyCycle(0)
        sleep(t)


def main():
    motor = Motor(3, 5, 7, 15, 11, 13)
    motor.move(0.6, 0, 2)
    motor.stop(2)
    motor.move(-0.5, 0.2, 2)
    motor.stop(2)


if __name__ == '__main__':
    main()
