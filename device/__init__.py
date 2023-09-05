""" 应用程序接口-API """
# API-应用程序与外设驱动的桥梁
# 目录包含顺序: {(API): (tools, device_driver); device_driver: (tools)}
from time import time

from .tools import *
from .device_driver import DeviceDriver

OPEN, CLOSE = 1, 0


class SorterAPI(metaclass=NamespaceMeta):
    """ 命名空间 - 分拣操作API - 高层封装  """
    advance_time = None
    driver = None
    x, y = 0, 0

    @classmethod
    def init(cls):
        """ 初始化连接， """
        DeviceDriver.connect()
        cls.driver = DeviceDriver

    @classmethod
    def baffle_set(cls, status: bool, sid: SID, *, runtime: float = None):
        """ 设置挡板 """
        DeviceDriver.steer_set(
            sid, 0 if status == CLOSE else 100, runtime=runtime)

    @classmethod
    def baffle_set_all(cls, status: bool, *, runtime: float = None):
        """ 设置挡板 """
        value = 0 if status == CLOSE else 100
        DeviceDriver.steer_set(SID.BAFFLE_0, value, runtime=runtime)
        DeviceDriver.steer_set(SID.BAFFLE_1, value, runtime=runtime)
        DeviceDriver.steer_set(SID.BAFFLE_2, value, runtime=runtime)
        DeviceDriver.steer_set(SID.BAFFLE_3, value, runtime=runtime)

    @classmethod
    def arm_move(cls, x, y, v=10_000, *, runtime: float = None):
        """ 返回移动所耗时间 
        ## Parameter
        `x` - 坐标x
        `y` - 坐标y
        `v` - 移动速度
        ## Return
        `consume` - 此次移动耗时"""
        DeviceDriver.arm_move(x, y, v, runtime=runtime)

        cls.x = x
        cls.y = y

    @classmethod
    def arm_pick_up(cls, rotation: int, height: int | str | float, spread: int = None, *, runtime: float = None) -> float:
        """ 捡起物体
        ## Return
        `consume` - 此次移动耗时 """
        runtime = time() if runtime is None else runtime
        # 下落
        DeviceDriver.arm_rorate(rotation, runtime=runtime)
        DeviceDriver.arm_updown(height, runtime=runtime)
        DeviceDriver.arm_claw(100, runtime=runtime)
        # 抓取
        delay = (0.4, 0.4)
        DeviceDriver.arm_claw(spread, runtime=runtime+sum(delay[:1]))
        # 回升
        DeviceDriver.arm_updown('max', runtime=runtime+sum(delay[:2]))
        consume = sum(delay)
        return consume

    @classmethod
    def arm_throw_down(cls, *, runtime: float = None) -> float:
        """ 丢落物体
        ## Return
        `consume` - 此次移动耗时 """
        runtime = time() if runtime is None else runtime
        DeviceDriver.arm_updown(0, runtime=runtime)  # 下落
        delay = (0.4, 0.4)
        DeviceDriver.arm_claw(100, runtime=runtime+sum(delay[:1]))  # 丢下
        DeviceDriver.arm_updown('max', runtime=runtime+sum(delay[:2]))  # 回升
        consume = sum(delay)
        return consume

    @classmethod
    def reset_arm(cls, *, runtime: float = None):
        """ 复位机械臂的状态 """
        DeviceDriver.arm_claw(0)
        DeviceDriver.arm_rorate(0)
        DeviceDriver.arm_updown('max')
