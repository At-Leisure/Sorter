""" 命名空间 - 分拣操作API - 高层封装  """

from time import time

from .tools import *
from .device_driver import DeviceDriver

OPEN, CLOSE = 1, 0


class ModulePropertyUnit:
    """ API模块属性量 """
    advance_time = None
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


def arm_move(x, y, v=10_000, *, runtime: float = None):
    """ 返回移动所耗时间 
    ## Parameter
    `x` - 坐标x
    `y` - 坐标y
    `v` - 移动速度
    ## Return
    `consume` - 此次移动耗时"""
    runtime = time() if MPU.time is None else MPU.time
    
    DeviceDriver.arm_move(x, y, v, runtime=runtime)

    consume = (abs(MPU.x -x)+abs(MPU.y-y))/v+2
    MPU.add_time(consume)

    MPU.x = x
    MPU.y = y
    


def arm_pick_up(rotation: int, height: int | str | float, spread: int = None, *, runtime: float = None) -> float:
    """ 捡起物体
    ## Return
    `consume` - 此次移动耗时 """
    runtime = time() if MPU.time is None else MPU.time
    delay = (0.4, 0.4)
    # 抓
    DeviceDriver.arm_rorate(rotation, runtime=runtime)  # 旋转
    DeviceDriver.arm_updown(height, runtime=runtime)  # 下落
    DeviceDriver.arm_claw(100, runtime=runtime)  # 开爪
    # 收
    DeviceDriver.arm_claw(spread, runtime=runtime+sum(delay[:1]))  # 抓取
    DeviceDriver.arm_updown('max', runtime=runtime+sum(delay[:2]))  # 回升
    consume = sum(delay)
    MPU.add_time(consume)
    return consume


def arm_throw_down(*, runtime: float = None) -> float:
    """ 丢落物体
    ## Return
    `consume` - 此次移动耗时 """
    runtime = time() if MPU.time is None else MPU.time
    delay = (0.4, 0.4)
    # 丢
    DeviceDriver.arm_updown(0, runtime=runtime)  # 下落
    DeviceDriver.arm_claw(100, runtime=runtime+sum(delay[:1]))  # 丢下
    # 收
    DeviceDriver.arm_updown('max', runtime=runtime+sum(delay[:2]))  # 回升
    consume = sum(delay)
    MPU.add_time(consume)
    return consume


def reset_arm(*, runtime: float = None):
    """ 复位机械臂的状态 """
    runtime = time() if MPU.time is None else MPU.time
    DeviceDriver.arm_claw(0,runtime=runtime)
    DeviceDriver.arm_rorate(0,runtime=runtime)
    DeviceDriver.arm_updown('max',runtime=runtime)
    
def reset_move(*, runtime: float = None):
    """ 通过指令让机械臂自动复位到(0,0)坐标 """
    DeviceDriver.arm_move_reset()


def sequence_begin(*, runtime: float = None):
    """ 开始连续操作-默认即刻执行 """
    MPU.advance_time = time() if runtime is None else runtime


def sequence_finish():
    MPU.advance_time = None
