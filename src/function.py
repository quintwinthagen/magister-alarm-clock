import time
import logging
import sys

from os import path

from contextlib import redirect_stdout

with redirect_stdout(None):
    from pygame import mixer

RPI = False
if "--rpi" in sys.argv:
    from RPi import GPIO

    RPI = True

class EventFunction:
    def __init__(self, fn, type: str):
        self.fn = fn
        self.type = type

    def __call__(self):
        time.sleep(0.1)
        self.fn()


def play_alarm() -> None:
    """Play alarm"""

    print("Playing alarm...")
    mixer.init()
    mixer.music.load(path.normpath(path.join(path.dirname(__file__), "../audio-files/alarm_sound.mp3")))

    if RPI:
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        mixer.music.play(-1)
        GPIO.wait_for_edge(10, GPIO.FALLING)
        mixer.music.stop()
    else:
        mixer.music.play()
        print("Type 'stop' to cut the alarm")
        while input() != "stop":
            pass
        mixer.music.stop()

    print("Played alarm")

def lights_on():
    print("Lights have been turned on")


def lights_off():
    print("lights have been turned off")


alarm_function = EventFunction(play_alarm, type='Alarm')
lights_on_function = EventFunction(lights_on, type="Lights On")
lights_off_function = EventFunction(lights_off, type="Lights Off")
available_functions = {"Alarm": alarm_function,
                       "Lights on": lights_on_function,
                       "Lights off": lights_off_function}
