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


def md5(face_encoding):
    # print(face_str, type(face_str))
    m = hashlib.md5()
    m.update(json.dumps(face_encoding).encode())
    return m.hexdigest()


sql_client = MysqlClient(host='localhost', user='root')
aliyun_oss = Aliyun(account_info)


app = Flask(__name__)

face_dict = dict()
num_jitters = 1
number_of_times_to_upsample = 1

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


@app.route('/face_register', methods=['GET', 'POST'])
def face_register():
    global max_id
    # update feature_dict from face_encoding table
    for i in sql_client.select(field="*", table_name="keruyun.image", where="id > %s" % max_id):
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
    max_id = sql_client.select(field="max(id) as max_id", table_name="keruyun.image")[0]["max_id"]
    if max_id is None:
        max_id = 0

    start = time.time()
    print("A", os.getpid(), os.getppid())
    image_name = request.values.get("image_name")
    appid = request.values.get("appid")
    group_id = request.values.get("group_id")
    uid = request.values.get("uid")
    image = aliyun_oss.pull_image_from_aliyun("%s/%s/%s/%s" % (appid, group_id, uid, image_name))
    if image is None:
        return jsonify({})
    shape = image.shape
    print(shape)
    if shape[0] > 300:
        radio = (300*1.0)/shape[0]
        print(int(shape[1]*radio), radio, shape[1])
        image = cv2.resize(image, (int(shape[1]*radio), 300))
        print(image.shape)
    print("loading pic", time.time() - start)
    start = time.time()
    face_locations = face_recognition.face_locations(image, number_of_times_to_upsample)
    print("face_locations", time.time() - start, face_locations)
    if len(face_locations) != 1:
        return jsonify({})
    start = time.time()
    face_encoding = face_recognition.face_encodings(image, face_locations, num_jitters)[0]
    print("face_encoding", time.time() - start)
    token = md5(face_encoding.tolist())

    if appid in feature_dict and group_id in feature_dict[appid] and token in feature_dict[appid][group_id]["image_token_list"]:
        return jsonify({})

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

    image_name = request.values.get("image_name")
    if image_name is None:
        return jsonify({"error": "need image_name!"})
    appid = request.values.get("appid")
    if appid is None:
        return jsonify({"error": "need appid!"})

    group_id = request.values.get("group_id")
    if group_id is None:
        return jsonify({"error": "need group_id!"})

    image = aliyun_oss.pull_image_from_aliyun("%s/%s/%s" % (appid, group_id, image_name))
    if image is None:
        return jsonify({})
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
        return jsonify({})


@app.route('/face_search', methods=['GET', 'POST'])
def face_search():
    global max_id
    # update feature_dict from face_encoding table
    for i in sql_client.select(field="*", table_name="keruyun.image", where="id > %s" % max_id):
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
    max_id = sql_client.select(field="max(id) as max_id", table_name="keruyun.image")[0]["max_id"]
    if max_id is None:
        max_id = 0

    start = time.time()
    print("A", os.getpid(), os.getppid())
    image_name = request.values.get("image_name")
    if image_name is None:
        return jsonify({"error": "need image_name!"})
    appid = request.values.get("appid")
    if appid is None:
        return jsonify({"error": "need appid!"})

    group_id = request.values.get("group_id")
    if group_id is None:
        return jsonify({"error": "need group_id!"})

    search_group_id_list = request.values.get("search_group_id_list")
    if search_group_id_list is None:
        return jsonify({"error": "need search_group_id_list!"})

    max_user_num = request.values.get("max_user_num")
    if max_user_num is None:
        max_user_num = 5

    if appid not in feature_dict:
        return jsonify({})

    image = aliyun_oss.pull_image_from_aliyun("%s/%s/%s" % (appid, group_id, image_name))
    if image is None:
        return jsonify({})
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
        return jsonify({})
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


