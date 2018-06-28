import cv2
import face_recognition
import os
import json
import numpy as np


def fun():
    video_capture = cv2.VideoCapture(0)
    num_jitters = 10
    number_of_times_to_upsample = 1
    # cls.init(callback)
    # Load a sample picture and learn how to recognize it.
    print("encode example")
    face_encoding_list = list()
    if os.path.exists("face_encoding_dict.json"):
        with open('face_encoding_dict.json', 'r') as fp:
            face_encoding_dict = json.load(fp)
    else:
        face_encoding_dict = dict()
    face_list = os.listdir("face_images")
    for face in face_list:
        print(face)
        name = face.split("_")[0]
        user_id = face.split("_")[1]
        if user_id in face_encoding_dict:
            face_encoding_list.append([
                face_encoding_dict[user_id]["name"], user_id, np.array(face_encoding_dict[user_id]["face_encoding"])])
        else:
            image = face_recognition.load_image_file("face_images/%s" % face)
            face_locations = face_recognition.face_locations(image, number_of_times_to_upsample)
            face_encoding = face_recognition.face_encodings(image, face_locations, num_jitters)[0]
            face_encoding_list.append([name, user_id, face_encoding])
            face_encoding_dict[user_id] = {
                "name": name,
                "face_encoding": face_encoding.tolist()
            }
    with open('face_encoding_dict.json', 'w') as fp:
        json.dump(face_encoding_dict, fp)

    print("end example")
    process_this_frame = True

    while True:

        print("start")
        face_names = []
        print("start1")
        # Grab a single frame of video
        ret, frame = video_capture.read()
        ret, frame = video_capture.read()

        # Resize frame of video to 1/4 size for faster face recognition processing
        print(frame.shape)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        print(small_frame.shape)
        cv2.imwrite("face_images/yuanjun1_9.jpg", small_frame)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = small_frame[:, :, ::-1]
        face_locations = []
        most_small_distance = 1
        # Only process every other frame of video to save time
        if process_this_frame:
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame, number_of_times_to_upsample)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations, num_jitters)
            print("face count", face_locations)

            for face_encoding in face_encodings:
                name = "Unknown"
                user_id = -1
                # See if the face is a match for the known face(s)
                current_match_score = 0.4
                match_scores = face_recognition.face_distance([i[2] for i in face_encoding_list], face_encoding)
                for i, match_score in enumerate(match_scores):
                    if match_score < current_match_score:
                        current_match_score = match_score
                        name = face_encoding_list[i][0]
                        user_id = face_encoding_list[i][1]
                    if match_score < most_small_distance:
                        most_small_distance = match_score
                print(most_small_distance)

                face_names.append(name)
                print(face_names)

        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
        cv2.imshow("Face", frame)
        cv2.waitKey(20)


fun()
