""" 支持各种格式的视频和图片播放， """
# encoding:utf-8
# file:main.py
# official module
import sys
import enum
from functools import partial
import time
from threading import Thread
import json
import typing
import yaml

# third-party module
import cv2
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import *


class VideoState(enum.Enum):
    FINISHED, RUNNING, PAUSE = range(3)


class VideoWidget(QWidget):
    """ main window """

    def __init__(self, default_video_path: str):
        super(QWidget, self).__init__()
        # 动态加载ui文件
        self.ui = uic.loadUi('./graphic/video_widget.ui', self)
        self.video_screen: QLabel  # 视频幕布
        self.video_container: QWidget  # 幕布容器
        self.video_button: QPushButton  # 播放按钮
        self.video_button.clicked.connect(self.play_video)
        # 属性值
        self.progressBar : QProgressBar #显示进度
        self.video_path = default_video_path
        self.video_state = VideoState.FINISHED  # 设置为播放完成状态
        self.video_thread = None  # 视频播放线程
        self.video_break = False  # 视频中断信号

    def videoPause(self, is_pause: bool):
        """ 睡眠暂停 """
        self.video_state = VideoState.PAUSE if is_pause else VideoState.RUNNING

    def run(self):
        """ 新线程的目标任务 """
        video_capture = cv2.VideoCapture(self.video_path)  # 视频读取器
        # 获取帧数和帧速率
        frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.progressBar.setRange(0,frame_count)
        # 播放每一帧
        frame_count_i = 0
        while video_capture.isOpened():
            #更新进度条
            frame_count_i += 1
            if frame_count_i <= frame_count-1:
                self.progressBar.setValue(frame_count_i)#这里的值不能超出设置的范围，否则程序会直接退出
            # 获取视频信息
            fps = int(video_capture.get(cv2.CAP_PROP_FPS))  # 视频帧率
            video_width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            video_height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            # 获取最小缩放比
            label_size = self.video_screen.size()
            resize_ratio = min(label_size.width()/video_width,
                               label_size.height()/video_height)
            # 实际显示尺寸
            target_width = int(resize_ratio*video_width)
            target_height = int(resize_ratio*video_height)

            # 通过睡眠暂停
            while self.video_state is VideoState.PAUSE:
                time.sleep(0.01)

            if not self.video_break:
                # 播放视频代码
                useful, frame = video_capture.read()  # 读取当前帧
                # 读取失败，播放结束
                if useful == False:
                    break
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 变化通道排列为RGB
                image = cv2.resize(frame,
                                   (target_width, target_height))  # 更改图片尺寸
                # 将图片数据加载为PyQt可使用的类型，彩色图像的每行字节数应该为其宽度乘以通道数
                # 使用QImage的bytesPerLine参数，防止图像变灰和显示倾斜
                qt_img = QImage(image.data, target_width, target_height,
                                target_width*3, QImage.Format_RGB888)
                qt_pix = QPixmap.fromImage(qt_img)  # 加载图片为可显示的类型
                self.video_screen.setPixmap(qt_pix)  # 加载图片到幕布上并显示
                time.sleep(1/fps)  # 同步视频实际播放速度
            # 视频中断代码
            else:
                # 打断播放
                break
        # 更新状态，为下次播放做准备
        self.video_break = False
        self.video_state = VideoState.FINISHED
        print('[INFO]Video read completed.')

    def play_video(self):
        """ 创建一个新的线程用以播放视频 """
        # 如果正在播放，就打断当前播放，重新播放视频
        if self.video_state is VideoState.RUNNING:
            self.video_break = True
            # 等待视频中断
            while self.video_state is VideoState.RUNNING:
                pass
        # 播放新的视频
        self.video_state = VideoState.RUNNING  # 设置为播放状态
        # 创建新的线程
        self.video_thread = Thread(target=self.run, daemon=True,name='播放')
        self.video_thread.start()
        print('[INFO]Video starts playing.')


# main threading
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VideoWidget('./video/示例.mp4')
    window.setWindowTitle('垃圾分类装置 - Equipment of Garbage Sorting')
    window.setWindowIcon(QIcon('./icon/flash.png'))
    window.show()
    sys.exit(app.exec_())
