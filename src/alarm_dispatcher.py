#!/usr/bin/env python3

import sys
import time
import datetime as dt
import threading
import logging
import sched

from os import path, mkdir

from dataclasses import dataclass
from contextlib import redirect_stdout

with redirect_stdout(None):
    from pygame import mixer

RPI = False
if "--rpi" in sys.argv:
    from RPi import GPIO

    RPI = True


class scheduler_with_polling(sched.scheduler):
    def __init__(self, timefn, waitfn, **kwargs):
        super().__init__(timefn, waitfn)
        self.polling_interval = kwargs.get('polling_interval', 0.01)

    def run(self):
        self.enter(self.polling_interval, 1, self.__poll)
        super().run()

    def __poll(self):
        if self.queue:
            self.enter(self.polling_interval, 1, self.__poll)

    # def cancel(self, event):
    #     # self.log.info("{scheduler_with_polling}: cancelling...")
    #     super().cancel(event)


@dataclass
class AlarmEvent:
    """Class for keeping track of alarm thread info"""
    name: str
    time: dt.datetime
    thread: threading.Thread
    scheduler: sched.scheduler

    def __repr__(self):
        return f"({self.name} at {self.time.isoformat(' ', timespec='minutes')})"


class AlarmDispatcher:

    def __init__(self, audio_path: str, pin: int) -> None:
        self.audio_path = path.normpath(path.join(path.dirname(__file__), audio_path))
        self.pin = pin
        self.alarm_events = []
        mixer.init()

        if RPI:
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        self.alarm_counter = 0
        self.__init_logger()

    def __init_logger(self):
        self.log = logging.getLogger("Alarm Dispatcher")
        self.log.setLevel(logging.DEBUG)
        m_format = "(%(levelname)s) [%(name)s] %(asctime)s: %(message)s"
        m_main_formatter = logging.Formatter(m_format)

        m_stream_handler = logging.StreamHandler()
        m_stream_handler.setFormatter(m_main_formatter)

        log_path = path.normpath(path.join(path.dirname(__file__), "../logs"))
        log_file = path.join(log_path, "malarm.log")

        m_file_handler = logging.FileHandler(log_file)
        m_file_handler.setFormatter(m_main_formatter)

        self.log.addHandler(m_stream_handler)
        self.log.addHandler(m_file_handler)
        self.log.debug("Succesfully initialized logger")

    def play_alarm(self) -> None:
        """Play alarm"""

        self.log.info("Playing alarm...")
        mixer.music.load(self.audio_path)

        if RPI:
            mixer.music.play(-1)
            GPIO.wait_for_edge(self.pin, GPIO.FALLING)
            mixer.music.stop()
        else:
            mixer.music.play()
            self.log.info("Type 'stop' to cut the alarm")
            if input() == "stop":
                mixer.music.stop()

        self.log.debug("Played alarm")

    def dispatch(self, _time: dt.datetime, nameprefix):

        def alarm_schedule_function(_scheduler, _time: dt.datetime):
            _scheduler.enterabs(_time.timestamp(), 1, self.play_alarm)
            _scheduler.run()
            self.log.debug("done with thread, removing from list...")
            for event in self.alarm_events:
                if event.thread == threading.current_thread():
                    self.alarm_events.remove(event)
                    break

        for alarm_event in self.alarm_events:
            if alarm_event.time == _time:
                return "Duplicate alarm found, not dispatching it"

        self.alarm_counter += 1
        _name = f"{nameprefix}-{self.alarm_counter}"
        _scheduler = scheduler_with_polling(time.time, time.sleep)
        _thread = threading.Thread(target=alarm_schedule_function
                                   , args=(_scheduler, _time)
                                   , name=_name
                                   , daemon=True)
        _thread.start()
        event = AlarmEvent(_name, _time, _thread, _scheduler)
        self.alarm_events.append(event)
        self.log.info("Set alarm: %s", event)
        return "Succesfully set new alarm."

    def cancel_alarm(self, alarm_event: AlarmEvent):
        scheduler_event = alarm_event.scheduler.queue[1]
        alarm_event.scheduler.cancel(scheduler_event)
        self.log.info("Removed alarm: %s", alarm_event)
        time.sleep(0.05)

    def cancel_alarm_by_name(self, _name):
        for alarm_event in self.alarm_events:
            if alarm_event.name == _name:
                self.cancel_alarm(alarm_event)
                return f"Removed {_name}"
        return f"There is no alarm with name {_name}"

    def cancel_all(self):
        self.log.info("Cancelling all alarms...")
        while self.alarm_events:
            self.cancel_alarm(self.alarm_events[0])
        time.sleep(0.15)

        if len(self.alarm_events) != 0:
            self.log.error("failed to cancel all alarms")
            self.status()

    def status(self):
        string = "\n--STATUS--\n--Running Threads--\n"

        for thread in threading.enumerate():
            string += repr(thread) + "\n"

        string += "--self.alarm_events--\n"
        for alarm_event in self.alarm_events:
            string += repr(alarm_event) + "\n"

        self.log.info(string)

    def get_current(self) -> list:
        return self.alarm_events

    @staticmethod
    def compare_events(event1, event2):
        if event1.time < event2.time:
            return -1
        elif event1.time > event2.time:
            return 1
        return 0
