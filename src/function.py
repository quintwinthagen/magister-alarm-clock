import time


class EventFunction:
    def __init__(self, fn, type: str):
        self.fn = fn
        self.type = type

    def __call__(self):
        time.sleep(0.1)
        self.fn()


def play_alarm():
    print('BEEEEEEEP BEEEEEEEEP')


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
