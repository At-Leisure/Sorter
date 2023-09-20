import time

import cv2
import yaml
from icecream import ic

import device
import camera
from position import transform


device.init()
camera.init()

with open('./config.yml', 'r', encoding='utf-8') as f:
    conf = yaml.load(f, yaml.BaseLoader)

print(conf)


def linkUpAPI(info):
    """ 链接camera和device的API，使可以从识别信息到分拣物体一贯而成。 """
    print(info)
    index, category, (x, y), (w, h), rotation = info
    if category in conf['有害垃圾']:
        the_kind = device.Kind.有害垃圾
    elif category in conf['回收垃圾']:
        the_kind = device.Kind.回收垃圾
    elif category in conf['厨余垃圾']:
        the_kind = device.Kind.厨余垃圾
    elif category in conf['其他垃圾']:
        the_kind = device.Kind.其他垃圾

    x = int(x / (640/1280))
    y = int(y / (640/1024))

    device.sequence_begin()
    device.baffle_set_all(0)
    device.reset_arm()
    tx, ty = transform(x, y)
    device.arm_move(tx, ty)
    device.arm_pick_up(rotation, 0, 10)
    device.baffle_set_all(1)
    device.arm_move_to(the_kind)
    device.arm_throw_down(0)
    device.arm_move(200, 200)
    device.reset_arm()


def test():
    """  """
    im = camera.extract()
    im = camera.extract()
    infos, draw = camera.scan_from(im)
    if infos:
        for info in infos:
            linkUpAPI(info)
            # while time.time() < device.ModulePropertyUnit.time:
            #     time.sleep(0.05)
    cv2.imshow('draw', draw)
    print(1)


device.wait_tkinter(test).mainloop()
