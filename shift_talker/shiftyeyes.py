import cv2
import numpy as np
import threading
import time
import random

# Load different eye directions
eye_imgs = {
    "left": cv2.imread("resources/eye_left.png", cv2.IMREAD_UNCHANGED),
    "center": cv2.imread("resources/eye_center.png", cv2.IMREAD_UNCHANGED),
    "right": cv2.imread("resources/eye_right.png", cv2.IMREAD_UNCHANGED)
}

eye_size = (200, 150)
for key in eye_imgs:
    eye_imgs[key] = cv2.resize(eye_imgs[key], eye_size)

# Initial state
left_eye_pos = [100, 100]
right_eye_pos = [300, 100]
dragging_eye = None
drag_offset = (0, 0)

# Overlay helper
def overlay_image(background, overlay, x, y):
    h, w = overlay.shape[:2]
    if overlay.shape[2] == 4:
        alpha = overlay[:, :, 3] / 255.0
        for c in range(3):
            background[y:y+h, x:x+w, c] = (
                alpha * overlay[:, :, c] +
                (1 - alpha) * background[y:y+h, x:x+w, c]
            )
    return background

# Mouse drag logic
def mouse_callback(event, x, y, flags, param):
    global dragging_eye, drag_offset, left_eye_pos, right_eye_pos

    pad = 20
    if event == cv2.EVENT_LBUTTONDOWN:
        for name, pos in [("left", left_eye_pos), ("right", right_eye_pos)]:
            px, py = pos
            if px - pad <= x <= px + eye_size[0] + pad and py - pad <= y <= py + eye_size[1] + pad:
                dragging_eye = name
                drag_offset = (x - px, y - py)
                break

    elif event == cv2.EVENT_MOUSEMOVE and dragging_eye:
        if dragging_eye == "left":
            left_eye_pos[0] = x - drag_offset[0]
            left_eye_pos[1] = y - drag_offset[1]
        elif dragging_eye == "right":
            right_eye_pos[0] = x - drag_offset[0]
            right_eye_pos[1] = y - drag_offset[1]

    elif event == cv2.EVENT_LBUTTONUP:
        dragging_eye = None

# Eye animation function with random selection
def animate_eyes():
    global eye_state
    while True:
        eye_state = random.choice(["left", "center", "right"])
        time.sleep(0.5)


def start_eyes(): 
    # Setup phase: 10 seconds to drag
    cv2.namedWindow("Eye Animation")
    cv2.setMouseCallback("Eye Animation", mouse_callback)

    # Setup phase
    setup_duration = 19  # seconds
    fps = 30
    delay = int(1000 / fps)

    print("🕹️ Setup: Drag eyes for 10 seconds...")

    start_time = time.time()

    while True:
        frame = np.zeros((350, 840, 3), dtype=np.uint8)

        # Display countdown timer
        remaining_time = int(setup_duration - (time.time() - start_time))
        if remaining_time > 0:
            cv2.putText(frame, f"Setup mode: Drag eyes ({remaining_time}s)", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        overlay_image(frame, eye_imgs["center"], *left_eye_pos)
        overlay_image(frame, eye_imgs["center"], *right_eye_pos)
        cv2.imshow("Eye Animation", frame)

        if time.time() - start_time > setup_duration:
            print("✅ Setup complete. Starting eye animation...")
            break

        if cv2.waitKey(delay) == 27:
            cv2.destroyAllWindows()
            exit()

    # Start eye animation thread
    eye_thread = threading.Thread(target=animate_eyes, daemon=True)
    eye_thread.start()

    # Main loop
    while True:
        frame = np.zeros((350, 840, 3), dtype=np.uint8)
        overlay_image(frame, eye_imgs[eye_state], *left_eye_pos)
        overlay_image(frame, eye_imgs[eye_state], *right_eye_pos)
        cv2.imshow("Eye Animation", frame)
        # print("👁️ Eye state:", eye_state)
        if cv2.waitKey(delay) == 27:
            break

    cv2.destroyAllWindows()


start_eyes()