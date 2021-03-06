import face_recognition
from flask import Flask, jsonify, request, redirect
import time
import os
import cv2
import numpy as np
import random
import hashlib
import json
from lib.mysql import MysqlClient
from lib.aliyun import Aliyun
from config import *
import threading
import re
import os, base64
import cv2

mutex = threading.Lock()


def md5(face_encoding):
    # print(face_str, type(face_str))
    m = hashlib.md5()
    m.update(json.dumps(face_encoding).encode())
    return m.hexdigest()


def base64_to_image(strs):
    try:
        imgdata = base64.b64decode(strs)
        nparr = np.fromstring(imgdata, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return image
    except:
        return None


sql_client = MysqlClient(host='localhost', user='root')
aliyun_oss = Aliyun()


app = Flask(__name__)

face_dict = dict()
num_jitters = 1
number_of_times_to_upsample = 1


mutex.acquire()
max_id = sql_client.select(field="max(id) as max_id", table_name="keruyun.image")[0]["max_id"]
if max_id is None:
    max_id = 0
print(max_id)

feature_dict = dict()

for i in sql_client.select(field="*", table_name="keruyun.image"):
    if i["appid"] not in feature_dict:
        feature_dict[i["appid"]] = dict()
    if i["group_id"] not in feature_dict[i["appid"]]:
        feature_dict[i["appid"]][i["group_id"]] = dict()
    if "uid_list" not in feature_dict[i["appid"]][i["group_id"]]:
        feature_dict[i["appid"]][i["group_id"]]["uid_list"] = list()
    if "image_encoding_list" not in feature_dict[i["appid"]][i["group_id"]]:
        feature_dict[i["appid"]][i["group_id"]]["image_encoding_list"] = list()
    if "image_token_list" not in feature_dict[i["appid"]][i["group_id"]]:
        feature_dict[i["appid"]][i["group_id"]]["image_token_list"] = list()
    feature_dict[i["appid"]][i["group_id"]]["uid_list"].append(i["uid"])
    feature_dict[i["appid"]][i["group_id"]]["image_token_list"].append(i["image_token"])
    feature_dict[i["appid"]][i["group_id"]]["image_encoding_list"].append(json.loads(i["image_encoding"]))
mutex.release()


@app.route('/face_register', methods=['GET', 'POST'])
def face_register():
    mutex.acquire()
    global max_id
    print("max_id: %s" % max_id)
    # update feature_dict from face_encoding table
    user_list = sql_client.select(field="*", table_name="keruyun.image", where="id > %s" % max_id)
    print(user_list)
    for i in user_list:
        # print("***********", i)
        if i["appid"] not in feature_dict:
            feature_dict[i["appid"]] = dict()
        if i["group_id"] not in feature_dict[i["appid"]]:
            feature_dict[i["appid"]][i["group_id"]] = dict()
        if "uid_list" not in feature_dict[i["appid"]][i["group_id"]]:
            feature_dict[i["appid"]][i["group_id"]]["uid_list"] = list()
        if "image_encoding_list" not in feature_dict[i["appid"]][i["group_id"]]:
            feature_dict[i["appid"]][i["group_id"]]["image_encoding_list"] = list()
        if "image_token_list" not in feature_dict[i["appid"]][i["group_id"]]:
            feature_dict[i["appid"]][i["group_id"]]["image_token_list"] = list()

        feature_dict[i["appid"]][i["group_id"]]["uid_list"].append(i["uid"])
        feature_dict[i["appid"]][i["group_id"]]["image_token_list"].append(i["image_token"])
        feature_dict[i["appid"]][i["group_id"]]["image_encoding_list"].append(json.loads(i["image_encoding"]))
        if max_id < i["id"]:
            max_id = i["id"]
    mutex.release()

    start = time.time()
    print("A", os.getpid(), os.getppid())

    base64_image_str = request.values.get("base64_image_str")
    image = None
    if base64_image_str is None or base64_image_str == "":
        try:
            upload_file = request.files['base64_image_str']
            print(upload_file)
            if upload_file:
                image_str = np.asarray(bytearray(upload_file.stream.read()), dtype="uint8")
                image = cv2.imdecode(image_str, cv2.IMREAD_COLOR)
                print("fuck", image.shape)
            else:
                return jsonify({"errorMessage": "need base64_image_str!"})
        except:
            jsonify({"errorMessage": "need base64_image_str!"})
    else:
        image = base64_to_image(base64_image_str)

    appid = request.values.get("appid")
    if appid is None or appid == "":
        return jsonify({"errorMessage": "need appid!"})
    if not re.match("^[A-Za-z0-9_-]*$", appid):
        return jsonify({"errorMessage": "appid contain illegal character"})
    if len(appid) > 20:
        return jsonify({"errorMessage": "appid is too long"})

    group_id = request.values.get("group_id")
    if group_id is None or group_id == "":
        return jsonify({"errorMessage": "need group_id!"})
    if not re.match("^[A-Za-z0-9_-]*$", group_id):
        return jsonify({"errorMessage": "group_id contain illegal character"})
    if len(group_id) > 20:
        return jsonify({"errorMessage": "group_id is too long"})

    uid = request.values.get("uid")
    if uid is None or uid == "":
        return jsonify({"errorMessage": "need uid!"})
    if not re.match("^[A-Za-z0-9_-]*$", uid):
        return jsonify({"errorMessage": "uid contain illegal character"})
    if len(group_id) > 20:
        return jsonify({"errorMessage": "uid is too long"})

    # image = base64_to_image(base64_image_str)
    # image = aliyun_oss.pull_image_from_aliyun("%s/%s/%s/%s" % (appid, group_id, uid, image_name))
    if image is None:
        return jsonify({"errorMessage": "base64_image_str wrong"})
    shape = image.shape
    print(shape)
    if shape[0] > 300:
        radio = (300*1.0)/shape[0]
        # print(int(shape[1]*radio), radio, shape[1])
        image = cv2.resize(image, (int(shape[1]*radio), 300))
        # print(image.shape)
    # print("loading pic", time.time() - start)
    start = time.time()
    face_locations = face_recognition.face_locations(image, number_of_times_to_upsample)
    # print("face_locations", time.time() - start, face_locations)
    if len(face_locations) == 0:
        return jsonify({"errorMessage": "can not find face!!!!"})
    if len(face_locations) > 1:
        return jsonify({"errorMessage": "too many face!!!!"})
    start = time.time()
    face_encoding = face_recognition.face_encodings(image, face_locations, num_jitters)[0]
    # print("face_encoding", time.time() - start)
    token = md5(face_encoding.tolist())

    if appid in feature_dict and group_id in feature_dict[appid] and token in feature_dict[appid][group_id]["image_token_list"]:
        return jsonify({"errorMessage": "same pic repeat register"})
    image_name = "%s-%s-%s.jpg" % (os.getpid(), os.getppid(), time.time())
    aliyun_oss.push_object2aliyun("%s/%s/%s/%s" % (appid, group_id, uid, image_name), image)
    sql_client.insert(table_name="keruyun.image", params={
        "uid": uid, "appid": appid, "group_id": group_id,
        "image_name": image_name, "image_encoding": json.dumps(face_encoding.tolist()),
        "image_token": token
    })
    return jsonify({"face_token": token})


@app.route('/face_detect', methods=['GET', 'POST'])
def face_detect():
    result = dict()
    start = time.time()
    print("A", os.getpid(), os.getppid())

    base64_image_str = request.values.get("base64_image_str")
    image = None
    if base64_image_str is None or base64_image_str == "":
        try:
            upload_file = request.files['base64_image_str']
            print(upload_file)
            if upload_file:
                image_str = np.asarray(bytearray(upload_file.stream.read()), dtype="uint8")
                image = cv2.imdecode(image_str, cv2.IMREAD_COLOR)
                print("fuck", image.shape)
            else:
                return jsonify({"errorMessage": "need base64_image_str!"})
        except:
            jsonify({"errorMessage": "need base64_image_str!"})
    else:
        image = base64_to_image(base64_image_str)

    appid = request.values.get("appid")
    if appid is None or appid == "":
        return jsonify({"errorMessage": "need appid!"})
    if not re.match("^[A-Za-z0-9_-]*$", appid):
        return jsonify({"errorMessage": "appid contain illegal character"})

    if appid not in feature_dict:
        return jsonify({"errorMessage": "appid invalid"})

    # image = aliyun_oss.pull_image_from_aliyun("%s/%s/%s" % (appid, group_id, image_name))
    if image is None:
        return jsonify({"errorMessage": "base64_image_str wrong"})
    shape = image.shape
    print(shape)
    radio = 1
    if shape[0] > 300:
        radio = 300.0 / shape[0]
        image = cv2.resize(image, (int(shape[1] * radio), 300))
        print(image.shape)
    print("loading pic", time.time() - start)
    start = time.time()
    face_locations = face_recognition.face_locations(image, number_of_times_to_upsample)
    print("face_locations", time.time() - start, face_locations)
    result["face_num"] = len(face_locations)
    result["face_list"] = list()
    if len(face_locations) > 0:
        start = time.time()
        face_encoding_list = face_recognition.face_encodings(image, face_locations, num_jitters)
        print("face_encoding", time.time() - start, len(face_encoding_list))
        for i in range(len(face_encoding_list)):

            result["face_list"].append(
                {
                    "face_token": md5(face_encoding_list[i].tolist()),
                    "location":
                    {
                        "top": face_locations[i][0],
                        "right": face_locations[i][1],
                        "bottom": face_locations[i][2],
                        "left": face_locations[i][3],
                    }
                }
            )
        return jsonify(result)
    else:
        return jsonify({"errorMessage": "can not find face!!!"})


@app.route('/face_search', methods=['GET', 'POST'])
def face_search():
    mutex.acquire()
    global max_id
    # update feature_dict from face_encoding table
    user_list = sql_client.select(field="*", table_name="keruyun.image", where="id > %s" % max_id)
    for i in user_list:
        if i["appid"] not in feature_dict:
            feature_dict[i["appid"]] = dict()
        if i["group_id"] not in feature_dict[i["appid"]]:
            feature_dict[i["appid"]][i["group_id"]] = dict()
        if "uid_list" not in feature_dict[i["appid"]][i["group_id"]]:
            feature_dict[i["appid"]][i["group_id"]]["uid_list"] = list()
        if "image_encoding_list" not in feature_dict[i["appid"]][i["group_id"]]:
            feature_dict[i["appid"]][i["group_id"]]["image_encoding_list"] = list()
        if "image_token_list" not in feature_dict[i["appid"]][i["group_id"]]:
            feature_dict[i["appid"]][i["group_id"]]["image_token_list"] = list()

        feature_dict[i["appid"]][i["group_id"]]["uid_list"].append(i["uid"])
        feature_dict[i["appid"]][i["group_id"]]["image_token_list"].append(i["image_token"])
        feature_dict[i["appid"]][i["group_id"]]["image_encoding_list"].append(json.loads(i["image_encoding"]))
        if max_id < i["id"]:
            max_id = i["id"]
    mutex.release()

    start = time.time()
    print("A", os.getpid(), os.getppid())
    base64_image_str = request.values.get("base64_image_str")
    print("as")
    image = None
    if base64_image_str is None or base64_image_str == "":
        try:
            upload_file = request.files['base64_image_str']
            print(upload_file)
            if upload_file:
                image_str = np.asarray(bytearray(upload_file.stream.read()), dtype="uint8")
                image = cv2.imdecode(image_str, cv2.IMREAD_COLOR)
                print("fuck", image.shape)
            else:
                return jsonify({"errorMessage": "need base64_image_str!"})
        except:
            jsonify({"errorMessage": "need base64_image_str!"})

    else:
        image = base64_to_image(base64_image_str)

    appid = request.values.get("appid")
    if appid is None or appid == "":
        return jsonify({"errorMessage": "need appid!"})
    if not re.match("^[A-Za-z0-9_-]*$", appid):
        return jsonify({"errorMessage": "appid contain illegal character"})
    if appid not in feature_dict:
        return jsonify({"errorMessage": "appid invalid"})
    if len(appid) > 20:
        return jsonify({"errorMessage": "appid is too long"})

    # group_id = request.values.get("group_id")
    # if group_id is None or group_id == "":
    #     return jsonify({"errorMessage": "need group_id!"})
    # if not re.match("^[A-Za-z0-9_-]*$", group_id):
    #     return jsonify({"errorMessage": "group_id contain illegal character"})

    search_group_id_list = request.values.get("search_group_id_list")
    if search_group_id_list is None or search_group_id_list == "":
        return jsonify({"errorMessage": "need search_group_id_list!"})
    for search_group_id in search_group_id_list.split(","):
        if not re.match("^[A-Za-z0-9_-]*$", search_group_id):
            return jsonify({"errorMessage": "search_group_id_list contain illegal character"})
        if search_group_id not in feature_dict[appid]:
            return jsonify({"errorMessage": "search_group_id_list invalid"})

    max_user_num = request.values.get("max_user_num")
    if max_user_num is None:
        max_user_num = 5

    if appid not in feature_dict:
        return jsonify({"errorMessage": "appid invalid"})

    # print("face search %s/%s/%s" % (appid, group_id, image_name))

    # image = base64_to_image(base64_image_str)
    # image = aliyun_oss.pull_image_from_aliyun("%s/%s/%s" % (appid, group_id, image_name))
    if image is None:
        return jsonify({"errorMessage": "base64_image_str wrong"})
    shape = image.shape
    print(shape)
    if shape[0] > 300:
        radio = 300.0 / shape[0]
        image = cv2.resize(image, (int(shape[1] * radio), 300))
        print(image.shape)
    print("loading pic", time.time() - start)
    start = time.time()
    face_locations = face_recognition.face_locations(image, number_of_times_to_upsample)
    print("face_locations", time.time() - start, face_locations)
    if len(face_locations) == 0:
        return jsonify({"errorMessage": "can not find face!!!"})
    start = time.time()
    face_encoding = face_recognition.face_encodings(image, face_locations, num_jitters)[0]
    token = md5(face_encoding.tolist())
    print("face_encoding", time.time() - start)

    result_list = dict()
    result_list["face_token"] = token
    result_list["user_list"] = list()
    for search_group_id in search_group_id_list.split(","):
        start = time.time()
        if search_group_id not in feature_dict[appid]:
            continue
        result = np.linalg.norm(np.array(feature_dict[appid][search_group_id]["image_encoding_list"]) - face_encoding, axis=1)
        result = [[result[i], feature_dict[appid][search_group_id]["uid_list"][i]] for i in range(len(result))]
        result = sorted(result, key=lambda a: a[0], reverse=True)
        for i in result[-max_user_num:]:
            result_list["user_list"].append({
                "appid": appid,
                "group_id": search_group_id,
                "user_id": i[1],
                "score": 1-i[0] if 1-i[0] > 0 else 0
            })
        print("compare", time.time() - start)
    return jsonify(result_list)

# if __name__ == "__main__":
#     app.run(host='0.0.0.0', port=5001, processes=3)


