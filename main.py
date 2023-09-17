# official module
import sys
import enum
from functools import partial
from threading import Thread
import typing
import typing
from PyQt5.QtWidgets import QWidget


# third-party module
import cv2
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore, uic
from PyQt5.QtCore import *
#
import camera as CMR
import device as DVS
import graphic as GRC


class SorterWindow(GRC.MainWindow):
    """ 最终界面 """
    def __init__(self, *args, **kwargs):
        GRC.MainWindow.__init__(self)


def justRun(func):
    func()
    return func


@justRun
def main():
    app = QApplication(sys.argv)
    # 加载qss
    with open('./graphic/main.qss', 'r', encoding='utf-8') as f:
        qss = ''.join(f.readlines())
    app.setStyleSheet(qss)
    window = SorterWindow()
    window.show()
    sys.exit(app.exec())
