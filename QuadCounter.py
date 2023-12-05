import cv2
import numpy as np
import math
import pafy 

# # live stream version
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

cap = cv2.VideoCapture("QuadCam5Min.mp4")

# settings
paused = False
frames_to_advance = 1
movement_threshold = 30
frame_life = 30
inner_border_points = [(750, 400), (1200, 400), (1650, 800), (250, 800)]
outer_border_points = [(700, 350), (1250, 350), (1800, 900), (100, 900)]

# Snapshot background to compare stationary entities
ret, background = cap.read()

# background subtractor
object_detector = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=40)

# tracking variables
objects = {}
object_id = 0 # start counter at 0, will increment for new objects
total_people = 0
frame_count = 0
prev_detections = []

def processFrame():

    global objects
    global object_id
    global total_people
    global frame_count
    global prev_detections
    global frame_life

    frame_count+=1
    ret, frame = cap.read()

    mask = object_detector.apply(frame)
    mask = update_mask(frame, mask, background) # account stationary people
    _, mask = cv2.threshold(mask, 254, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    curr_detections = []

    # Part 1: Object Detection and adding object detections to array
    for contour in contours:
        # Calculate area and remove small elements
        area = cv2.contourArea(contour)
        if area > 30:
            x, y, w, h = cv2.boundingRect(contour)
            center_x = int(x + w / 2)
            center_y = int(y + h / 2)
            curr_detections.append((center_x,center_y))

            # draw object detection
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3) # draw rectangle
            cv2.circle(frame, (center_x, center_y), 3, (0, 255, 0), -1) # draw circle
    
    # at start of program, compare prev frame to curr frame . will identify all initial objects on the screen.
    if frame_count <= 2:
        for curr in curr_detections:
            for prev in prev_detections:
                distance = math.hypot(prev[0]-curr[0],prev[1]-curr[1])
                # if distance between detections less than threshold, register this object
                if distance < movement_threshold:
                    objects[object_id] = [curr, frame_life]
                    object_id +=1
    else: # rest of program will compare prev objects with current objects to see if it still exists. if not, we remove it.
        objects_copy = objects.copy()
        curr_detections_copy = curr_detections.copy()
        for curr_object_id, curr_object in objects_copy.items(): # iterate through objects
            exists = False
            for curr_detection in curr_detections_copy: # iterate through detections
                if curr_detection in curr_detections:
                    distance = math.hypot(curr_object[0][0]-curr_detection[0],curr_object[0][1]-curr_detection[1])
                    # if distance between detections less than thrashold, than remove that extra detection since it's the same object.
                    if distance < movement_threshold:
                        exists = True
                        objects[curr_object_id] = [curr_detection, frame_life] # update object id to current position
                        curr_detections.remove(curr_detection) # remove old position from detection array
                        continue
            if not exists: # if prev not found in curr, we decremetn it's frame lifespan. if it hits 0, remove it from objects list.
                objects[curr_object_id][1] -= 1
                if objects[curr_object_id][1] == 0:
                    objects.pop(curr_object_id)

    # register new objects detected
    for curr_detection in curr_detections:
        objects[object_id] = [curr_detection, frame_life]
        object_id +=1

    for id, object in objects.items():
        cv2.circle(frame, object[0], 5, (0, 0, 255), -1)
        cv2.putText(frame, str(id), (object[0][0], object[0][1] - 7), 0, 1, (0, 0, 255), 2)

    # draw on frame
    cv2.polylines(frame, [np.array(outer_border_points)], isClosed=True, color=(0, 0, 255), thickness=3)
    cv2.polylines(frame, [np.array(inner_border_points)], isClosed=True, color=(0, 0, 255), thickness=3)
    # cv2.putText(frame, f'Total People: {int(track_id)}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Frame", frame)
    cv2.imshow("Mask", mask)

    prev_detections = curr_detections.copy()

while True: # analyze frame by frame
    if paused == False:
        processFrame()

    key = cv2.waitKey(1)
    if key == 27:  # esc = break loop
        break
    elif key == ord('p'):  # p = play
        paused = not paused
    elif key == ord('a'):  # a = advance
        for _ in range(frames_to_advance):
            ret, frame = cap.read()
            if not ret:
                break
            processFrame()
    
cap.release()
cv2.destroyAllWindows()
