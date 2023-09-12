""" 读取摄像头数据 """
from typing import overload
#
import cv2
import numpy as np
#
from .rabish_3_net import scan_image, scan_video


cap = None
CAP_WIDTH_MAX = 1280
CAP_HEIGHT_MAX = 1024

def camera_init():
    """ 连接相机 """
    global cap
    cap = cv2.VideoCapture(1)
    # 设置帧的宽度和高度
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAP_WIDTH_MAX)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAP_HEIGHT_MAX)
    
    
def extract():
    """ 视频抽帧 """
    ret,frame = cap.read()
    assert ret,'警告：抽取图像失败'
    return frame
    


def scan_from(data: str | np.ndarray):
    """ 从图片中获取信息
    ## Parameter
    `data` - str: 本地图片地址， MatLike: cv2的图像矩阵数据
    ## Return
    [(序号，类型，中心点，最小外接矩形的长宽，旋转角度), ...]
    ## Example
    >>> scan_from()
    [('1', 'recyclable', ['184', '349'], ['225', '507'], '89'), ('2', 'recyclable', ['444', '352'], ['235', '508'], '90')]"""
    if isinstance(data, str):
        return scan_image(data)
    elif isinstance(data, np.ndarray):
        return scan_video(data)
    else:
        raise TypeError()



def image_to_robot_arm(image_x, image_y):
    """ 将图片坐标转换为步进电机坐标 """
    # 图像坐标范围
    image_min_x = 151
    image_max_x = 516
    image_min_y = 545
    image_max_y = 8

    # 机械臂坐标范围
    arm_min_x = 0
    arm_max_x = 7000
    arm_min_y = 0
    arm_max_y = 8000

    # 缩放因子的倒数
    scale_factor_x = (arm_max_x - arm_min_x) / (image_max_x - image_min_x)
    scale_factor_y = (arm_max_y - arm_min_y) / (image_max_y - image_min_y)

    # 坐标映射计算
    robot_arm_x = int((image_x - image_min_x) * scale_factor_x + arm_min_x)
    robot_arm_y = int((image_y - image_min_y) * scale_factor_y + arm_min_y)

    # 返回实际机械臂坐标
    print(robot_arm_x, robot_arm_y)
    return robot_arm_x, robot_arm_y
