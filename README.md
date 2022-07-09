# magister-alarm-clock
A python projects that turns your device into an alarm clock. It scrapes schedule data from Magister (Esprit only) and wakes you up accordingly. A Flask web interface lets you set and remove alarms remotely. Initially designed for the Raspberry Pi.

## Getting started
1. Install the required python libraries with `python3 -m pip install -r requirements.txt`
2. Run `app.py` in the `src` directory. If you are running this on a Raspberry Pi, use the `--rpi` flag and connect a push button to pin 10. This will then serve as an alarm stopping button.
3. Enter your Magister credentials when prompted
4. Enjoy. You can acces the web interface on your local machine at `http://127.0.0.1:5000` or from any other device on your local network with the IP adress of the host device, at port 5000
