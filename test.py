import requests
import time
import os

start = time.time()
for image_path in os.listdir("face_images/"):

    result = requests.post("http://172.16.30.162:5001/face_register",
                           data={
                               'image_name': image_path,
                               'appid': 2,
                               'group_id': 1,
                               "uid": image_path.split("_")[1].split(".")[0]
                           })
    print(result.json())
    print(time.time()-start)
    exit()

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

# start = time.time()
# result = requests.post("http://localhost:5001/face_detect",
#                        data={
#                            'image_name': "1/yuanjun_1.jpg",
#                            'appid': 2,
#                            'group_id': 1,
#                            "search_group_id_list": "1"
#                            })
# print(result.json())
# print(time.time()-start)

