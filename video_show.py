import cv2

video_capture = cv2.VideoCapture(1)

while True:
    ret, frame = video_capture.read()

    cv2.imshow("video", frame)
    cv2.waitKey(1)
