import cv2
import numpy as np
import math
import pafy 
from objects import FrameData

# # # live stream version
# youtube_url = 'https://www.youtube.com/watch?v=cNJDExqhx5o'
# video = pafy.new(youtube_url).getbest(preftype="mp4")
# cap = cv2.VideoCapture(video.url)

# # Check if the video stream is opened successfully
# if not cap.isOpened():
#     print("Error: Could not open the video stream.")
#     exit()

cap = cv2.VideoCapture("QuadCam5Min.mp4")

# settings
paused = False
frames_to_advance = 1

# define process area
inner_border_points = [(750, 400), (1200, 400), (1650, 800), (250, 800)]
outer_border_points = [(700, 350), (1250, 350), (1800, 900), (100, 900)]

frame_count = 0

# considered_area_size, movement_threadhold, frame_life, show_detections, detector
# lower var threadhold = less picky selecting foreground
# lower history = less of particle trail
setting0 = [15, 60, 15, True, cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=50)]
setting1 = [15, 60, 15, False, cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=50)]
# setting2 = [15, 60, 15, cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=50)]
settings = [setting0,setting1]

# Snapshot background to compare stationary entities
ret, background = cap.read()

frame_data = [FrameData(),FrameData()]

def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        cursor_position = f'Cursor Position: ({x}, {y})'
        print(cursor_position)

def createFrame(frame, setting, frame_data):
    global frame_count
    global background

    # apply settings
    considered_area_size, movement_threshold, frame_life, show_detections, detector = setting
    
    # retrieve frame data
    objects = frame_data.objects
    object_id = frame_data.object_id
    prev_detections = frame_data.prev_detections

    # get mask
    blurred_frame = cv2.GaussianBlur(frame, (3, 3), 0) # apply gaussian blur to create more blended white blobs. NOTE: adding blur was a big improvement 
    mask = detector.apply(blurred_frame) # create mask using blurred frame
    _, mask = cv2.threshold(mask, 250, 255, cv2.THRESH_BINARY)

    vertices = np.array([[0, 540],[0, 0],[1920,0],[1920, 475],[1320, 160], [665, 160]])
    cv2.drawContours(mask, [vertices], 0, (0), thickness=cv2.FILLED)

    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Part 1: Object Detection and adding object detections to array

    curr_detections = []
    for contour in contours:
        # Calculate area and remove small elements
        contour_area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        
        center_x = int(x + w / 2)
        center_y = int(y + h / 2)
        # address people on top of window vs bottom scaling and who to consider as object
        scaled_considered_area_size = considered_area_size * (1/(frame.shape[0]**2))*(center_y**2)  # scaled_considered_area_size based on y, smaller y = smaller scaled_considered_area_size
        # scaled_considered_area_size = considered_area_size * y / frame.shape[0]  # scaled_considered_area_size based on y, smaller y = smaller scaled_considered_area_size
    

        if contour_area > scaled_considered_area_size: # if big enough to consider
            if show_detections:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 1)
                cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)
            curr_detections.append((center_x,center_y))
    
    # at start of program, compare prev frame to curr frame . will identify all initial objects on the screen.
    if frame_count <= 2:
        for curr in curr_detections:
            for prev in prev_detections:
                distance = math.hypot(prev[0]-curr[0],prev[1]-curr[1])
                # if distance between detections less than threshold, register this object
                # if distance < movement_threshold * (1/(frame.shape[0]**2))*(curr[1]**2): # account for y scaling
                if distance < movement_threshold * curr[1] / frame.shape[0]: # account for y scaling
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
                    # if distance < movement_threshold * (1/(frame.shape[0]**2))*(curr_detection[1]**2): # account for y scaling
                    if distance < movement_threshold * curr_detection[1] / frame.shape[0]: # account for y scaling
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
        if show_detections:
            cv2.circle(frame, object[0], 5, (0, 0, 255), -1)
        # cv2.putText(frame, str(id), (object[0][0], object[0][1] - 7), 0, 1, (0, 0, 255), 2)

    # draw on frame
    cv2.polylines(frame, [np.array(vertices)], isClosed=True, color=(0, 0, 255), thickness=3)
    cv2.putText(frame, f'Total People: {int(len(objects))}', (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 10)
    
    prev_detections = curr_detections.copy()

    # update frame data
    frame_data.objects = objects
    frame_data.object_id = object_id
    frame_data.prev_detections = prev_detections

    return frame, mask

def processFrame(frame_data):
    global frame_count
    frame_count+=1
    _, captured_frame = cap.read()
    
    for index in range(len(settings)):
        processed_frame, processed_mask = createFrame(captured_frame.copy(), settings[index], frame_data[index])
        cv2.imshow("Frame " + str(index), processed_frame)
        cv2.imshow("Mask " + str(index), processed_mask)
        # cv2.setMouseCallback("Frame and Mask " + str(index), mouse_callback)

while True: # analyze frame by frame
    if paused == False:
        processFrame(frame_data)
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
            processFrame(frame_data)
    
cap.release()
cv2.destroyAllWindows()
