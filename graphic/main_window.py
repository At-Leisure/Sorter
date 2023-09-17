# encoding:utf-8
# file:main.py

# official module
import sys
import enum
from functools import partial
import time
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
try:
    from .video_widget import VideoWidget
    from .work_widget import WorkWidget
except:
    from video_widget import VideoWidget
    from work_widget import WorkWidget
    print('local import')


class MainWindow(QMainWindow):
    """ 主界面 """

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        # 动态加载ui文件
        self.ui = uic.loadUi('./graphic/main_window.ui', self)
        # 可堆叠窗口
        self.stackedWidget: QStackedWidget
        self.video_page = VideoWidget('./video/宣传.mp4')  # 创建页
        self.work_page = WorkWidget()
        self.stackedWidget.addWidget(self.video_page)  # 添加页
        self.stackedWidget.addWidget(self.work_page)
        # 标明控件
        self.state_label: QLabel
        self.state_button: QPushButton
        self.state_button.clicked.connect(self.changePageReverse)
        
        #开始播放-注意，此时不能循环播放
        self.video_page.play_video()

    def changePageTo(self, which: str):
        if which[0] == 'v':
            self.video_page.videoPause(False)
            self.stackedWidget.setCurrentWidget(self.video_page)
            self.state_label.setText('播放视频ING')
        elif which[0] == 'w':
            # 休眠播放
            self.video_page.videoPause(True)
            self.stackedWidget.setCurrentWidget(self.work_page)
            self.state_label.setText('识别分拣ING')

    def changePageReverse(self):
        if self.stackedWidget.currentWidget() is self.video_page:
            self.changePageTo('work')
        elif self.stackedWidget.currentWidget() is self.work_page:
            self.changePageTo('video')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 加载qss
    with open('./graphic/main.qss', 'r', encoding='utf-8') as f:
        qss = ''.join(f.readlines())
    app.setStyleSheet(qss)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
