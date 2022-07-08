#!/usr/bin/env python3

import json
import sys
import datetime as dt

from os import path


class JsonHelper:
    def __init__(self, json_dir="../"):
        self.path = json_dir

    def get_absolute_path(self, relative_path: str) -> str:
        return path.normpath(path.join(path.dirname(__file__), self.path, relative_path))

    def initialize(self):
        for f in ["config.json", "out.json", "credentials.json", "prev_out.json"]:
            abs_path = self.get_absolute_path(f)
            if not path.exists(abs_path):
                with open(abs_path, "w+", encoding="utf-8") as fhandler:
                    # self.log.debug("Created file: %s", f)
                    print(f"Created file: {f}")
                    if f == "credentials.json":
                        username = input("Magister username: ") or ""
                        password = input("Magister password: ") or ""
                        json.dump({"username": username,  "password": password), fhandler, indent=4)
                    if f in ("out.json", "prev_out.json"):
                        fhandler.write("{}")

                    if f == "config.json":
                        json.dump({"last_update": dt.datetime(year=1, month=1, day=1).isoformat()}, fhandler)
        if not self.get_credentials()["username"] or not self.get_credentials()["password"]:
            print("--- Credentials not complete ---")


    def get_out(self) -> dict:
        with open(self.get_absolute_path("out.json"), "r", encoding="utf-8") as out:
            data = json.load(out)
            return data

    def get_last_update(self) -> dt.datetime:
        with open(self.get_absolute_path("config.json"), "r", encoding="utf-8") as config:
            data = json.load(config)
            return dt.datetime.fromisoformat(data["last_update"])

    def get_credentials(self) -> dict:
        with open(self.get_absolute_path("credentials.json"), "r", encoding="utf-8") as creds:
            data = json.load(creds)
            if "username" not in data:
                print("Username not found!")
            if "password" not in data:
                print("Password not found!")
        return data

    def write_out(self, data: list) -> None:
        with open(self.get_absolute_path("out.json"), "w", encoding="utf-8") as out:
            json.dump(data, out, sort_keys=True, indent=4)

    def last_update_data(self, last_update: dt.datetime) -> None:
        with open(self.get_absolute_path("config.json"), "w", encoding="utf-8") as config:
            json.dump({"last_update": last_update.isoformat()}, config, sort_keys=True, indent=True)

    def update_previous(self) -> None:
        with open(self.get_absolute_path("prev_out.json"), "w+", encoding="utf-8") as prev_out:
            json.dump(self.get_out(), prev_out, indent=4)


if __name__ == "__main__":
    jh = JsonHelper()
    jh.initialize()
#     print(jh.get_out())
#     jh.write_out({"test": "mest"})
#     jh.update_previous()
#     jh.last_update_data(dt.datetime.now())
