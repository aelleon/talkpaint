import time
import subprocess
import random

def load_taunts(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

# List of fun or distinct macOS voices
available_voices = [
     #"Jester"
    #"Organ"
    # "Jacques"
    "Daniel"
]

def speak(text):
    voice = random.choice(available_voices)
    print(f"Voice: {voice} | Saying: {text}")
    subprocess.run(['say', '-v', voice, text])

def main():
    taunts = load_taunts('taunts.txt')
    print(f"Loaded {len(taunts)} taunts.")
    
    while True:
        taunt = random.choice(taunts)
        speak(taunt)
        time.sleep(10)

if __name__ == '__main__':
    main()
