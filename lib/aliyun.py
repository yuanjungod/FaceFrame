# -*- coding: utf-8 -*-

import oss2
import numpy as np
import cv2


class Aliyun(object):

    def __init__(self, account_info):
        self.bucket = oss2.Bucket(
            oss2.Auth(account_info["AccessKeyId"], account_info["AccessKeySecret"]),
            account_info["EndPoint"], account_info["Bucket"])

    def push_image2aliyun(self, remote_file_name, local_file_name):
        return self.bucket.put_object_from_file(remote_file_name, local_file_name)

    def pull_image_from_aliyun(self, remote_file_name):
        image = np.asarray(bytearray(self.bucket.get_object(remote_file_name).read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        image = image[:, :, ::-1]
        return image


if __name__ == "__main__":
    import time
    import os
    from lib.mysql import *
    account_info = {
        "AccessKeyId": "LTAI1121mPMMQ0mO",
        "AccessKeySecret": "3rZfXSiHE0KNvZU8csYiFEPtViPY0v",
        "EndPoint": "oss-cn-shenzhen.aliyuncs.com",
        "Bucket": "keruyun-face"
    }

    aliyun = Aliyun(account_info)
    sql_client = MysqlClient(host='localhost', user='root')
    start = time.time()

    for image_path in os.listdir("../face_images"):
        aliyun.push_image2aliyun("2/1/%s/%s" % (
            image_path.split("_")[1].split(".")[0], image_path), "../face_images/%s" % image_path)
        print(time.time()-start)
    # start = time.time()
    # image = aliyun.pull_image_from_aliyun("2/1/biantaigou_999090.png")
    # print(image.shape)
    # print(time.time() - start)


