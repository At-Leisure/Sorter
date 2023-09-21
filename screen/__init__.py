""" 1.当为video状态时，循环播放视频\\
    2.当为work状态时，根据主进程的需要，向主进程发送识别后的数据，并持续显示实时画面"""

# official module
import sys
import enum
from functools import partial
from threading import Thread
import typing
import multiprocessing
from multiprocessing.connection import PipeConnection
import yaml
# third-party module
import cv2
import numpy as np
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore, uic
from PyQt5.QtCore import *
#
from camera import scan_from


class WorkMode(enum.Enum):
    """ 工作两个模式"""
    VIDEO, WORK = range(2)  # 两个工作状态


class PipeMode(enum.Enum):
    """ 通信信息的合法类型 """
    ASK_INFOS = 0  # 请求返回识别信息
    SET_VIDEO = 1  # 进入video模式
    SET_WORK = 2  # 进入work模式


class ItemType(enum.Enum):
    """ 物品四大类 """
    kitchen, harmful, general, recycle = range(4)  # 此处顺序和满载提示顺序需要一致


def _coverQLabelByArray(lbl: QLabel, im_gbr: str | np.ndarray):
    """ 使用矩阵图像覆盖QLabel的画面 """
    im = im_gbr
    if isinstance(im, str):
        im = cv2.imread(im)
    imH, imW = im.shape[:2]  # 图像的高宽
    lbH, lbW = lbl.height(), lbl.width()
    minRatio = min(lbH/imH, lbW/imW)  # 最适缩放比
    targetW, targetH = int(minRatio*imW), int(minRatio*imH)
    imRGB = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)  # 变化通道排列为RGB
    image = cv2.resize(imRGB, (targetW, targetH))  # 更改图片尺寸
    # 将黑色区域变成白色
    mask = np.all(image == [0, 0, 0], axis=2)  # 创建掩膜，将黑色区域设为 True
    image[mask] = (240, 240, 240)  # 将黑色区域的像素值设为灰白色
    qt_img = QImage(image.data, targetW, targetH,
                    targetW*3, QImage.Format_RGB888)
    qt_pix = QPixmap.fromImage(qt_img)  # 加载图片为可显示的类型
    lbl.setPixmap(qt_pix)  # 加载图片到幕布上并显示


pipe_ctrl = ...  # 占位声明
""" 双进程通信管道-控制端 """
pipe_disp = ...  # 占位声明
""" 双进程通信管道-显示端 """

pipe_ctrl, pipe_disp = multiprocessing.Pipe()


