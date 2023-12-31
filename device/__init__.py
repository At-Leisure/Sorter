""" 应用程序接口-API """
# API-应用程序与外设驱动的桥梁
# 目录包含顺序: {(API): (tools, device_driver); device_driver: (tools)}

from .tools import *
import tkinter as tk
from time import time as ttime
from .device_driver import DeviceDriver
from .speed_api import timeCalculate
from icecream import ic
from enum import Enum


""" 命名空间 - 分拣操作API - 高层封装  """


OPEN, CLOSE = 1, 0
default_speed = 10_000


class ModulePropertyUnit:
    """ API模块属性量 """
    advance_time = 0
    advance_using = False
    x, y = 0, 0

    @classmethod
    @property
    def time(cls):
        return cls.advance_time

    @classmethod
    def add_time(cls, more_time):
        if not cls.advance_time is None:
            cls.advance_time += more_time


MPU = ModulePropertyUnit


def init():
    """ 初始化连接， """
    DeviceDriver.connect()


def baffle_set(status: bool, sid: SID, *, runtime: float = None):
    """ 设置挡板 """
    DeviceDriver.steer_set(
        sid, 0 if status == CLOSE else 100, runtime=runtime)


def baffle_set_all(status: bool, *, runtime: float = None):
    """ 设置挡板 """
    value = 0 if status == CLOSE else 100
    DeviceDriver.steer_set(SID.BAFFLE_0, value, runtime=runtime)
    DeviceDriver.steer_set(SID.BAFFLE_1, value, runtime=runtime)
    DeviceDriver.steer_set(SID.BAFFLE_2, value, runtime=runtime)
    DeviceDriver.steer_set(SID.BAFFLE_3, value, runtime=runtime)


def arm_move(x: int, y: int, v: int = default_speed, *, runtime: float = None) -> float:
    """ 返回移动所耗时间 
    ## Parameter
    `x` - 坐标x
    `y` - 坐标y
    `v` - 移动速度
    ## Return
    `consume` - 此次移动耗时"""
    runtime = ttime() if MPU.time is None else MPU.time

    DeviceDriver.arm_move(x, y, v, runtime=runtime)

    consume = timeCalculate(MPU.x-x, MPU.y-y, v)
    MPU.add_time(consume)

    MPU.x = x
    MPU.y = y

    return consume


class Kind(Enum):
    回收垃圾 = 0
    厨余垃圾 = 1
    有害垃圾 = 2
    其他垃圾 = 3


def arm_move_to(kind: Kind):
    """ 根据类型，移动到预定位置 """
    if kind is Kind.回收垃圾:
        arm_move(4000, 8000)
    elif kind is Kind.厨余垃圾:
        arm_move(50, 8000)
    elif kind is Kind.有害垃圾:
        arm_move(50, 0)
    elif kind is Kind.其他垃圾:
        arm_move(7000, 50)
    else:
        raise ValueError(f'预定义中不存在[{kind}]值')


def arm_pick_up(rotation: int, height: int | str | float, spread: int = None, *, runtime: float = None) -> float:
    """ 捡起物体
    ## Return
    `consume` - 此次移动耗时 """
    global arm_rotation
    runtime = ttime() if MPU.time is None else MPU.time
    delay = (0.3, 0.4)
    delay_k = 0.3
    delay_ro = abs(rotation - DeviceDriver.arm_rotation)*0.01 #旋转用时
    # 抓
    DeviceDriver.arm_rorate(rotation, runtime=runtime)  # 旋转
    DeviceDriver.arm_claw(100, runtime=runtime+delay_ro)  # 开爪
    DeviceDriver.arm_updown(height, runtime=runtime+delay_k+delay_ro)  # 下落
    # 收
    DeviceDriver.arm_claw(spread, runtime=runtime+sum(delay[:1])+delay_k+delay_ro)  # 抓取
    DeviceDriver.arm_updown('max', runtime=runtime +
                            sum(delay[:2])+delay_k+delay_ro)  # 回升
    consume = sum(delay)+delay_k+delay_ro
    MPU.add_time(consume)
    return consume


