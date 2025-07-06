import cv2
import numpy as np
import threading
import time
import random

# Load and resize mouth images
mouth_open = cv2.imread("resources/mouth_open.png")
mouth_closed = cv2.imread("resources/mouth_closed.png")



mouth_state = "closed"
speaking_event = threading.Event()

def animate_mouth():
    global mouth_state
    while speaking_event.is_set():
        mouth_state = random.choice(["open", "closed"])
        time.sleep(random.uniform(0.1, 0.3))
    mouth_state = "closed"

def speak_simulation():
    speaking_event.set()
    threading.Thread(target=animate_mouth).start()

    # Simulated speaking duration
    print("🔊 Speaking...")
    time.sleep(5)  # Simulate speech duration
    print("✅ Done speaking.")
    speaking_event.clear()

def overlay_mouth(base_frame, x_offset=100, y_offset=100):
    global mouth_state
    mouth_img = mouth_open if mouth_state == "open" else mouth_closed
    h, w, _ = mouth_img.shape
    base_frame[y_offset:y_offset + h, x_offset:x_offset + w] = mouth_img
    return base_frame

# --- Main Loop ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Camera error.")
    exit()

threading.Thread(target=speak_simulation).start()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = overlay_mouth(frame)

    cv2.imshow("Animated Mouth", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()