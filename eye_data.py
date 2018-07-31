# coding=utf-8
import numpy as np
import cv2
import dlib
from scipy.spatial import distance
import os
from imutils import face_utils

# 对应特征点的序号
RIGHT_EYE_START = 37 - 1
RIGHT_EYE_END = 42 - 1
LEFT_EYE_START = 43 - 1
LEFT_EYE_END = 48 - 1
VECTOR_SIZE = 3

pwd = os.getcwd()  # 获取当前路径
model_path = os.path.join(pwd, 'model')  # 模型文件夹路径
shape_detector_path = os.path.join(model_path, 'shape_predictor_68_face_landmarks.dat')  # 人脸特征点检测模型路径

detector = dlib.get_frontal_face_detector()  # 人脸检测器
predictor = dlib.shape_predictor(shape_detector_path)  # 人脸特征点检测器
frame_counter = 0  # 连续帧计数
blink_counter = 0  # 眨眼计数
cap = cv2.VideoCapture(0)


def eye_aspect_ratio(eye):
    # print(eye)
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear


def queue_in(queue, data):
    ret = None
    if len(queue) >= VECTOR_SIZE:
        ret = queue.pop(0)
    queue.append(data)
    return ret, queue


print('Prepare to collect images with your eyes open')
print('Press s to start collecting images.')
print('Press e to end collecting images.')
print('Press q to quit')
flag = 0
txt = open('train_open.txt', 'wb')
data_counter = 0
ear_vector = []
while 1:
    ret, frame = cap.read()
    key = cv2.waitKey(1)
    if key & 0xFF == ord("s"):
        print('Start collecting images.')
        flag = 1
    elif key & 0xFF == ord("e"):
        print('Stop collecting images.')
        flag = 0
    elif key & 0xFF == ord("q"):
        print('quit')
        break

    if flag == 1:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = detector(gray, 0)
        for rect in rects:
            shape = predictor(gray, rect)
            points = face_utils.shape_to_np(shape)  # convert the facial landmark (x, y)-coordinates to a NumPy array
            # points = shape.parts()
            leftEye = points[LEFT_EYE_START:LEFT_EYE_END + 1]
            rightEye = points[RIGHT_EYE_START:RIGHT_EYE_END + 1]
            leftEAR = eye_aspect_ratio(leftEye)
            rightEAR = eye_aspect_ratio(rightEye)
            # print('leftEAR = {0}'.format(leftEAR))
            # print('rightEAR = {0}'.format(rightEAR))

            ear = (leftEAR + rightEAR) / 2.0

            leftEyeHull = cv2.convexHull(leftEye)
            rightEyeHull = cv2.convexHull(rightEye)
            cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

            ret, ear_vector = queue_in(ear_vector, ear)
            if len(ear_vector) == VECTOR_SIZE:
                # print(ear_vector)
                # input_vector = []
                # input_vector.append(ear_vector)

                txt.write(str(ear_vector))
                txt.write('\n')
                data_counter += 1
                print(data_counter)

            cv2.putText(frame, "EAR:{:.2f}".format(ear), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("frame", frame)
txt.close()
