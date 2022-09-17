#!/usr/bin/env python3

import string
import random
import datetime as dt

from functools import cmp_to_key
from flask import Flask, render_template, request, redirect, url_for, flash
from malarm import Malarm
from event_dispatcher import EventDispatcher
from json_helper import JsonHelper
from function import alarm_function, available_functions
    
app = Flask(__name__, template_folder="../templates")
app.secret_key = "".join([random.choice(string.ascii_letters + string.digits) for _ in range(20)])
json_helper = JsonHelper()


@app.route("/", methods=["GET"])
def index():
    if request.method == "GET":
        _format = "%H:%M (%d-%m-%Y)"
        event_list = dispatcher.get_current()
        event_list.sort(key=cmp_to_key(EventDispatcher.compare_events))
        current_events = [(e.time.strftime(_format), e.name) for e in event_list]
        last_update = json_helper.get_last_update()
        if last_update == dt.datetime(year=1, month=1, day=1):
            last_update = "Never"
        else:
            last_update = last_update.strftime(_format)
        _status = malarm.get_status().name

        return render_template("index.html", current_alarms=current_events
                               , last_update=last_update
                               , status=_status
                               , types = available_functions.keys())


@app.route("/set_alarm", methods=["POST"])
def set_alarm():
    alarm_due = dt.datetime.fromisoformat(request.form["datetime"])
    event_function = request.form["function"]
    msgs = dispatcher.dispatch(alarm_due, available_functions[event_function])
    if msgs:
        if isinstance(msgs, list):
            for msg in msgs:
                flash(msg)
        else:
            flash(msgs)

    return redirect(url_for("index"))


@app.route("/cancel_alarm", methods=["POST"])
def cancel_alarm():
    msg = dispatcher.cancel_event_by_name(request.form["name"])
    if msg:
        flash(msg)
    return redirect(url_for("index"))


@app.route("/cancel_all", methods=["POST"])
def cancel_all():
    dispatcher.cancel_all()
    return redirect(url_for("index"))


@app.route("/status", methods=["POST"])
def status():
    dispatcher.status()
    return redirect(url_for("index"))


@app.route("/magister_scrape", methods=["POST"])
def magister_scrape():
    malarm.refresh_magister_data()
    return redirect(url_for("index"))


@app.route("/setup_alarms", methods=["POST"])
def setup_alarms():
    msgs = malarm.setup_alarms(dispatcher)
    if msgs:
        if type(msgs) == list:
            for msg in msgs:
                flash(msg)
        else:
            flash(msgs)
    return redirect(url_for("index"))


if __name__ == "__main__":
    global m, dispatcher
    malarm = Malarm((1800, 2400, 1200), "../audio-files/alarm_sound.mp3", 10)
    dispatcher = EventDispatcher()
    app.run(host="0.0.0.0", port=5000, debug=True)
