import ollama
import subprocess
from vosk import Model, KaldiRecognizer
import pyaudio
import json

# Load the Vosk model at startup so it's ready when needed
vosk_model = Model("vosk-model-en-us-0.22")

def recognize_speech():
    """
    Captures audio from the microphone and returns the recognized text using Vosk.
    """
    rec = KaldiRecognizer(vosk_model, 16000)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
    stream.start_stream()

    print("Listening... (speak now)")
    while True:
        data = stream.read(4000)
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result['text']
            if text.strip():
                print(f"You (speech): {text}")
                stream.stop_stream()
                stream.close()
                p.terminate()
                return text

def interactive_chat(model_name="llama3"):
    messages = []
    # Add the system message to define the model's persona
    system_prompt = "You are a trivia host. Please ask the user what topic they would like trivia about, then generate an easy question based on that topic that has a short answer, then evaluate their response leniently to determine if they are correct or not. The user will speak their answer, so don't mention anything about typing. Also only respond with the text and do not include any additional instructions or explanations. Ask a total of 10 questions. Don't reply with if they were correct or not until the end. Give them a total score out of 10"
    messages.append({'role': 'system', 'content': system_prompt})
    print(f"System: {system_prompt}")

    # Initial prompt to the model to start the trivia game
    initial_user_message = "Start the trivia game by asking me for a topic."
    messages.append({'role': 'user', 'content': initial_user_message})

    print("AI: ", end="", flush=True)
    initial_ai_response_content = ""
    try:
        # Get the AI's initial response (asking for a topic)
        for chunk in ollama.chat(model=model_name, messages=messages, stream=True):
            if chunk['message']['content']:
                print(chunk['message']['content'], end="", flush=True)
                initial_ai_response_content += chunk['message']['content']
        print("\n") # New line after AI's initial response
        subprocess.call(['say', initial_ai_response_content])
        messages.append({'role': 'assistant', 'content': initial_ai_response_content})
    except ollama.ResponseError as e:
        print(f"\nError during initial chat setup: {e.error}")
        if e.status_code == 404:
            print(f"Model '{model_name}' not found. Please run 'ollama pull {model_name}' first.")
        return # Exit if initial setup fails
    except Exception as e:
        print(f"\nAn unexpected error occurred during initial chat setup: {e}")
        return # Exit if initial setup fails

    while True:
        print("Speak your answer, or type 'quit'/'exit' to leave, or 'reset' to restart.")
        user_input = recognize_speech()

        if user_input.lower() in ["quit", "exit"]:
            print("Exiting chat. Goodbye!")
            break
        elif user_input.lower() == "reset":
            messages = [{'role': 'system', 'content': system_prompt}] # Reset to just the system prompt
            print("Conversation history cleared.")
            continue

        messages.append({'role': 'user', 'content': user_input})

        print("AI: ", end="", flush=True)
        current_response_content = ""
        try:
            for chunk in ollama.chat(model=model_name, messages=messages, stream=True):
                if chunk['message']['content']:
                    print(chunk['message']['content'], end="", flush=True)
                    current_response_content += chunk['message']['content']
            print("\n") # New line after AI's response
            subprocess.call(['say', current_response_content])
            messages.append({'role': 'assistant', 'content': current_response_content})
        except ollama.ResponseError as e:
            print(f"\nError: {e.error}")
            if e.status_code == 404:
                print(f"Model '{model_name}' not found. Please run 'ollama pull {model_name}' first.")
            # Remove the last user message if there was an error, so it doesn't pollute history
            messages.pop()
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
            messages.pop() # Remove the last user message

if __name__ == "__main__":
    # You can change 'llama3' to any other model you have pulled (e.g., 'mistral', 'codellama', 'phi')
    MODEL_TO_USE = "gemma3:latest"
    interactive_chat(MODEL_TO_USE)