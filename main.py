# official module
import sys
import enum
from functools import partial
from threading import Thread
import typing
from PyQt5.QtWidgets import QWidget
# third-party module
import cv2
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore, uic
from PyQt5.QtCore import *
# api
import camera as CMR
import device as DVS
import graphic as GRC
from test_linkup import linkUpAPI
#
import time

DVS.init()
CMR.init()




    

class SorterWindow(GRC.MainWindow):
    """ 最终界面 """

    def __init__(self, *args, **kwargs):
        GRC.MainWindow.__init__(self)

        self.ctrl_thread = Thread(target=self.run, daemon=True, name='控制')

# ==============================================视频循环 and 分拣控制=================================================#

    def run(self):
        """ 视频循环 and 分拣控制 """
        while True:
            # """ 视频循环 """
            if self.video_page.video_state is self.video_page.VS.FINISHED:
                self.video_page.play_video()  # 重新播放

            # """ 流程控制 """
            raw_image = CMR.extract()  # 获得原始图像
            infos, draw = CMR.scan_from(raw_image)  # 分析图像
            if infos:  # 如果有识别到物件-切换到工作页面
                self.changePageTo('work')
                print(len(infos))
                GRC.setQLabelPixmap(self.work_page.work_screen, draw)

            else:  # 切换到待机页面
                self.changePageTo('video')

            # 控制线程睡眠0.1s-尝试不让此线程阻塞主线程
            time.sleep(0.1)

# ========================================================================================================================#


def justRun(func): func()


@justRun
def main():
    app = QApplication(sys.argv)
    # 加载qss
    with open('./graphic/main.qss', 'r', encoding='utf-8') as f:
        qss = ''.join(f.readlines())
    app.setStyleSheet(qss)
    window = SorterWindow()
    window.show()
    window.ctrl_thread.start()  # 开启控制线程
    sys.exit(app.exec())
