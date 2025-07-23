import numpy as np
import cv2
import mediapipe as mp
import time
import random
import os
from arduino_setup import win, command

def play_cham_cham_cham():
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        min_detection_confidence=0.5, min_tracking_confidence=0.5
    )
    mp_drawing = mp.solutions.drawing_utils
    drawing_spec = mp_drawing.DrawingSpec(color=(128, 0, 128), thickness=2, circle_radius=1)
    cap = cv2.VideoCapture(0)

    directions = ["Up", "Down", "Left", "Right"]
    hand_images = ["hands/up.png", "hands/down.png", "hands/left.png", "hands/right.png"]
    forbidden_direction = None
    game_state = "waiting"  # waiting, countdown, playing, result
    countdown_start = None
    result_time = None
    result_direction = "Forward"
    result_text = ""
    face_detected = False
    last_detected_direction = "Forward"
    consecutive_correct = 0
    win_message_time = None
    timer = 4
    lives = 3

    override_direction = None

    hand_image = cv2.imread("hands/down.png")
    cv2.imshow("Hand Image", hand_image)


    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break

        image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = face_mesh.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        img_h, img_w, img_c = image.shape

        face_2d = []
        face_3d = []
        detected_direction = last_detected_direction

        cv2.putText(
            image, f"Lives: {lives}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4
        )
        cv2.putText(
            image, f"Correct: {consecutive_correct}", (1300, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4
        )
        cv2.putText(image, "Detected: " + str(detected_direction), (1300, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2)
        cv2.putText(image, "Override: " + str(override_direction), (1300, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 2)

        if results.multi_face_landmarks:
            face_detected = True
            for face_landmarks in results.multi_face_landmarks:
                for idx, lm in enumerate(face_landmarks.landmark):
                    if idx in [33, 263, 1, 61, 291, 199]:
                        if idx == 1:
                            nose_2d = (lm.x * img_w, lm.y * img_h)
                            nose_3d = (lm.x * img_w, lm.y * img_h, lm.z * 3000)
                        x, y = int(lm.x * img_w), int(lm.y * img_h)
                        face_2d.append([x, y])
                        face_3d.append([x, y, lm.z])

                face_2d = np.array(face_2d, dtype=np.float64)
                face_3d = np.array(face_3d, dtype=np.float64)
                focal_length = 1 * img_w
                cam_matrix = np.array(
                    [[focal_length, 0, img_h / 2], [0, focal_length, img_w / 2], [0, 0, 1]]
                )
                distortion_matrix = np.zeros((4, 1), dtype=np.float64)
                _, rotation_vec, translation_vec = cv2.solvePnP(
                    face_3d, face_2d, cam_matrix, distortion_matrix
                )
                rmat, _ = cv2.Rodrigues(rotation_vec)
                angles, *_ = cv2.RQDecomp3x3(rmat)
                x_angle = angles[0] * 360
                y_angle = angles[1] * 360
                z_angle = angles[2] * 360

                if y_angle < -3:
                    detected_direction = "Left"
                elif y_angle > 3:
                    detected_direction = "Right"
                elif x_angle < -1:
                    detected_direction = "Down"
                elif x_angle > 3:
                    detected_direction = "Up"
                else:
                    detected_direction = "Forward"

                last_detected_direction = detected_direction

                p1 = (int(nose_2d[0]), int(nose_2d[1]))
                p2 = (int(nose_2d[0] + y_angle * 10), int(nose_2d[1] - x_angle * 10))
                cv2.line(image, p1, p2, (255, 0, 0), 3)
                mp_drawing.draw_landmarks(
                    image=image,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=drawing_spec,
                    connection_drawing_spec=drawing_spec,
                )
        else:
            face_detected = False
            # Do not reset game state or forbidden_direction here

        # Game logic
        if win_message_time is not None:
            cv2.putText(
                image,
                "You won! 5 in a row!",
                (20, 300),
                cv2.FONT_HERSHEY_SIMPLEX,
                2,
                (0, 255, 0),
                4,
            )
            # if time.time() - win_message_time > 3:
            #     game_state = "waiting"
            #     forbidden_direction = None
            #     countdown_start = None
            #     result_text = ""
            #     consecutive_correct = 0
            #     win_message_time = None
            cv2.imshow("Head Pose Game", image)
            if cv2.waitKey(5) & 0xFF == 32:
                game_state = "waiting"
                lives = 3
                win_message_time = None
                consecutive_correct = 0
            continue

        if game_state == "waiting":
            countdown_start = time.time()
            if face_detected:
                game_state = "countdown"
        elif game_state == "countdown":
            elapsed = int(time.time() - countdown_start)
            countdown = 3 - elapsed
            if countdown > 0:
                cv2.putText(
                    image,
                    f"Starting in {countdown}",
                    (20, 100),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2,
                    (0, 255, 255),
                    3,
                )
                if countdown == timer - 1:
                    os.system("afplay /System/Library/Sounds/Frog.aiff &")
                    timer -= 1
            else:
                forbidden_direction = random.choice(directions)
                game_state = "playing"

        elif game_state == "playing":
            timer = 4
            # Show the correct hand image for the forbidden direction
            if forbidden_direction in directions:
                idx = directions.index(forbidden_direction)
                hand_image = cv2.imread(hand_images[idx])
                cv2.imshow("Hand Image", hand_image)

            if override_direction is not None:
                detected_direction = override_direction
                override_direction = None

            if detected_direction == forbidden_direction or detected_direction == "Forward":
                os.system("afplay /System/Library/Sounds/Sosumi.aiff &")
                result_text = "Wrong!"
                color = (0, 0, 255)
                lives -= 1
            else:
                os.system("afplay /System/Library/Sounds/Glass.aiff &")
                result_text = "Correct!"
                color = (0, 255, 0)
                consecutive_correct += 1
            result_time = time.time()
            result_direction = detected_direction
            game_state = "result"
        elif game_state == "result":
            override_direction = None
            cv2.putText(
                image, result_text, (20, 300), cv2.FONT_HERSHEY_SIMPLEX, 2, color, 4
            )
            cv2.putText(
                image,
                f"Forbidden Direction: {forbidden_direction}",
                (20, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                2,
                color,
                4,
            )
            cv2.putText(
                image,
                f"Detected Direction: {result_direction}",
                (20, 210),
                cv2.FONT_HERSHEY_SIMPLEX,
                2,
                color,
                4,
            )
            # cv2.putText(image, f"Score: {consecutive_correct}/5", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,255,0), 2)
            if consecutive_correct >= 5:
                win_message_time = time.time()
                os.system("afplay ./win.wav &")
                win()

            elif lives > 0 and time.time() - result_time > 2:
                game_state = "waiting"
                forbidden_direction = None
                countdown_start = None
                result_text = ""

        cv2.imshow("Head Pose Game", image)

        # if cv2.waitKey(5) & 0xFF == 32:
        key = cv2.waitKey(5)
        if key == 32:
            game_state = "waiting"
            lives = 3
            consecutive_correct = 0
            timer = 4
            override_direction = None
        elif key == ord('w'):
            os.system("afplay ./win.wav &")
            win()
        elif key >= 0 and key <= 3:
            override_direction = directions[key]
    cap.release()

if __name__ == "__main__":
    play_cham_cham_cham()