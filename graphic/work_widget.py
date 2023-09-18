""" 够显示垃圾分类的各种数据，如投放顺序、垃圾名称、数量、任务完成提示、满载情况等。 """
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


class ItemType(enum.Enum):
    """ 物件类型：
    `HENERAL` - 其他垃圾
    `RECYCLE` - 可回收垃圾
    `KITCHEN` - 厨余垃圾
    `HARMFUL` - 有害垃圾 """
    GENERAL, RECYCLE, KITCHEN, HARMFUL = range(4)


def setQLabelPixmap(lbl: QLabel, im: str | np.ndarray):
    """ 图片自适应填充标签显示 """
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


class WorkImage(QWidget):
    """ Image-Widget """

    def __init__(self, parent, image_path: str = './icon/pink_flash.png', *args, **kwargs) -> None:
        super(QWidget, self).__init__(parent, *args, **kwargs)
        # 动态加载ui文件
        self.ui = uic.loadUi('./graphic/single_item.ui', self)
        # 函数重载实现
        setQLabelPixmap(self.image_label, image_path)


class WorkThrow(QWidget):
    """ Throw-Widget """

    def __init__(self, parent, a: str, b: str, c: str, d: str, *args, **kwargs) -> None:
        """ 分拣完成提示-示例`1 有害垃圾 1 OK!`
        ## Parameters
        `a` - 序号
        `b` - 种类
        `c` - 数量
        `d` - 成否"""
        super(QWidget, self).__init__(parent)
        # 动态加载ui文件
        self.ui = uic.loadUi('./graphic/throw_item.ui', self)
        self.a.setText(str(a))
        self.b.setText(str(b))
        self.c.setText(str(c))
        self.d.setText(str(d))


class WorkWidget(QWidget):
    """ main window """

    def __init__(self):
        super(QWidget, self).__init__()
        # 动态加载ui文件
        self.ui = uic.loadUi('./graphic/work_widget.ui', self)

        self.fullLoad_general: QLabel  # 其他垃圾-满载提示
        self.fullLoad_recycle: QLabel  # 可回收垃圾-满载提示
        self.fullLoad_kitchen: QLabel  # 厨余垃圾-满载提示
        self.fullLoad_harmful: QLabel  # 有害垃圾-满载提示
        
        self.work_screen :QLabel #播放屏幕

        self.image_scroll: QScrollArea
        self.image_scroll_queue = []  # 队列，先入先出
        self.throw_scroll: QScrollArea
        self.throw_scroll_queue = []

    def fullyLoadedTip(self, which_type: ItemType, isFull: bool):
        """ 满载提示-对应标签变红 
        `which_type` - 选择调整对象
        `isFull` - 调整值"""
        if which_type is ItemType.GENERAL:  # 有害垃圾满载
            self.fullLoad_general.setProperty('isFulled', isFull)
        elif which_type is ItemType.RECYCLE:  # 可回收垃圾满载
            self.fullLoad_recycle.setProperty('isFulled', isFull)
        elif which_type is ItemType.KITCHEN:  # 厨余垃圾满载
            self.fullLoad_kitchen.setProperty('isFulled', isFull)
        elif which_type is ItemType.HARMFUL:  # 有害垃圾满载
            self.fullLoad_harmful.setProperty('isFulled', isFull)
        else:
            raise ValueError(f'{which_type.value} 不存在该枚举常量')

    def _test_addImages(self, n1=15, n2=20):
        from random import randint
        # 左上侧添加示例
        lot = self.image_scroll.widget().layout()
        # QScrollArea的布局的调用只能通过scroll.widget()进行
        for _ in range(n1):
            wim = WorkImage(self.image_scroll)
            wim.category_label.setText(f'类型：None')
            # 队列之末，弹簧之前
            self.image_scroll_queue.append(wim)
            lot.insertWidget(-2, self.image_scroll_queue[-1])
            # 底部有弹簧，防止控件在少量时分散
        # 右下侧添加示例
        lot = self.throw_scroll.widget().layout()
        category = [0, 0, 0, 0]
        for i in range(n2):
            j = randint(0, 3)
            category[j] += 1
            wit = WorkThrow(self.throw_scroll, i, j, category[j], 'OK')
            self.throw_scroll_queue.append(wit)
            # 队列之末，弹簧之前
            lot.insertWidget(1, self.throw_scroll_queue[-1])

    def updateImagesIndex(self):
        """ 更新投放列表的序号，从1开始 """
        for i, wim in enumerate(self.image_scroll_queue):
            wim.index_label.setText(f'序号：{i+1}')


# main threading
if __name__ == '__main__':
    app = QApplication(sys.argv)
    work_widget = WorkWidget()
    work_widget.setWindowTitle('垃圾分类装置 - Equipment of Garbage Sorting')
    work_widget.setWindowIcon(QIcon('./icon/flash.png'))
    work_widget.show()
    with open('./graphic/main.qss', 'r', encoding='utf-8') as f:
        qss = ''.join(f.readlines())
    app.setStyleSheet(qss)
    work_widget._test_addImages()  # 添加
    work_widget.updateImagesIndex()  # 排序
    sys.exit(app.exec_())
