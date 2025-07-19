from vosk import Model, KaldiRecognizer
import pyaudio
import json

model = Model("vosk-model-en-us-0.22")
rec = KaldiRecognizer(model, 16000)
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
stream.start_stream()

while True:
    data = stream.read(4000)
    if rec.AcceptWaveform(data):
        result = json.loads(rec.Result())
        print(result['text'])
