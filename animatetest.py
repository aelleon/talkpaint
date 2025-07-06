import cv2
import subprocess
import threading
import time

# Load images from resources directory
mouth_open = cv2.imread("resources/mouth_open.png", cv2.IMREAD_UNCHANGED)
mouth_closed = cv2.imread("resources/mouth_closed.png", cv2.IMREAD_UNCHANGED)

# Resize images
mouth_open = cv2.resize(mouth_open, (100, 60))
mouth_closed = cv2.resize(mouth_closed, (100, 60))

# Shared state
mouth_state = {"open": False}

def draw_mouth_image(frame, mouth_img):
    y_offset, x_offset = 300, 270
    y1, y2 = y_offset, y_offset + mouth_img.shape[0]
    x1, x2 = x_offset, x_offset + mouth_img.shape[1]

    alpha_m = mouth_img[:, :, 3] / 255.0
    alpha_f = 1.0 - alpha_m

    for c in range(3):
        frame[y1:y2, x1:x2, c] = (alpha_m * mouth_img[:, :, c] +
                                  alpha_f * frame[y1:y2, x1:x2, c])

def speak_and_animate(text):
    print("🗣️ Speaking (via 'say'):", text)
    mouth_state["open"] = True
    subprocess.run(["say", text])
    mouth_state["open"] = False
    print("✅ Speech done")

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open webcam.")
        return

    # Start speech thread
    threading.Thread(target=lambda: (time.sleep(1), speak_and_animate("Hello! Testing mouth overlay.")), daemon=True).start()

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.resize(frame, (640, 480))

        # Draw the appropriate mouth image
        if mouth_state["open"]:
            draw_mouth_image(frame, mouth_open)
        else:
            draw_mouth_image(frame, mouth_closed)

        cv2.imshow("Talking Head", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("👋 Quit requested")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