def arm_throw_down(rotation: int, kind: Kind, *, runtime: float = None) -> float:
    """ 丢落物体
    ## Return
    `consume` - 此次移动耗时 """
    runtime = ttime() if MPU.time is None else MPU.time
    delay = (0.4, 0.4)
    # 开挡板
    match kind.value:
        case Kind.有害垃圾.value:
            bf0, bf1 = SID.BAFFLE_0, SID.BAFFLE_1
        case Kind.其他垃圾.value:
            bf0, bf1 = SID.BAFFLE_1, SID.BAFFLE_2
        case Kind.厨余垃圾.value:
            bf0, bf1 = SID.BAFFLE_2, SID.BAFFLE_3
        case Kind.回收垃圾.value:
            bf0, bf1 = SID.BAFFLE_3, SID.BAFFLE_0
        case _:
            raise TypeError(f'kind {kind} 类型不符合')
    baffle_set(OPEN, bf0, runtime=runtime)
    baffle_set(OPEN, bf1, runtime=runtime)
    # 丢
    DeviceDriver.arm_rorate(rotation, runtime=runtime)  # 旋转
    DeviceDriver.arm_updown(0, runtime=runtime)  # 下落
    DeviceDriver.arm_claw(100, runtime=runtime+sum(delay[:1]))  # 丢下
    # 收
    DeviceDriver.arm_updown('max', runtime=runtime+sum(delay[:2]))  # 回升
    baffle_set_all(CLOSE, runtime=runtime+sum(delay[:2])+0.3)  # 关挡板
    consume = sum(delay)
    MPU.add_time(consume)
    return consume


def reset_arm(*, runtime: float = None):
    """ 复位机械臂的状态 """
    runtime = ttime() if MPU.time is None else MPU.time
    DeviceDriver.arm_claw(0, runtime=runtime)
    DeviceDriver.arm_rorate(0, runtime=runtime)
    DeviceDriver.arm_updown('max', runtime=runtime)


def reset_move(*, runtime: float = None):
    """ 通过指令让机械臂自动复位到(0,0)坐标 """
    DeviceDriver.arm_move_reset()


def press_cans(n: int = 3, *, runtime: float = None):
    """ 压缩易拉罐 """
    runtime = ttime() if MPU.time is None else MPU.time
    delay = 3
    for i in range(n):
        DeviceDriver.yaso_press(9, 0.5, 0.01, runtime=runtime+delay*i)
        DeviceDriver.yaso_press(0, 0.1, 0.01, runtime=runtime+delay*i+0.3)


def sequence_begin(*, runtime: float = None):
    """ 开始连续操作-默认即刻执行 """
    # MPU.advance_time = time() if runtime is None else runtime
    if runtime is None:
        if MPU.advance_time is None:
            MPU.advance_time = ttime()
        elif MPU.advance_time < ttime():
            MPU.advance_time = ttime()
    else:
        if runtime > MPU.advance_time:
            MPU.advance_time = runtime


def sequence_finish(): ...


def wait_tkinter(test_func=None) -> tk.Tk:
    def func_type(*args, **kwargs):
        print('提示：未定义测试执行函数')
    print(test_func is None)

    def command(event=None, *args, **kwargs):
        if test_func is None:
            func_type()
        else:
            test_func()
    win = tk.Tk()
    win.title('外设测试程序 - ZYF')
    win.wm_attributes('-topmost', 1)  # 置顶
    win.wm_attributes('-toolwindow', 1)  # 工具窗
    W, H = win.winfo_screenwidth(), win.winfo_screenheight()
    w, h = 300, 75
    win.geometry(f'{w}x{h}+{(W-w)//2}+{(H-h)//3}')
    win['bg'] = '#dddddc'
    btn = tk.Button(win, text='退出', fg='gray', font=(
        None, 20, 'bold'), command=win.destroy)
    btn_test = tk.Button(win, text='测试', font=(
        None, 20, 'bold'), command=command)
    btn.place(x=25, y=15, width=100, height=50)
    btn_test.place(x=10+125, y=15, width=150, height=50)
    win.bind('<KeyRelease-space>', command)
    
    win.mainloop()
