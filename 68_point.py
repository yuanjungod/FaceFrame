import cv2
import dlib
import numpy
import os


def get_fea_points(rects, im, new_name):
    global landmarks
    feas = []  # 关键点
    fea_file_name = new_name[:-3] + 'pts'  # pts文件名为旋转后图片名称.pts
    fea_file = open('face_images/' + fea_file_name, 'a')  # 新建pts文件
    fea_file.write('version: 1' + '\n' + 'n_points: 68' + '\n' + '{' + '\n')  # 写入文件头部信息
    for i in range(len(rects)):  # 遍历所有检测到的人脸（我的是单个人脸）
        landmarks = numpy.matrix([[p.x, p.y] for p in predictor(im, rects[i]).parts()])
    im = im.copy()
    # 使用enumerate 函数遍历序列中的元素以及它们的下标
    for idx, point in enumerate(landmarks):
        pos = (point[0, 0], point[0, 1])  # 依次保存每个关键点
        feas.append(pos)
        # 在图上画出关键点
        cv2.circle(im, pos, 3, color=(0, 255, 0))
    for pos in feas:
        fea_file.write(str(pos[0]) + ' ' + str(pos[1]) + '\n')  # 写如特征点到pts文件
    fea_file.write('}')  # 写pts文件尾部
    fea_file.close()
    cv2.namedWindow("im", 2)  # 显示标记特征点的图片
    cv2.imshow("im", im)
    cv2.waitKey(1)


PREDICTOR_PATH = 'shape_predictor_68_face_landmarks.dat'  # 关键点提取模型路径
landmarks = []  # 存储人脸关键点
# 1. 定义人脸检测器
detector = dlib.get_frontal_face_detector()

# 2. 载入关键点提取模型
predictor = dlib.shape_predictor(PREDICTOR_PATH)
have_face_img_num = 0  # 统计检测到人脸的图片个数

print('*** Face detection start! ***')
video_capture = cv2.VideoCapture(0)
while True:
    ret, im = video_capture.read()
    rects = detector(im, 1)  # 检测人脸
    if len(rects) >= 1:  # 检测到人脸
        get_fea_points(rects, im, "fufufufufufufufu")  # 调用关键点子程序，见步骤d）
