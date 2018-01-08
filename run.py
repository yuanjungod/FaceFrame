import threading
# import libJetson as JT
import socket
import cv2
import face_recognition
import threading
import os

HOST = '192.168.2.19'  # The remote host
PORT = 9999  # The same port as used by the server
face_ready = threading.Event()


def client1(message):
    buy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    buy_socket.connect((HOST, PORT))
    try:
        buy_socket.sendall(message)
    finally:
        buy_socket.close()


def callback(name, id, action):
    result = "%s,%s,%s" % (name, id, action)
    # print "result", result
    # client(buy_socket, result)
    client1(result)


# cls = JT.Classfication()


def finish1():
    HOST = '192.168.2.19'  # The remote host
    PORT = 9999  # The same port as used by the server
    while True:
        print("beginbeginbeginbeginbeginbeginbeginbeginbeginbegin")
        finish_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        finish_sock.connect((HOST, PORT))
        try:
            finish_sock.sendall("complete")
            finish_sock.recv(1024)
            print("finishfinishfinishfinishfinishfinishfinishfinishfinishfinishfinish")
        finally:
            # cls.stop()
            face_ready.set()
            finish_sock.close()


def fun():
    HOST = '192.168.2.19'  # The remote host
    PORT = 9999  # The same port as used by the server
    video_capture = cv2.VideoCapture(0)
    num_jitters = 10
    number_of_times_to_upsample = 1
    # cls.init(callback)
    # Load a sample picture and learn how to recognize it.
    print("encode example")
    face_encoding_list = list()
    face_list = os.listdir("face_images")
    for face in face_list:
        print(face)
        image = face_recognition.load_image_file("face_images/%s" % face)
        face_locations = face_recognition.face_locations(image[:, :, ::-1], number_of_times_to_upsample)
        face_encoding = face_recognition.face_encodings(image, face_locations, num_jitters)[0]
        name = face.split("_")[0]
        user_id = face.split("_")[1]
        face_encoding_list.append([name, user_id, face_encoding])

    print("end example")
    # Initialize some variables
    # face_locations = []
    # face_encodings = []
    # face_names = []
    process_this_frame = True
    face_names = []

    while True:

        print("start")
        if len(face_names) > 0:
            pass
            # face_ready.wait()
        face_names = []
        print("start1")
        # Grab a single frame of video
        ret, frame = video_capture.read()

        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = small_frame[:, :, ::-1]
        face_locations = []
        user_id = -1
        # Only process every other frame of video to save time
        if process_this_frame:
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame, number_of_times_to_upsample)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations, num_jitters)
            print("LKJHGFDSA", len(face_encodings))

            for face_encoding in face_encodings:
                name = "Unknown"
                user_id = -1
                # See if the face is a match for the known face(s)
                current_match_score = 0.35
                match_scores = face_recognition.face_distance([i[2] for i in face_encoding_list], face_encoding)
                for i, match_score in enumerate(match_scores):
                    if match_score < current_match_score:
                        name = face_encoding_list[i][0]
                        user_id = face_encoding_list[i][1]

                # match = face_recognition.compare_faces(
                #     [i[2] for i in face_encoding_list], face_encoding, 0.33)
                #
                # for i in range(len(match)):
                #     if match[i]:
                #         name = face_encoding_list[i][0]
                #         user_id = face_encoding_list[i][1]
                # print("match count:", match.count(True))
                face_names.append(name)
                print(face_names)
        # process_this_frame = not process_this_frame

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
        cv2.waitKey(1)

        if len(face_names) > 0:
            print(user_id)
            try:
                face_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                face_sock.connect((HOST, PORT))
                face_sock.sendall("0,%s,0" % user_id)
                face_ready.clear()
            finally:
                face_sock.close()
                # cls.start()


finish_thread = threading.Thread(target=finish1)
finish_thread.start()

# jt_thread = threading.Thread(target=fun)
# jt_thread.start()
fun()
# finish(finish_sock)
