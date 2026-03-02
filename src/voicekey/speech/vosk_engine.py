import json
import queue
import threading
import sounddevice as sd
from vosk import Model, KaldiRecognizer


class VoskEngine:
    def __init__(self, model_path, grammar=None):
        self.model = Model(model_path)
        self.grammar = grammar
        self.recognizer = self._build_recognizer()
        self.queue = queue.Queue()
        self._stop = threading.Event()

    def _build_recognizer(self):
        if self.grammar:
            return KaldiRecognizer(
                self.model,
                16000,
                json.dumps(self.grammar)
            )
        return KaldiRecognizer(self.model, 16000)

    def start(self, callback):
        def audio_callback(indata, frames, time, status):
            if status:
                print(status)
            self.queue.put(bytes(indata))

        def run():
            with sd.RawInputStream(
                samplerate=16000,
                blocksize=8000,
                dtype="int16",
                channels=1,
                callback=audio_callback,
            ):
                print("[voicekey] Listening...")
                while not self._stop.is_set():
                    data = self.queue.get()
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get("text", "")
                        if text:
                            callback(text)

        threading.Thread(target=run, daemon=True).start()

    def stop(self):
        self._stop.set()