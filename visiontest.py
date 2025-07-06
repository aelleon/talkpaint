
import cv2
import torch
# from yolov5 import YOLOv5

# Load YOLOv5 model (use the local path to your .pt file)
model_path = 'yolov5s.pt'  # Make sure to replace with the correct path if needed
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')  # Load YOLOv5 model architecture

# Start video capture (webcam)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

while True:
    # Capture frame-by-frame from webcam
    ret, frame = cap.read()

    if not ret:
        print("Error: Failed to capture image.")
        break

    # Perform object detection on the frame using YOLOv5
    results = model(frame)

    # Render results
    results.render()  # Draw boxes and labels on the frame

    # Display the resulting frame
    cv2.imshow("Webcam Object Detection", frame)

    # Check for exit key (press 'q' to quit)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close the window
cap.release()
cv2.destroyAllWindows()
