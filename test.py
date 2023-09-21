import time
#
import cv2
import yaml
from icecream import ic
#
import device
import camera
from position import transform


with open('./config.yml', 'r', encoding='utf-8') as f:
    conf = yaml.load(f, yaml.BaseLoader)


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
    print(category, the_kind)

    x = int(x / (640/1280))
    y = int(y / (640/1024))

    device.sequence_begin()
    device.reset_arm()
    tx, ty = transform(x, y)
    device.arm_move(tx, ty)
    device.arm_pick_up(rotation, 0, 10)
    device.arm_move_to(the_kind)
    device.arm_throw_down(0, the_kind)
    device.arm_move(200, 200)
    device.reset_arm()


if __name__ == '__main__':

    class Tester:
        @staticmethod
        def test_linkUpAPI():
            device.init()
            camera.init()
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
            device.wait_tkinter(test)

        @staticmethod
        def test_pickUp_throwDown():
            device.init()
            def test():
                device.sequence_begin()#开始
                device.arm_move(4000,4000)
                device.arm_pick_up(45,0,10)
                device.arm_move(4000,7500)
                device.arm_throw_down(0,device.Kind.回收垃圾)
                device.arm_move(0,0)
                device.reset_arm()
                # # t = time()
                # # device.DeviceDriver.yaso_press(9.99,0.99,0.005,runtime=t)
                # # device.DeviceDriver.yaso_press(0,0.5,0.01,runtime=t+0.5)
                device.sequence_finish()#结束
            device.wait_tkinter(test)
            
        @staticmethod
        def test_autoBaffle():
            device.init()
            def test():
                device.sequence_begin()
                device.baffle_set_all(device.CLOSE)
                device.arm_throw_down(0,kind=device.Kind.有害垃圾)
                device.reset_arm()
                time.sleep(5)
                device.sequence_begin()
                device.arm_throw_down(0,kind=device.Kind.回收垃圾)
                device.reset_arm()
                time.sleep(5)
                device.sequence_begin()
                device.arm_throw_down(0,kind=device.Kind.厨余垃圾)
                device.reset_arm()
                time.sleep(5)
                device.sequence_begin()
                device.arm_throw_down(0,kind=device.Kind.其他垃圾)
                device.reset_arm()
            device.wait_tkinter(test)
        
    Tester.test_pickUp_throwDown()