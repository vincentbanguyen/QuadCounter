# Goals: 
# Counter for how many people walked past alma, hourly bar graph of traffic (Ex: 10 ppl at 1)

import cv2
import pafy  # You may need to install the pafy library using: pip install pafy

# Replace 'YOUR_YOUTUBE_URL' with the actual URL of the livestream
youtube_url = 'https://www.youtube.com/watch?v=FtSlr1Vz0z4'

# Get the video stream using pafy
video = pafy.new(youtube_url).getbest(preftype="mp4")

# OpenCV VideoCapture with the YouTube stream URL
cap = cv2.VideoCapture(video.url)

# Check if the video stream is opened successfully
if not cap.isOpened():
    print("Error: Could not open the video stream.")
    exit()

# Your processing logic goes here
while True:
    ret, frame = cap.read()

    if not ret:
        print("Error: Failed to capture frame.")
        break

    # Your OpenCV processing code here
    # e.g., apply object detection, image processing, etc.

    # Display the frame
    cv2.imshow('YouTube Livestream', frame)

    # Break the loop if 'Esc' key is pressed
    key = cv2.waitKey(1)
    if key == 27:
        break

# Release the VideoCapture and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()
