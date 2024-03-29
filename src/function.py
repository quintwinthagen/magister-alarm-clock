import time
import logging
import sys

from os import path
from contextlib import redirect_stdout

from speech import SpeechManager

with redirect_stdout(None):
    from pygame import mixer

RPI = False
if "--rpi" in sys.argv:
    from RPi import GPIO

    RPI = True

sm = SpeechManager()

class EventFunction:
    def __init__(self, fn, type: str):
        self.fn = fn
        self.type = type

    def __call__(self):
        time.sleep(0.1)
        self.fn()


def play_alarm() -> None:
    """Play alarm"""

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

    time.sleep(2)
    sm.play_good_morning() #Play good morning when alarm has just stopped
    time.sleep(2)
    sm.play_bye()

alarm_function = EventFunction(play_alarm, type='Alarm')
good_morning_function = EventFunction(sm.play_good_morning, type="Good morning")
available_functions = {"Alarm": alarm_function,
                       "Good morning": good_morning_function}
