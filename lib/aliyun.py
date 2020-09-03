# -*- coding: utf-8 -*-

import oss2
import numpy as np
import cv2
import requests
import json
from lib.time_fuc import *


class Aliyun(object):

    def __init__(self):
        self.accessKeySecret = None
        self.securityToken = None
        self.expiration = None
        self.accessKeyId = None
        self.sts_auth = None
        # self.oss_endpoint = "kry-ai.oss-cn-hangzhou-internal.aliyuncs.com"
        # self.oss_endpoint = "oss-cn-hangzhou-internal.aliyuncs.com"
        self.oss_endpoint = "oss-cn-hangzhou.aliyuncs.com"
        self.oss_bucket = "kry-ai"
        self.bucket = None
        # self.bucket = oss2.Bucket(
        #     oss2.Auth(account_info["AccessKeyId"], account_info["AccessKeySecret"]),
        #     account_info["EndPoint"], account_info["Bucket"])

    def check_account_info(self):
        if self.accessKeySecret is None or datetime.datetime.now() > self.expiration:
            print("get acount info")
            url = 'http://alists.keruyun.com/api/v1/osstoken/'
            payload = {
                'bucket': 'kry-ai'
            }
            # Adding empty header as parameters are being sent in payload
            headers = {"Authorization": "Token bec5aeb7deeb833442b1ad9eefefd63c256db50c"}
            r = requests.post(url, data=json.dumps(payload), headers=headers)
            data1 = json.loads(r.content)
            # print(data1)
            credentials = data1["data"]["Credentials"]
            self.accessKeySecret = credentials["AccessKeySecret"]
            self.securityToken = credentials["SecurityToken"]
            self.expiration = utc2local(datetime.datetime.strptime(credentials["Expiration"], "%Y-%m-%dT%H:%M:%SZ"))
            self.accessKeyId = credentials["AccessKeyId"]
            self.sts_auth = oss2.StsAuth(self.accessKeyId, self.accessKeySecret, self.securityToken)
            # self.bucket = oss2.Bucket(self.sts_auth, self.oss_endpoint, self.oss_bucket)

    def push_image2aliyun(self, remote_file_name, local_file_name):
        self.check_account_info()
        self.bucket = oss2.Bucket(self.sts_auth, self.oss_endpoint, self.oss_bucket)
        return self.bucket.put_object_from_file(remote_file_name, local_file_name)

    def push_object2aliyun(self, remote_fine_name, image):
        self.check_account_info()
        self.bucket = oss2.Bucket(self.sts_auth, self.oss_endpoint, self.oss_bucket)
        img_encode = cv2.imencode('.jpg', image)[1]
        print(type(img_encode))
        data_encode = np.array(img_encode)
        str_encode = data_encode.tostring()
        self.bucket.put_object(remote_fine_name, str_encode)

    def pull_image_from_aliyun(self, remote_file_name):
        self.check_account_info()
        self.bucket = oss2.Bucket(self.sts_auth, self.oss_endpoint, self.oss_bucket)
        try:
            image = np.asarray(bytearray(self.bucket.get_object(remote_file_name).read()), dtype="uint8")
            image = cv2.imdecode(image, cv2.IMREAD_COLOR)
            image = image[:, :, ::-1]
            return image
        except:
            return None


if __name__ == "__main__":
    import time
    import os
    from lib.mysql import *
    # account_info = {
    #     "AccessKeyId": "***",
    #     "AccessKeySecret": "**",
    #     "EndPoint": "***",
    #     "Bucket": "keruyun-face"
    # }
    #
    # aliyun = Aliyun(account_info)
    # sql_client = MysqlClient(host='localhost', user='root')
    # start = time.time()
    # image = cv2.imread("../face_images/zilu_4.jpg")
    # aliyun.push_object2aliyun("fuck.jpg", image)

    # for image_path in os.listdir("../face_images"):
    #     aliyun.push_image2aliyun("2/1/%s/%s" % (
    #         image_path.split("_")[1].split(".")[0], image_path), "../face_images/%s" % image_path)
    #     print(time.time()-start)
    # start = time.time()
    # image = aliyun.pull_image_from_aliyun("2/1/biantaigou_999090.png")
    # print(image.shape)
    # print(time.time() - start)
    aliyun = Aliyun()
    # aliyun.push_image2aliyun("test/1.jpg", "../face_images/zilu_4.jpg")
    print(aliyun.pull_image_from_aliyun("test/1.jpg").shape)
    print(aliyun.pull_image_from_aliyun("test/1.jpg").shape)


