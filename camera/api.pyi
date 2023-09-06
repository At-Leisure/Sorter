""" 读取摄像头数据 """
from typing import overload
#
import cv2
import numpy as np
#
from .rabish_3_net import scan_image, scan_video


def camera_init(): ...
def extract(): ...
@overload
def scan_from(data: str) -> tuple[tuple, np.ndarray]: ...
@overload
def scan_from(data: np.ndarray) -> tuple[tuple, np.ndarray]: ...
