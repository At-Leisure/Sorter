""" 读取摄像头数据 """
from typing import overload

import cv2
import numpy as np

try:
    from .rabish_3_net import scan_image, scan_video
except:
    from rabish_3_net import scan_image, scan_video


@overload
def scan_from(data: str) -> tuple: pass
@overload
def scan_from(data: np.ndarray) -> tuple: pass


def scan_from(data):
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


if __name__ == '__main__':
    """ sample = './camera/sample.jpg'
    print(scan_from(sample))
    m = cv2.imread(sample)
    print(type(m))
    print(scan_from(m)) """
    
    v = cv2.VideoCapture(0)
    v.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
    v.set(cv2.CAP_PROP_FRAME_HEIGHT,1024)
    while v.isOpened():
        ret ,img = v.read()
        cv2.imshow('im',img)
        cv2.waitKey(int(1000/60))
        
