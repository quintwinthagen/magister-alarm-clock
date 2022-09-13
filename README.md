# magister-alarm-clock
A python project that turns your device into an alarm clock. It scrapes schedule data from Magister (Esprit only) and wakes you up accordingly. A Flask web interface lets you set and remove alarms remotely. Initially designed for the Raspberry Pi.

## Getting started
1. Install the required python libraries with `python3 -m pip install -r requirements.txt`
2. Run `app.py` in the `src` directory. If you are running this on a Raspberry Pi, use the `--rpi` flag and connect a push button to pin 10. This will then serve as an alarm stopping button. Without the flag set, type `stop` to stop a playing alarm.
3. Enter your Magister credentials when prompted
4. Enjoy. You can acces the web interface on your local machine at `http://127.0.0.1:5000` or from any other device on your local network with the IP adress of the host device, at port 5000

### Notes
This is a personal project and is not meant for anyone to start using, and will thus not receive updates or bugfixes. You can use the code but know that it is not very stable. Besides, the web scraping code is designed to work with a specific schools login page (i.e. Microsoft).

---
Web interface on startup (without scrape data)
![magister-alarm-clock-new](https://user-images.githubusercontent.com/60112845/178141688-a6ebcf37-ae5d-46ab-bfa7-d0071f16c468.png)

Web interface when having scraped
![magister-alarm-clock-scraped](https://user-images.githubusercontent.com/60112845/178141707-6552fa59-4daa-43bd-ae5b-05a3c9d2f558.png)

Web interface when having pushed setup and with alarms set
![magister-alarm-clock-with-alarms](https://user-images.githubusercontent.com/60112845/178141717-582f5e00-1447-4c51-b7e4-e964e1c6b4ad.png)
