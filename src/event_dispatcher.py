#!/usr/bin/env python3

import time
import datetime as dt
import threading
import logging
import sched

from os import path, mkdir

from function import EventFunction, alarm_function


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


class ScheduledEvent:
    """Class for keeping track of event thread info"""
    def __init__(self, name, time, thread, scheduler):
        self.name = name
        self.time = time
        self.thread = thread
        self.scheduler = scheduler

    def __repr__(self):
        return f"({self.name} at {self.time.isoformat(' ', timespec='minutes')})"


class EventDispatcher:

    def __init__(self) -> None:
        self.events = []
        self.event_counter = 0
        self.__init_logger()

    def __init_logger(self):
        self.log = logging.getLogger("Event Dispatcher")
        self.log.setLevel(logging.DEBUG)
        m_format = "(%(levelname)s) [%(name)s] %(asctime)s: %(message)s"
        m_main_formatter = logging.Formatter(m_format)

        m_stream_handler = logging.StreamHandler()
        m_stream_handler.setFormatter(m_main_formatter)

        log_path = path.normpath(path.join(path.dirname(__file__), "../logs"))
        if not path.exists(log_path):
            mkdir(log_path)

        log_file = path.join(log_path, "malarm.log")
        if not path.exists(log_file):
            with open(log_file, "w"): pass

        m_file_handler = logging.FileHandler(log_file)
        m_file_handler.setFormatter(m_main_formatter)

        if (self.log.hasHandlers()):
            self.log.handlers.clear()

        self.log.addHandler(m_stream_handler)
        self.log.addHandler(m_file_handler)
        self.log.debug("Succesfully initialized logger")
        
        
    def dispatch(self, _time: dt.datetime, func: EventFunction):

        def schedule_function(_scheduler, _time: dt.datetime):
            _scheduler.enterabs(_time.timestamp(), 1, func)
            _scheduler.run()
            self.log.debug("done with thread, removing from list...")
            for event in self.events:
                if event.thread == threading.current_thread():
                    self.events.remove(event)
                    break

        for event in self.events:
            if event.time == _time and func.type in event.name:
                return "Duplicate event found, not dispatching it"

        self.event_counter += 1
        _name = f"{func.type}-{self.event_counter}"
        _scheduler = scheduler_with_polling(time.time, time.sleep)
        _thread = threading.Thread(target=schedule_function
                                   , args=(_scheduler, _time)
                                   , name=_name
                                   , daemon=True)
        _thread.start()
        event = ScheduledEvent(_name, _time, _thread, _scheduler)
        self.events.append(event)
        self.log.info("Scheduled event: %s", event)
        return "Succesfully set new event."

    def cancel_event(self, event: ScheduledEvent):
        scheduler_event = event.scheduler.queue[1]
        event.scheduler.cancel(scheduler_event)
        self.log.info("Removed event: %s", event)
        time.sleep(0.05)

    def cancel_event_by_name(self, _name):
        for event in self.events:
            if event.name == _name:
                self.cancel_event(event)
                return f"Removed {_name}"
        return f"There is no event with name {_name}"

    def cancel_all(self):
        self.log.info("Cancelling all events...")
        while self.events:
            self.cancel_event(self.events[0])
        time.sleep(0.15)

        if len(self.events) != 0:
            self.log.error("failed to cancel all events")
            self.status()

    def status(self):
        string = "\n--STATUS--\n--Running Threads--\n"

        for thread in threading.enumerate():
            string += repr(thread) + "\n"

        string += "--self.events--\n"
        for event in self.events:
            string += repr(event) + "\n"

        self.log.info(string)

    def get_current(self) -> list:
        return self.events

    @staticmethod
    def compare_events(event1, event2):
        if event1.time < event2.time:
            return -1
        elif event1.time > event2.time:
            return 1
        return 0

    
if __name__ == '__main__':
    ad = EventDispatcher()
    time.sleep(5)
    n = dt.datetime.now()
    ad.dispatch(n + dt.timedelta(seconds=5) , alarm_function)
    #ad.status()
    
