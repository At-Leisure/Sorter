""" 读取摄像头数据 """
from typing import overload
#
import cv2
import numpy as np
#
from .rabish_3_net import scan_image, scan_video

CAP_WIDTH_MAX = 1280
CAP_HEIGHT_MAX = 1024

def init(): ...
def extract(): ...
@overload
def scan_from(data: str) -> tuple[tuple, np.ndarray]: ...
@overload
def scan_from(data: np.ndarray) -> tuple[tuple, np.ndarray]: ...
def image_to_robot_arm(image_x, image_y) -> tuple[int, int]: ...