def _dispProcess(pipe_disp_: PipeConnection):
    with open('./config.yml', 'r', encoding='utf-8') as f:
        conf = yaml.load(f, yaml.BaseLoader)  # 配置.yml

    class ProcessWindow(QWidget):
        """ 单开一个进程用来处理视频 """

        def __init__(self, *args, **kwargs):
            QWidget.__init__(self)
            # 动态加载ui文件
            uic.loadUi('./screen/screen.ui', self)
            # 声明控件
            self.label_screen: QLabel
            self.setItemFull(False)

            # 视频和摄像头地画面捕获器
            self.video_cap = cv2.VideoCapture(conf['视频'])  # 视频捕获器
            self.camera_cap = cv2.VideoCapture(1)  # 摄像头画面捕获器
            self.is_identifying = False  # 是否正在分类识别图像
            self.identify_period = 100  # 检测是否在识别中地降额间隔毫秒数
            self.work_mode = WorkMode.VIDEO  # 设置默认工作状态
            self.is_returninfos = False  # 是否返回识别信息
            # 设置screen画面更新定时器
            self.timer = QTimer(self)  # 创建定时器
            self.timer.timeout.connect(self.update_frame)  # 定时器触发更新方法
            self.video_period = int(
                1000/self.video_cap.get(cv2.CAP_PROP_FPS))  # 获取视频帧率对应的周期
            self.timer.start(self.video_period)  # 设置定时器间隔

            # 设置定时器以接收通信管线的信息
            self.pipe_disp = pipe_disp_  # 引用通信管线
            self.recv_timer = QTimer(self)
            self.recv_timer.timeout.connect(self.updatePipeMode)
            self.recv_timer.start(50)  # 隔n毫秒接收管线信息

        def updatePipeMode(self):
            # 接收来自控制进程的消息
            msg: PipeMode  # 使编辑器可以提示代码
            if self.pipe_disp.poll():  # 是否有任何可供读取的输入信息，防止阻塞
                msg = self.pipe_disp.recv()  # 阻塞式接收来自管线地信息
                assert isinstance(
                    msg, PipeMode), f'{type(msg)} 类型非法'  # 检测信息地非法性
                # 检测信息类型
                if msg is PipeMode.SET_VIDEO:
                    self.work_mode = WorkMode.VIDEO  # 更新为对应工作模式
                    period_ms = self.video_period  # 设置定时器间隔为视频帧率周期
                elif msg is PipeMode.SET_WORK:
                    self.work_mode = WorkMode.WORK
                    period_ms = self.identify_period  # 设置定时器间隔为识别检测周期
                # 如果是返回识别信息的请求
                # elif msg is PipeMode.ASK_INFOS:
                #     self.is_returninfos = True
                #     return
                self.timer.setInterval(period_ms)  # 设置新周期
                print(f'[INFO]更新为{msg.name}模式，检测周期为{period_ms}ms')

        def setItemFull(self, isFull: bool, which: ItemType = None):
            """ 设置对应itemtype的满载情况。当which==None，则覆盖全部四个标签。"""
            if which is None:
                for i in range(4):
                    exec(
                        f'self.label_full_{i}.setProperty("isFulled",{isFull})')
            else:
                exec(
                    f'self.label_full_{which.value}.setProperty("isFulled",{isFull})')

        def update_frame(self):
            """ 播放视频 or 实时演示"""
            # 当工作状态为视频播放
            if self.work_mode is WorkMode.VIDEO:
                ret, video_frame = self.video_cap.read()
                if ret:  # 成功读取
                    _coverQLabelByArray(self.label_screen,
                                        video_frame)  # 视频读取成功时，更新画面
                else:  # 读取失败
                    self.video_cap.set(
                        cv2.CAP_PROP_POS_FRAMES, 0)  # 视频读取完毕时，重置指针
            # 当工作状态为实时演示
            elif self.work_mode is WorkMode.WORK:
                if self.is_identifying:
                    # 识别处于统一线程，所以此if语句永远不会执行
                    print('识别中，此次不更新图像')
                    return
                # 新一轮识别
                self.is_identifying = True  # 开始分类识别
                ret, im = self.camera_cap.read()  # 0
                ret, im = self.camera_cap.read()  # 1 重复以防止画面不是及时的
                infos, draw = scan_from(im)
                _coverQLabelByArray(self.label_screen,
                                    draw)  # 更新识别画面
                self.is_identifying = False  # 结束分类识别

    # 开启画面
    app = QApplication(sys.argv)
    with open('./screen/screen.qss', 'r', encoding='utf-8') as f:
        qss = ''.join(f.readlines())
    app.setStyleSheet(qss)
    window = ProcessWindow('./video/示例.mp4')
    window.setWindowTitle('Equipment of Garbage Sorting')
    window.setWindowIcon(QIcon('./icon/flash.png'))
    window.show()
    sys.exit(app.exec_())


def runProcess() -> multiprocessing.Process:
    """ 打开播放视频进程并返回其引用 """
    a = multiprocessing.Process(
        target=_dispProcess, daemon=True, args=(pipe_disp,))
    a.start()
    return a


def sendPipeMode(pipe_mode: PipeMode):
    """ 向子进程发送设置工作状态的提示
    >>> sendPipeMode(PipeMode.VIDEO) #使进入video模式
    >>> sendPipeMode(PipeMode.WORK) #使进入work模式
    >>> sendPipeMode(PipeMode.ASK_INFOS) #请求返回识别信息"""
    global pipe_ctrl
    assert isinstance(
        pipe_mode, PipeMode), f'{type(pipe_mode)} 类型非法'  # 检测信息地非法性
    pipe_ctrl.send(pipe_mode)  # 发送


if __name__ == '__main__':
    """ 到test.py去测试 """
    runProcess().join()
