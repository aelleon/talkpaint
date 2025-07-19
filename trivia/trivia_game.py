import pyttsx3
import speech_recognition as sr
import json
import random

# Initialize TTS
engine = pyttsx3.init(driverName='nsss')
engine.setProperty('rate', 150)  # Speed of speech


def speak(text):
    engine.say(text)
    engine.runAndWait()

# Initialize STT
recognizer = sr.Recognizer()
mic = sr.Microphone()

def listen_for_answer():
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("🎤 Listening...")
        audio = recognizer.listen(source, timeout=5)
    try:
        response = recognizer.recognize_google(audio)
        print(f"🗣️ You said: {response}")
        return response.lower()
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that.")
        return ""
    except sr.RequestError:
        speak("Speech recognition service is unavailable.")
        return ""

# Load questions (You can customize this file or use an API)
def load_questions(path="questions.json"):
    with open(path, "r") as file:
        return json.load(file)

def validate_answer(user_answer, correct_answer):
    return user_answer.strip().lower() == correct_answer.strip().lower()

def game_round(question):
    speak(question["question"])
    print(f"\n❓ {question['question']}")
    user_answer = listen_for_answer()
    if validate_answer(user_answer, question["answer"]):
        speak("Correct! 🎉")
        return True
    else:
        speak(f"Wrong! The correct answer was {question['answer']}. 😢")
        return False

def run_game():
    score = 0
    questions = load_questions()
    random.shuffle(questions)

    for q in questions:
        if game_round(q):
            score += 1

    speak(f"Game Over! You scored {score} out of {len(questions)}.")
    print(f"\n🏁 Final Score: {score}/{len(questions)}")

if __name__ == "__main__":
    speak("Welcome to the voice trivia game!")
    run_game()
