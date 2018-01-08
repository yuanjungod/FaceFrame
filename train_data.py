import cv2

video_capture = cv2.VideoCapture(0)

i = 0
while True:
    ret, frame = video_capture.read()
    cv2.imshow("test", frame)
    cv2.waitKey(1)
    if i%10 == 0:
        cv2.imwrite("data/%s.jpg" % i, frame)
    i += 1
