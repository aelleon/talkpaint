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
warnings.filterwarnings("ignore", category=FutureWarning)
logging.basicConfig(
    level=logging.DEBUG,  # or DEBUG if you want more detail
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]  # Sends logs to terminal
)
# Configuration
CHECK_INTERVAL = 10  # seconds
DISTRACTION_THRESHOLD = 0  # seconds of detected distraction

last_warning_time = 0
cooldown_seconds = 35

# Read API key from environment variable
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")


client = OpenAI(api_key= api_key)
message_queue = queue.Queue()

# New: Speaking flag
speaking_event = Event()
mouth_state = "closed"  # Initial state of the mouth

# Coordinates where mouth overlay should go on the painting
x_offset = 100  # Horizontal position
y_offset = 200  # Vertical position

mouth_size  = (550, 350)  # Size of the mouth images
# Load painting and mouth images
painting_base = cv2.imread("./resources/painting.jpg")  # Your base painting
mouth_open = cv2.imread("./resources/mouth_open.png", cv2.IMREAD_UNCHANGED)  # With transparency
mouth_closed = cv2.imread("./resources/mouth_closed.png", cv2.IMREAD_UNCHANGED)

mouth_open = cv2.resize(mouth_open, mouth_size)
mouth_closed = cv2.resize(mouth_closed, mouth_size)

# --- Initialize text-to-speech engine ---
tts = pyttsx3.init()
tts.setProperty('rate', 180)  # speed of speech

# --- Load the pre-trained model for activity classification ---
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')  # Load YOLOv5 model architecture

model.eval()  # Set the model to evaluation mode


# State
last_focus_time = time.time()
distraction_detected = False

def on_speech_end(name, completed):
    print("Speech ended.")
    speaking_event.clear()

def message_speaker():
    while True:
        message = message_queue.get()
        if message is None:
            break  # Optional way to exit cleanly
        print("🗣️ Got message:", message)
        Thread(target=speak_message, args=(message,)).start()
        # speak_message(message)


def animate_mouth():
    global mouth_state
    while speaking_event.is_set():
        print("Animating mouth...")
        mouth_state = random.choice(["open", "closed"])
        time.sleep(random.uniform(0.01, 0.10))  # Random delay between 0.1 and 0.3 seconds

# New: Overlay function
def overlay_image(background, overlay, position):
    x, y = position
    h, w = overlay.shape[:2]

    alpha_s = overlay[:, :, 3] / 255.0
    alpha_l = 1.0 - alpha_s

    for c in range(3):  # RGB
        background[y:y+h, x:x+w, c] = (alpha_s * overlay[:, :, c] +
                                       alpha_l * background[y:y+h, x:x+w, c])
                                       

# Simulate activity classification
def is_user_distracted(frame):
    # Perform YOLO object detection
    results = model(frame)

    # Parse detection results
    detected_classes = results.names
    detections = results.xyxy[0].cpu().numpy()

    for *box, conf, cls in detections:
        if detected_classes[int(cls)] == 'cell phone' and conf > 0.5:  # Check for phones
            return True
    return False

def speak_message(message):
    speaking_event.set()  # Set speaking event
    mouth_thread = Thread(target=animate_mouth)  # Start mouth animation thread
    mouth_thread.start()
    try:
        print("🔊 Speaking message...")
        tts.connect('finished-utterance', on_speech_end)  # Connect to the event
        # speaking_event.clear()

        # tts.say(message)
        # tts.runAndWait()
        subprocess.run(["say", message])
        on_speech_end(None, None)  # Call the end function manually


    except Exception as e:
        print("TTS error:", e)
        # Thread(target=tts.runAndWait).start()
    finally:
        mouth_thread.join()  # Ensure mouth animation thread ends
        
    

# Get GPT message
def get_gpt_message():
    print("Sending prompt to ChatGPT:")
    response = client.responses.create(
        model="gpt-4.1",
        input = "You are a wise animated painting that helps people stay on task. Send a quick quip  to the user to help them refocus, but make it really mean and condescending. Like really really mean. add a curse word here and there",
    )
    message_queue.put(response.output_text)
    # message_queue.put("i love you test ttest ttest ttest ttest ttest test ")
    print("Received response from ChatGPT.")

# --- Function to process the webcam feed ---
def process_webcam_feed(cap):
    global last_focus_time, distraction_detected, last_warning_time

    while True:
        ret, frame = cap.read()
        if not ret:
            print("frame failed, retry")
            time.sleep(1)
            continue
            break

        # Check for phone distraction in the current frame
        distraction_detected = is_user_distracted(frame)
        # distraction_detected = True  # For testing purposes
        if distraction_detected:
            if time.time() - last_warning_time > cooldown_seconds:
                last_warning_time = time.time()
                print("📱 Phone detected!")
                # if time.time() - last_focus_time > DISTRACTION_THRESHOLD:
                print("❗ Distraction detected! Starting thread...")
                Thread(target=get_gpt_message).start()
            else: 
                print("📱 Phone detected, but thread paused")

        else:
            print("✅ User is focused.")
            last_focus_time = time.time()
            distraction_detected = False

        # Render detection results on the frame
        results = model(frame)  # Get detection results again for rendering
        results.render()  # This modifies the image in-place with bounding boxes

        # try: 
        #     while not message_queue.empty():
        #         # message = message_queue.get()
        #         # print("Message from ChatGPT:", message)
        #         # Thread(target=speak_message, args=(message,)).start()
        # except Exception as e:
        #     print("Error processing message queue:", e)

        cv2.imshow("Webcam Object Detection", frame)

        # Display the resulting frame
        painting_frame = painting_base.copy()
        mouth_frame = mouth_open if mouth_state== "open" else mouth_closed
        print("mouth state:", mouth_state)
        overlay_image(painting_frame, mouth_frame, (x_offset, y_offset))

        cv2.imshow("Talking Painting", painting_frame)

        # Check for exit key (press 'q' to quit)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# --- Main loop to monitor webcam ---
def monitor_user():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print("📷 Webcam started. Monitoring...")

    # Start webcam feed processing in the main thread
    process_webcam_feed(cap)


def main():
    logging.info("🎬  Script starting")
    speaker_thread = Thread(target=message_speaker, daemon=False)
    speaker_thread.start()

    iteration = 0
    while True:
        iteration += 1
        logging.info(f"▶️  Starting monitor_user() iteration {iteration}")
        try:
            monitor_user()
            logging.warning("⚠️  monitor_user() returned normally")
        except Exception:
            logging.error("💥 Unhandled exception in monitor_user():\n" +
                          traceback.format_exc())
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
        atexit.register(print, "Exiting Python Script") 

    except Exception:
        logging.critical("🔥 Fatal exception in main():\n" + traceback.format_exc())
        sys.exit(1)
    finally:
        logging.info("🏁  Exiting script")