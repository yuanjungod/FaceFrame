import requests
import time
import os


import base64


def get_image_base64(image_path):
    with open(image_path, "rb") as f:
        base64_data = base64.b64encode(f.read())
        return base64_data
        # base64.b64decode(base64data)
        # print(base64_data)

# start = time.time()
# for image_path in os.listdir("face_images/"):
#
#     result = requests.post("http://172.16.30.162:5001/face_register",
#                            data={
#                                'image_name': image_path,
#                                'appid': 2,
#                                'group_id': 1,
#                                "uid": image_path.split("_")[1].split(".")[0]
#                            })
#     print(result.json())
#     print(time.time()-start)
#     exit()

# start = time.time()
# result = requests.post("http://172.16.30.162:5001/face_search",
#                        data={
#                            'image_name': "1/erge_2.jpg",
#                            'appid': 2,
#                            'group_id': 1,
#                            "search_group_id_list": "1"
#                            })
# print(result.json())
# print(time.time()-start)


start = time.time()
result = requests.post("http://ai-api.keruyun.com:5001/face_detect",
                       data={
                           'base64_image_str': get_image_base64("face_images/ziyu_5.jpg"),
                           'appid': 2,
                           'group_id': 1,
                           'uid': 2,
                           "search_group_id_list": "1"
                           })
print(result.json())
print(time.time()-start)

