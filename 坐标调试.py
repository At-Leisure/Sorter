import time
#
import cv2
#
import camera as CMR
import device as DVS
import graphic as GRC

CMR.init()
DVS.init()
#DVS.reset_move()
DVS.reset_arm()
DVS.baffle_set_all(1)
def linkUp(info):
    """ 输入摄像头的扫描数据，执行一次拾取作业
    (序号，类型，中心点，最小外接矩形的长宽，旋转角度) """
    index, category, (x,y), (w,h), rotation = info
    rotation %= 180
    x,y = CMR.image_to_robot_arm(x,y)
    DVS.sequence_begin()
    DVS.arm_move(x,y)
    DVS.arm_pick_up(rotation,0,0)
    DVS.arm_move_to(DVS.压缩垃圾)
    DVS.arm_throw_down(0)
    DVS.sequence_finish()


def test():
            im = CMR.extract()
            im = CMR.extract()
            im = cv2.rotate(im, cv2.ROTATE_180)

            infos, draw = CMR.scan_from(im)
            cv2.imshow('im',draw)
            if infos:
                for info in infos:
                    linkUp(info)


DVS.wait_tkinter(test).mainloop()