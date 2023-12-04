import cv2
import numpy as np
import pafy 

# live stream version
# youtube_url = 'https://www.youtube.com/watch?v=cNJDExqhx5o'
# video = pafy.new(youtube_url).getbest(preftype="mp4")
# cap = cv2.VideoCapture(video.url)

# # Check if the video stream is opened successfully
# if not cap.isOpened():
#     print("Error: Could not open the video stream.")
#     exit()


def update_mask(frame, mask, background, threshold=30):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_background = cv2.cvtColor(background, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(gray_frame, gray_background)

    # create a new mask based on threshold difference
    _, color_mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

    # OR between the current mask and new color_mask to account for stationary people
    updated_mask = cv2.bitwise_or(mask, color_mask)
    return updated_mask

# video version
cap = cv2.VideoCapture("QuadCam-5mins.mp4")

# Snapshot background to compare stationary entities
ret, background = cap.read()

# background subtractor
object_detector = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=40)

total_people = 0

while True: # analyze frame by frame
    ret, frame = cap.read()

    border_points = [(725, 380), (1225, 380), (1800, 1000), (100, 1000)]

    mask = object_detector.apply(frame)

    mask = update_mask(frame, mask, background)
    _, mask = cv2.threshold(mask, 254, 255, cv2.THRESH_BINARY)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
   
    detections = []

    # Part 1: Object Detection and adding object detections to array
    for contour in contours:
        # Calculate area and remove small elements
        area = cv2.contourArea(contour)
        if area > 10:
            x, y, w, h = cv2.boundingRect(contour)
            centroid_x = int(x + w / 2)
            centroid_y = int(y + h / 2)
            # draw object detection
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3) # draw rectangle
            cv2.circle(frame, (centroid_x, centroid_y), 3, (0, 255, 0), -1) # draw circle

    # Part 2: Object tracking that uses detections to track objects    

    # draw on frame
    cv2.polylines(frame, [np.array(border_points)], isClosed=True, color=(0, 0, 255), thickness=3)
    cv2.putText(frame, f'Total People: {0}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Frame", frame)
    cv2.imshow("Mask", mask)

    key = cv2.waitKey(30)

    if key == 27: # pressing esc will exit video capture
        break

cap.release()
cv2.destroyAllWindows()
