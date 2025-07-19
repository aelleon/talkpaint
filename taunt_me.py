import subprocess
import cv2
import torch
import time
from openai import OpenAI
from threading import Thread, Event
import os
import pyttsx3
import queue 
import random
import traceback
import logging
import sys
import atexit
import warnings
# from shiftyeyes import start_eyes
warnings.filterwarnings("ignore", category=FutureWarning)
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

# Configuration
CHECK_INTERVAL = 10  # seconds
DISTRACTION_THRESHOLD = 0  # seconds of detected distraction

last_warning_time = 0
cooldown_seconds = 35

# Read API key from environment variable (keep for your other GPT usage if needed)
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    logging.warning("OPENAI_API_KEY environment variable not set — GPT calls won't work.")

client = OpenAI(api_key=api_key) if api_key else None
message_queue = queue.Queue()

# Speaking flag
speaking_event = Event()
mouth_state = "closed"

x_offset = 100
y_offset = 200
mouth_size = (550, 350)

# Load painting and mouth images
painting_base = cv2.imread("./resources/painting.jpg")
mouth_open = cv2.imread("./resources/mouth_open.png", cv2.IMREAD_UNCHANGED)
mouth_closed = cv2.imread("./resources/mouth_closed.png", cv2.IMREAD_UNCHANGED)
mouth_open = cv2.resize(mouth_open, mouth_size)
mouth_closed = cv2.resize(mouth_closed, mouth_size)

# Initialize TTS engine
tts = pyttsx3.init()
tts.setProperty('rate', 180)  # Speed of speech

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
model.eval()

def on_speech_end(name, completed):
    logging.debug("Speech ended.")
    speaking_event.clear()

def message_speaker():
    while True:
        message = message_queue.get()
        if message is None:
            break
        logging.info(f"🗣️ Speaking: {message}")
        Thread(target=speak_message, args=(message,)).start()

def animate_mouth():
    global mouth_state
    while speaking_event.is_set():
        mouth_state = random.choice(["open", "closed"])
        time.sleep(random.uniform(0.01, 0.10))

def overlay_image(background, overlay, position):
    x, y = position
    h, w = overlay.shape[:2]

    alpha_s = overlay[:, :, 3] / 255.0
    alpha_l = 1.0 - alpha_s

    for c in range(3):
        background[y:y+h, x:x+w, c] = (alpha_s * overlay[:, :, c] +
                                       alpha_l * background[y:y+h, x:x+w, c])

def detect_objects(frame):
    results = model(frame)
    detected_classes = results.names
    detections = results.xyxy[0].cpu().numpy()

    detected = set()
    for *box, conf, cls in detections:
        if conf > 0.5:
            detected.add(detected_classes[int(cls)])
    return detected

def generate_ollama_taunt(prompt: str) -> str:
    try:
        # Adjust the command and model name to your setup
        result = subprocess.run(
            ["ollama", "run", "llama3.1:latest", prompt],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            logging.error(f"Ollama error: {result.stderr}")
            return "Hey, come try your luck at the claw machine!"
    except Exception as e:
        logging.error(f"Exception calling Ollama: {e}")
        return "Hey, come try your luck at the claw machine!"

def pick_and_speak_taunt(detected_objects):
    if detected_objects:
        obj_list = ", ".join(detected_objects)
        prompt = (
            f"You are a sassy and fun claw machine at a science fair. "
            f"Taunt the people nearby based on the fact you see these objects: {obj_list}. "
            f"Make it short and catchy to get them to visit the booth. make it only one or two sentences"
        )
    else:
        prompt = (
            "You are a sassy and fun claw machine at a science fair. "
            "Taunt the people nearby to visit the booth even if you see nothing interesting. "
            "Make it short and catchy. make it only one or two sentences"
        )

    taunt = generate_ollama_taunt(prompt)
    message_queue.put(taunt)

def speak_message(message):
    speaking_event.set()
    mouth_thread = Thread(target=animate_mouth)
    mouth_thread.start()
    try:
        logging.debug("🔊 Speaking message...")
        # Using macOS say for best mouth sync
        subprocess.run(["say", message])
        on_speech_end(None, None)
    except Exception as e:
        logging.error(f"TTS error: {e}")
    finally:
        mouth_thread.join()

def process_webcam_feed(cap):
    global last_warning_time

    while True:
        ret, frame = cap.read()
        if not ret:
            logging.warning("Frame grab failed, retrying...")
            time.sleep(1)
            continue

        detected_objects = detect_objects(frame)

        logging.debug(f"Detected objects: {detected_objects}")
        now = time.time()

        # Prioritize 'cell phone' and 'person' detections
        if "cell phone" in detected_objects:
            if now - last_warning_time > cooldown_seconds:
                last_warning_time = now
                logging.info("📱 Phone detected!")
                pick_and_speak_taunt(detected_objects)

        elif "person" in detected_objects:
            if now - last_warning_time > cooldown_seconds:
                last_warning_time = now
                logging.info("👤 Person detected!")
                pick_and_speak_taunt(detected_objects)

        else:
            # Encourage focused visitors occasionally
            if now - last_warning_time > cooldown_seconds * 3:
                last_warning_time = now
                logging.info("✅ No distractions detected.")
                pick_and_speak_taunt(set())

        results = model(frame)
        results.render()
        cv2.imshow("Webcam Object Detection", frame)

        painting_frame = painting_base.copy()
        mouth_frame = mouth_open if mouth_state == "open" else mouth_closed
        overlay_image(painting_frame, mouth_frame, (x_offset, y_offset))
        cv2.imshow("Talking Painting", painting_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def monitor_user():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Could not open webcam.")
        return

    logging.info("📷 Webcam started. Monitoring...")
    process_webcam_feed(cap)

def main():
    logging.info("🎬 Script starting")
    speaker_thread = Thread(target=message_speaker, daemon=False)
    speaker_thread.start()

    # Thread(target=start_eyes, daemon=False).start()
    # shift_eyes_process = subprocess.Popen( 
    #     ["python3", "shift_eyes.py"],
    #     stdout=subprocess.DEVNULL,
    #     stderr=subprocess.DEVNULL
    # )


    iteration = 0
    while True:
        iteration += 1
        logging.info(f"▶️ Starting monitor_user() iteration {iteration}")
        try:
            monitor_user()
            logging.warning("⚠️ monitor_user() returned normally")
        except Exception:
            logging.error("💥 Unhandled exception in monitor_user():\n" + traceback.format_exc())
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
        atexit.register(print, "Exiting Python Script")
    except Exception:
        logging.critical("🔥 Fatal exception in main():\n" + traceback.format_exc())
        sys.exit(1)
    finally:
        logging.info("🏁 Exiting script")