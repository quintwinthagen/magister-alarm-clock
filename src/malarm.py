#!/usr/bin/env python3
"""A python projects that rings my alarm at the right time
   each day by checking my schedule on Magister"""

# Standard imports
import time
import logging
import sys
import threading
import datetime as dt

from os import path, mkdir
from enum import Enum

# Selenium imports
from selenium import webdriver
# from selenium.common.exceptions import NoSuchElementException
import selenium.webdriver.remote.remote_connection
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

# Third-party-imports
from bs4 import BeautifulSoup

# Custom imports
# from speech import SpeechManager
from alarm_dispatcher import AlarmDispatcher
from json_helper import JsonHelper


class MalarmStatus(Enum):
    Running = "Running"
    Scraping = "Scraping Magister"


class Malarm():
    """Main Magister alarm class"""

    def __init__(self, times: tuple, audio_path: str, pin: int, DEBUG=False) -> None:
        """Initialize the instance variables and print a startup message"""

        self.DEBUG = DEBUG
        self.RUNNING = False
        self.pin = pin
        self.audio_path = audio_path
        self.TRAVEL_T, self.PREP_T, self.PRIME_T = [dt.timedelta(seconds=i) for i in times]
        self.driver = None
        self.status = MalarmStatus.Running

        self.__init_logger()

        # self.speech_manager = SpeechManager(cache_folder="speech_cache")
        self.alarm_dispatcher = AlarmDispatcher(self.audio_path, self.pin)
        self.json_helper = JsonHelper(json_dir="../")
        self.json_helper.initialize()
        self.upcoming_school_alarms = []

    def __init_logger(self) -> None:
        """Initialize logger variables"""

        self.log = logging.getLogger("Malarm")
        self.log.setLevel(logging.DEBUG if self.DEBUG else logging.INFO)
        self.log.setLevel(logging.DEBUG)

        selenium.webdriver.remote.remote_connection.LOGGER.setLevel(logging.CRITICAL)

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

        self.log.addHandler(m_stream_handler)
        self.log.addHandler(m_file_handler)
        self.log.debug("Succesfully initialized logger")


    def get_html(self) -> str:
        """Uses the selenium browser simulator to log in to Magister
           and returns the html source of the page with all the relevant data"""

        self.log.info("Fetching magister html")

        creds = self.json_helper.get_credentials()
        if not creds["username"] or not creds["password"]:
            self.log.critical("Credentials not complete")
            return ""

        try:
            m_opt = webdriver.ChromeOptions()
            m_opt.add_argument("--window-position=0,0")
            m_opt.add_argument("--window-size=1080,1080")
            self.driver = webdriver.Chrome(options=m_opt)


            self.log.info("Starting webscrape")
            self.driver.get("https://esprit.magister.net")
            self.await_page_load()
            time.sleep(2)

            actions = ActionChains(self.driver)
            actions.send_keys(creds["username"])
            actions.perform()
            time.sleep(2)

            username_submit = self.driver.find_element(By.ID, "username_submit")
            username_submit.click()
            self.await_page_load()

            if not "microsoft" in self.driver.current_url:
                self.log.critical("Failed to login (microsoft not in url)")
                return ""

            time.sleep(2)
            actions.send_keys(creds["password"])
            actions.perform()
            time.sleep(2)

            pw_submit = self.driver.find_element(By.ID, "idSIButton9")
            pw_submit.click()
            self.await_page_load()
            actions.send_keys(u"\ue007")
            actions.perform()
            time.sleep(2)

            self.driver.get("https://esprit.magister.net/magister/#/agenda")

            if not "agenda" in self.driver.current_url:
                self.log.critical("Failed to login (agenda not in url)")
                return ""

            self.await_page_load()
            self.log.info("Succesfull login")
            time.sleep(3)
            html = self.driver.page_source

            self.log.debug("Html fetch completed succesfully")
            return html
        except:
            self.log.exception("Failed to fetch html")

        finally:
            self.driver.quit()

    def process_html(self, html) -> None:
        """Takes in the html of the page and parses the relevant information,
           which is then dumped into a json file"""

        self.log.info("Starting the processing of the html")

        self.json_helper.update_previous()
        time_at_start = time.time() * 1000
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.find(class_="k-grid-content").tbody.find_all("tr")

        data = []
        day_counter = -1

        for entry in rows:
            if entry.has_attr("role") and entry["role"] == "row":
                day_counter += 1
                date = self.text_to_date(entry.text.strip())

                data.append(
                    {"date":
                         {"day": date[0], "mon": date[1]},
                     "sched_exception": 0,
                     "hours": []})
            elif entry.find(attrs={"ng-bind": "dataItem.lesuur"}):
                hour_data = entry.find_all("td")[2]
                if hour_data:
                    lesson = hour_data.text.strip()[1:].strip().replace("\n", " ")
                    hour_number = int(hour_data.text.strip()[0])
                    timeslot = self.find_timeslot(hour_number, short=False)

                    if data[day_counter]["sched_exception"] == 1:
                        timeslot = self.find_timeslot(hour_number, short=True)

                    hour_data = {"number": hour_number,
                                 "lesson": lesson,
                                 "timeslot": timeslot}
                    data[day_counter]["hours"].append(hour_data)

            else:
                verkort_rooster = ("verkort rooster" in entry.text.lower())
                min_rooster = ("40 minuten rooster" in entry.text.lower())
                no_min_rooster = (not "geen 40 minuten rooster" in entry.text.lower())

                if (verkort_rooster or min_rooster) and no_min_rooster:
                    data[day_counter]["sched_exception"] = 1

                elif "roostervrije dag" in entry.text.lower():
                    data[day_counter]["sched_exception"] = 2

        self.json_helper.write_out(data)

        self.log.info("Finished processing")
        self.log.debug("Processing html took: %d milliseconds", time.time() * 1000 - time_at_start)


    def find_timeslot(self, amount: int, short=False) -> str:
        """Converts the schedule index to a timeslot string"""

        if amount - 1 > 9 or amount < 1:
            self.log.error("FindTimeslot: amount not in range")
            return ""

        times = ["08:30 - 09:20",
                 "09:20 - 10:10",
                 "10:10 - 11:00",
                 "11:20 - 12:10",
                 "12:10 - 13:00",
                 "13:30 - 14:20",
                 "14:20 - 15:10",
                 "15:10 - 16:00",
                 "16:10 - 17:00"]

        times_short = ["08:30 - 09:10",
                       "09:10 - 09:50",
                       "09:50 - 10:30",
                       "10:50 - 11:30",
                       "11:30 - 12:10",
                       "12:10 - 12:50",
                       "13:20 - 14:00",
                       "14:00 - 14:40",
                       "14:40 - 15:20"]

        return times_short[amount - 1] if short else times[amount - 1]


    def await_page_load(self) -> None:
        """A blocking function that returns once the page is loaded"""

        while not self.driver.execute_script("return document.readyState") == "complete":
            time.sleep(1)

        time.sleep(2)
        self.log.debug("Page has loaded")


    def dispatch_alarm(self, _time: dt.datetime, nameprefix="alarm"):
        return self.alarm_dispatcher.dispatch(_time, nameprefix)


    def get_dispatcher(self) -> AlarmDispatcher:  # TODO(make dispatcher property and use @property decorator)
        return self.alarm_dispatcher


    def refresh_magister_data(self):

        def thread_func():
            self.log.info("Started new thread to refresh magister data")
            self.status = MalarmStatus.Scraping
            try:
                html = self.get_html()
                if html:
                    self.process_html(html)
                    self.json_helper.last_update_data(dt.datetime.now())
                else:
                    self.log.critical("Cannot process html if fetch failed")
            except:
                self.log.exception("Exception inside refresh thread")
            finally:
                self.status = MalarmStatus.Running

        refresh_thread = threading.Thread(target=thread_func, name="refresh thread", daemon=True)
        refresh_thread.start()


    def get_status(self) -> MalarmStatus:
        return self.status


    def setup_alarms(self):
        self.log.info("Setting up alarms...")
        return_list = []
        data = self.json_helper.get_out()
        now = dt.datetime.now()
        for day in data:
            if day["hours"]:
                day_start = dt.datetime.combine(dt.date(now.year, day["date"]["mon"], day["date"]["day"]),
                                                dt.datetime.strptime(
                                                    day["hours"][0]["timeslot"][:5],
                                                    "%H:%M").time())
                alarm_dt = day_start - self.TRAVEL_T - self.PREP_T
                if now > alarm_dt:
                    return_list.append("Found alarm before now")
                    continue

                for upcoming_school_alarm in self.upcoming_school_alarms:
                    if upcoming_school_alarm.date() == alarm_dt.date():
                        self.upcoming_school_alarms.remove(upcoming_school_alarm)

                self.upcoming_school_alarms.append(alarm_dt)

                msg = self.dispatch_alarm(alarm_dt, nameprefix="school")
                if msg:
                    return_list.append(msg)
        return return_list


    @staticmethod
    def find_dropped(hours: dict) -> list:
        """Returns a list of integers, each of which represents a dropped hour"""

        dropped = []
        first_hour = hours[0]["number"]
        last_hour = hours[len(hours) - 1]["number"]
        present = [hour["number"] for hour in hours]
        for i in range(first_hour, last_hour + 1):
            if not i in present:
                dropped.append(i)

        return dropped


    @staticmethod
    def get_speech_str(today: dict, day_start: dt.datetime) -> str:
        """Returns a string that introduces me to my day"""

        if today["hours"]:
            lesson_lut = {"NETL": "nederlands",
                          "SCHK": "scheikunde",
                          "FI": "filosofie",
                          "WISB": "wiskunde b",
                          "NAT": "natuurkunde",
                          "ENTL": "engels",
                          "BIOL": "biologie",
                          "LTC": "latijn",
                          "PE": "gym"}

            lesson = today["hours"][0]["lesson"].split(" - ")
            lesson_str = lesson_lut.get(lesson[0]) or "een onbekend vak"

            is_short = ""

            if today["sched_exception"] == 1:
                is_short = "Vandaag heb je verkort rooster. "
            elif today["sched_exception"] == 2:
                is_short = "Vandaag heb je een roostervrije dag. "

            dropped = ",".join([str(i) + "e" for i in Malarm.find_dropped(today["hours"])])
            dropped_str = "Je hebt vandaag de volgende tussenuren: het " + dropped if dropped else "Je hebt vandaag geen tussenuren"

            to_return = (f"Je begint vandaag het {today['hours'][0]['number']}e uur"
                         f"met {lesson_str} om "
                         f"{day_start.time().isoformat(timespec='minutes')}. "
                         f"{is_short}{dropped_str}. Fijne dag!")

            return to_return

        return "Je hebt vandaag vrij, dus ik weet niet waarom je een wekker zet, oelewapper!"

    @staticmethod
    def text_to_date(text: str) -> list:
        """Converts Dutch date string to day and month numbers"""

        lut_mon = {"januari": 1,
                   "februari": 2,
                   "maart": 3,
                   "april": 4,
                   "mei": 5,
                   "juni": 6,
                   "juli": 7,
                   "augustus": 8,
                   "september": 9,
                   "oktober": 10,
                   "november": 11,
                   "december": 12
                   }
        parts = text.split()
        parts[1] = int(parts[1])
        parts[2] = lut_mon[parts[2]]
        parts = parts[1:]
        return parts

    def __del__(self) -> None:
        """Destructor of the class, makes sure the selenium driver is always closed"""

        try:
            self.driver.quit()
        except AttributeError:
            pass


if __name__ == "__main__":
    DEBUG_ARG = len(sys.argv) > 1 and sys.argv[1] == "-d"
    m = Malarm((1800, 2400, 1200), "../audio-files/alarm_sound.mp3", 10, DEBUG=DEBUG_ARG)
