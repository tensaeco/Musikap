main_code = r'''
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.storage.jsonstore import JsonStore
from threading import Thread
import requests
import os
import time

try:
from jnius import autoclass
PythonActivity = autoclass('org.kivy.android.PythonActivity')
Intent = autoclass('android.content.Intent')
Uri = autoclass('android.net.Uri')
File = autoclass('java.io.File')
ON_ANDROID = True
except ImportError:
ON_ANDROID = False

REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"

MOOD_MAP = {
'ደስታ': 'joyful',
'ሐሴት': 'happy and uplifting',
'ስሜት ጭንቀት': 'tense and anxious',
'ሰላም': 'peaceful and calm',
}
TEMPO_MAP = {
'ቀዝቃዛ': 'slow tempo',
'መካከለኛ': 'medium tempo',
'ፈጣን': 'fast tempo',
}
INSTRUMENT_MAP = {
'ፒያኖ': 'piano',
'ጊታር': 'guitar',
'ቤስ': 'bass',
'ድምጽ': 'vocals',
'ሙሉ ኦርኬስትራ': 'full orchestra',
}

class MusicGeneratorApp(App):
def build(self):
self.store = JsonStore('settings.json')
self.saved_key = ''
if self.store.exists('api'):
self.saved_key = self.store.get('api')['key']

self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)  

    self.key_label = Label(  
        text="🔑 Replicate API Key:" if not self.saved_key else "🔑 API Key ተቀምጧል ✓",  
        size_hint=(1, 0.07), halign='left'  
    )  
    self.layout.add_widget(self.key_label)  

    self.api_key_input = TextInput(  
        multiline=False, password=True,  
        hint_text="r8_xxxx...",  
        text=self.saved_key,  
        size_hint=(1, 0.10)  
    )  
    self.layout.add_widget(self.api_key_input)  

    self.save_key_button = Button(  
        text="🔑 Key ያስቀምጡ",  
        size_hint=(1, 0.09),  
        background_color=(0.2, 0.6, 0.2, 1)  
    )  
    self.save_key_button.bind(on_press=self.save_key)  
    self.layout.add_widget(self.save_key_button)  

    self.label = Label(  
        text="እባክዎ አማርኛ መግለጫ ያስገቡ:",  
        size_hint=(1, 0.07), halign='center'  
    )  
    self.layout.add_widget(self.label)  

    self.input_text = TextInput(  
        multiline=False,  
        hint_text="ለምሳሌ: የምሽት ዝናብ ድምጽ",  
        size_hint=(1, 0.10)  
    )  
    self.layout.add_widget(self.input_text)  

    self.mood_spinner = Spinner(  
        text='ሁኔታ ምረጥ',  
        values=('ደስታ', 'ሐሴት', 'ስሜት ጭንቀት', 'ሰላም'),  
        size_hint=(1, 0.09)  
    )  
    self.layout.add_widget(self.mood_spinner)  

    self.instrument_spinner = Spinner(  
        text='መሣሪያ ምረጥ',  
        values=('ፒያኖ', 'ጊታር', 'ቤስ', 'ድምጽ', 'ሙሉ ኦርኬስትራ'),  
        size_hint=(1, 0.09)  
    )  
    self.layout.add_widget(self.instrument_spinner)  

    self.tempo_spinner = Spinner(  
        text='መጠን ምረጥ',  
        values=('ቀዝቃዛ', 'መካከለኛ', 'ፈጣን'),  
        size_hint=(1, 0.09)  
    )  
    self.layout.add_widget(self.tempo_spinner)  

    self.progress_bar = ProgressBar(max=120, value=0, size_hint=(1, 0.04))  
    self.progress_bar.opacity = 0  
    self.layout.add_widget(self.progress_bar)  

    self.spinner_label = Label(text="", size_hint=(1, 0.07), halign='center')  
    self.layout.add_widget(self.spinner_label)  

    self.generate_button = Button(  
        text="ሙዚቃ ፍጠር", size_hint=(1, 0.10),  
        background_color=(0.2, 0.4, 0.8, 1)  
    )  
    self.generate_button.bind(on_press=self.generate_music)  
    self.layout.add_widget(self.generate_button)  

    self.share_button = Button(  
        text="ሙዚቃ አጋራ", size_hint=(1, 0.10),  
        background_color=(0.6, 0.2, 0.6, 1)  
    )  
    self.share_button.bind(on_press=self.share_music)  
    self.layout.add_widget(self.share_button)  

    self.music_file = None  
    self.sound = None  
    self._elapsed = 0  
    self._progress_event = None  
    return self.layout  

def save_key(self, instance):  
    key = self.api_key_input.text.strip()  
    if not key:  
        self.label.text = "እባክዎ API key ያስገቡ!"  
        return  
    self.store.put('api', key=key)  
    self.saved_key = key  
    self.key_label.text = "🔑 API Key ተቀምጧል ✓"  
    self.label.text = "✓ Key ተቀምጧል! አሁን ሙዚቃ መፍጠር ይችላሉ።"  

def set_label(self, text):  
    Clock.schedule_once(lambda dt: setattr(self.label, 'text', text))  

def set_spinner_label(self, text):  
    Clock.schedule_once(lambda dt: setattr(self.spinner_label, 'text', text))  

def set_buttons_enabled(self, enabled):  
    def _update(dt):  
        self.generate_button.disabled = not enabled  
        self.share_button.disabled = not enabled  
        self.save_key_button.disabled = not enabled  
    Clock.schedule_once(_update)  

def show_loading(self, show):  
    def _update(dt):  
        if show:  
            self.progress_bar.opacity = 1  
            self.progress_bar.value = 0  
            self._elapsed = 0  
            self._progress_event = Clock.schedule_interval(self._tick_progress, 1)  
        else:  
            self.progress_bar.opacity = 0  
            self.progress_bar.value = 0  
            self.spinner_label.text = ""  
            if self._progress_event:  
                self._progress_event.cancel()  
                self._progress_event = None  
    Clock.schedule_once(_update)  

def _tick_progress(self, dt):  
    self._elapsed += 1  
    self.progress_bar.value = min(self._elapsed, 120)  
    self.spinner_label.text = f"በመፍጠር ላይ... {self._elapsed}ሰ"  

def generate_music(self, instance):  
    if not self.saved_key:  
        self.label.text = "እባክዎ አስቀድሞ API Key ያስቀምጡ!"  
        return  
    prompt = self.input_text.text.strip()  
    mood = self.mood_spinner.text  
    instrument = self.instrument_spinner.text  
    tempo = self.tempo_spinner.text  
    if not prompt or mood == 'ሁኔታ ምረጥ' or instrument == 'መሣሪያ ምረጥ' or tempo == 'መጠን ምረጥ':  
        self.label.text = "እባክዎ ሁሉንም አስገባ!"  
        return  
    self.set_buttons_enabled(False)  
    self.set_label("ሙዚቃ በመፍጠር ላይ...")  
    self.show_loading(True)  
    Thread(target=self._do_generate, args=(prompt, mood, instrument, tempo), daemon=True).start()  

def _do_generate(self, prompt, mood, instrument, tempo):  
    key = self.saved_key  
    english_prompt = (  
        f"{MOOD_MAP.get(mood, mood)}, "  
        f"{INSTRUMENT_MAP.get(instrument, instrument)}, "  
        f"{TEMPO_MAP.get(tempo, tempo)}, "  
        f"Ethiopian inspired, {prompt}"  
    )  
    try:  
        r = requests.post(  
            REPLICATE_API_URL,  
            headers={"Authorization": f"Token {key}", "Content-Type": "application/json"},  
            json={  
                "version": "671ac645ce5e552cc63a54a2bbff63fcf798043399427798e4c266d50db2c92f",  
                "input": {  
                    "prompt": english_prompt,  
                    "duration": 15,  
                    "model_version": "large",  
                    "output_format": "mp3",  
                    "normalization_strategy": "peak",  
                }  
            }  
        )  
        prediction = r.json()  
        if "id" not in prediction:  
            self.set_label("API ስህተት። እንደገና ይሞክሩ!")  
            self.show_loading(False)  
            self.set_buttons_enabled(True)  
            return  
        pid = prediction["id"]  
        audio_url = None  
        for _ in range(60):  
            time.sleep(2)  
            poll = requests.get(  
                f"{REPLICATE_API_URL}/{pid}",  
                headers={"Authorization": f"Token {key}"}  
            )  
            result = poll.json()  
            if result["status"] == "succeeded":  
                audio_url = result["output"][0]  
                break  
            elif result["status"] == "failed":  
                self.set_label("ሙዚቃ ፍጠር አልተሳካም!")  
                self.show_loading(False)  
                self.set_buttons_enabled(True)  
                return  
        if not audio_url:  
            self.set_label("ጊዜ አልፏል። እንደገና ይሞክሩ!")  
            self.show_loading(False)  
            self.set_buttons_enabled(True)  
            return  
        self.set_spinner_label("ሙዚቃ በማውረድ ላይ...")  
        audio_data = requests.get(audio_url).content  
        self.music_file = "amharic_music.mp3"  
        with open(self.music_file, "wb") as f:  
            f.write(audio_data)  
        def _play(dt):  
            if self.sound:  
                self.sound.stop()  
            self.sound = SoundLoader.load(self.music_file)  
            if self.sound:  
                self.sound.play()  
        Clock.schedule_once(_play)  
        self.show_loading(False)  
        self.set_label("ሙዚቃ ተፈጥሯል! ✓")  
    except Exception as e:  
        self.set_label(f"ስህተት: {str(e)}")  
        self.show_loading(False)  
    finally:  
        self.set_buttons_enabled(True)  

def share_music(self, instance):  
    if not self.music_file or not os.path.exists(self.music_file):  
        self.label.text = "እባክዎ አስቀድሞ ሙዚቃ ፍጠሩ!"  
        return  
    if not ON_ANDROID:  
        self.label.text = "አጋራ በ Android ላይ ብቻ ይሰራል"  
        return  
    activity = PythonActivity.mActivity  
    file = File(self.music_file)  
    uri = Uri.fromFile(file)  
    intent = Intent()  
    intent.setAction(Intent.ACTION_SEND)  
    intent.setType("audio/mp3")  
    intent.putExtra(Intent.EXTRA_STREAM, uri)  
    activity.startActivity(Intent.createChooser(intent, "ሙዚቃ አጋራ"))

if name == "main":
MusicGeneratorApp().run()
'''

Write to file — do NOT run the code, just save it

with open("/content/musicapp/main.py", "w", encoding="utf-8") as f:
f.write(main_code)

print("✓ main.py written successfully!")
