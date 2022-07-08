import time
import datetime as dt
import json
from io import BytesIO
from os import path
from os import system
from contextlib import redirect_stdout

from gtts import gTTS
from pydub import AudioSegment

with redirect_stdout(None):
    from pygame import mixer


class SpeechManager:

    def __init__(self, cache_folder="speech_cache"):
        mixer.init()

        if cache_folder.endswith("/"):
            self.path = cache_folder
        else:
            self.path = cache_folder + "/"

        if not path.exists(self.path + "regular.json"):
            system(f"mkdir {self.path} && touch {self.path}regular.json")
            with open(self.path+"regular.json", "w", encoding="utf-8") as reg_json:
                reg_json.write("{\n}")


    def play_speech(self, sound_file):
        mixer.music.load(sound_file)
        mixer.music.play()
        while mixer.music.get_busy():
            time.sleep(0.5)


    def add_speech(self, name:str, text:str, language="nl"):
        speech = gTTS(text=text, lang=language, slow=False)
        speech.save(self.path + name + ".mp3")
        regulars = self.get_cache()
        regulars[text] = name + ".mp3"
        with open(self.path + "regular.json", "w+", encoding="utf-8") as reg_json:
            json.dump(regulars, reg_json, indent=4, sort_keys=True, ensure_ascii=False)


    def play_good_morning(self):
        self.play_reg("Een hele goede morgen Quint")


    def play_bye(self):
        self.play_reg("Tot morgen, peace out.")


    def play_misc(self, text:str, language="nl"):
        file_obj = BytesIO()
        mp3_obj = BytesIO()
        speech = gTTS(text=text, lang=language, slow=False)
        speech.write_to_fp(file_obj)
        file_obj.seek(0)
        sound = AudioSegment.from_file(file_obj)
        mp3_obj = sound.export(file_obj, format="mp3")
        self.play_speech(mp3_obj)


    def play_reg(self, text:str, language="nl"):
        name = str(time.time())[11:]
        regulars = self.get_cache()
        if not text in regulars:
            self.add_speech(name, text, language=language)
            self.play_speech(self.path  + name + ".mp3")
        else:
            self.play_speech(self.path + regulars[text])

    
    def get_cache(self):
        with open(self.path + "regular.json", "r", encoding="utf-8") as reg_json:
            regular = json.load(reg_json)

        return regular


if __name__ == "__main__":
    sm = SpeechManager(cache_folder="../speech_cache")
    sm.play_good_morning()
    sm.play_reg("Dit is een test. Dit bericht word opgeslagen voor later gebruik")
    sm.play_misc("Dit is ook een test. Dit bericht wordt niet opgeslagen")
    print(json.dumps(sm.get_cache(), indent=4, sort_keys=True))
