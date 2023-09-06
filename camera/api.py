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
