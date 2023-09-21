""" 1.当为video状态时，循环播放视频\\
    2.当为work状态时，根据主进程的需要，向主进程发送识别后的数据，并持续显示实时画面"""

import multiprocessing
import enum


class WorkMode(enum.Enum):
    VIDEO, WORK = range(2)


class PipeMode(enum.Enum):
    """ 通信信息的合法类型 """
    ASK_INFOS = 0  # 请求返回识别信息
    SET_VIDEO = 1  # 进入video模式
    SET_WORK = 2  # 进入work模式


class ItemType(enum.Enum):
    kitchen, harmful, general, recycle = range(4)  # 此处顺序和满载提示顺序需要一致


def runProcess() -> multiprocessing.Process: ...
def sendPipeMode(work_mode: WorkMode): ...
