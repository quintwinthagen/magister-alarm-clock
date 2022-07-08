#!/usr/bin/env python3

import string
import random
import datetime as dt

from functools import cmp_to_key
from flask import Flask, render_template, request, redirect, url_for, flash
from malarm import Malarm
from alarm_dispatcher import AlarmDispatcher
from json_helper import JsonHelper

app = Flask(__name__, template_folder="../templates")
app.secret_key = "".join([random.choice(string.ascii_letters + string.digits) for _ in range(20)])
json_helper = JsonHelper()


@app.route("/", methods=["GET"])
def index():
    if request.method == "GET":
        _format = "%H:%M (%d-%m-%Y)"
        alarm_event_list = m.get_dispatcher().get_current()
        alarm_event_list.sort(key=cmp_to_key(AlarmDispatcher.compare_events))
        current_alarms = [(e.time.strftime(_format), e.name) for e in alarm_event_list]
        last_update = json_helper.get_last_update()
        if last_update == dt.datetime(year=1, month=1, day=1):
            last_update = "Never"
        else:
            last_update = last_update.strftime(_format)
        upcoming_school_alarms = [alarm.strftime(_format) for alarm in m.upcoming_school_alarms]
        _status = m.get_status().name

        return render_template("index.html", current_alarms=current_alarms
                               , upcoming_school_alarms=upcoming_school_alarms
                               , last_update=last_update
                               , status=_status)


@app.route("/set_alarm", methods=["POST"])
def set_alarm():
    alarm_due = dt.datetime.fromisoformat(request.form["datetime"])
    msgs = m.dispatch_alarm(alarm_due, nameprefix="custom")
    if msgs:
        if isinstance(msgs, list):
            for msg in msgs:
                flash(msg)
        else:
            flash(msgs)

    return redirect(url_for("index"))


@app.route("/cancel_alarm", methods=["POST"])
def cancel_alarm():
    msg = m.get_dispatcher().cancel_alarm_by_name(request.form["name"])
    if msg:
        flash(msg)
    return redirect(url_for("index"))


@app.route("/cancel_all", methods=["POST"])
def cancel_all():
    m.get_dispatcher().cancel_all()
    return redirect(url_for("index"))


@app.route("/status", methods=["POST"])
def status():
    m.alarm_dispatcher.status()
    return redirect(url_for("index"))


@app.route("/magister_scrape", methods=["POST"])
def magister_scrape():
    m.refresh_magister_data()
    return redirect(url_for("index"))


@app.route("/setup_alarms", methods=["POST"])
def setup_alarms():
    msgs = m.setup_alarms()
    if msgs:
        if type(msgs) == list:
            for msg in msgs:
                flash(msg)
        else:
            flash(msgs)
    return redirect(url_for("index"))


if __name__ == "__main__":
    global m
    m = Malarm((1800, 2400, 1200), "../audio-files/alarm_sound.mp3", 10, DEBUG=False)
    # m.run()
    app.run(host="0.0.0.0", port=5000, debug=True)
