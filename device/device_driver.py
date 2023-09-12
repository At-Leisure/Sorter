""" 设备驱动-硬件 """

# 内置拓展模块
from threading import Thread
from time import time, sleep
from platform import platform
from enum import Enum
from dataclasses import dataclass
from inspect import isfunction, isclass
from math import *
# 第三方拓展库
from icecream import ic
from serial import Serial
from serial.tools.list_ports import comports
# 自定义拓展库
from .tools import *


@dataclass
class OrderCarrier:
    """ 指令载体-结构体 """
    info_content: str = None  # 指令内容
    effective_time: float = None  # 指令生效时刻


class OrderProcessor(metaclass=NamespaceMeta):
    """ 命名空间 - 指令处理器 """
    orders = []  # 指令容器
    alternator = None
    motor_cache = None

    @classmethod
    def connect(cls) -> None:
        """ 指令处理器-构造函数\\
        `alternator` - 串口交流类"""
        cls.alternator = get_serial()
        print(cls.alternator)
        cls.thread = Thread(target=cls.target, name='指令处理器', daemon=True)
        cls.thread.start()

    @classmethod
    def receive(cls, info_content: str = None, effective_time: float = None):
        """ 接收新的指令载体
        `info_content` - 指令内容
        `effective_time` - 指令生效时刻"""
        assert not cls.alternator is None, '[指令处理器]串口尚未连接，不能传输信息'
        cls.orders.append(OrderCarrier(info_content, effective_time))

    @classmethod
    def execute(cls, info_content: str):
        """ 向单片机发出指令 """
        cls.alternator.write(info_content.encode('utf-8'))

    @classmethod
    def target(cls):
        """ 循环遍历指令集 """
        while True:
            for carrier in cls.orders:
                # 指令休眠结束
                # 生效时刻为空则默认立即执行，并且不会继续执行（time() > carrier.effective_time）语句
                # 生效时刻超过当前时刻就立即执行
                if carrier.effective_time is None or time() > carrier.effective_time:
                    # 向单片机发出指令
                    cls.execute(carrier.info_content)
                    # 执行后删除该指令
                    cls.orders.remove(carrier)
                    print(carrier, len(cls.orders))
                    sleep(0.005)  # 延时防止两次指令间隔时间太短导致的指令无效


    @classmethod
    @property
    def motor_usedtime(cls):
        return cls.motor_cache


class DeviceDriver(metaclass=NamespaceMeta):
    """ 命名空间 - 外设驱动 - 初步封装 """
    height_max = 110  # 爪子最大高度
    yaso_max = 10  # 压缩最大弧度
    x_max = 7000
    y_max = 7500
    v_max = 13_000

    @classmethod
    def connect(cls) -> None:
        OrderProcessor.connect()
        cls.processor = OrderProcessor

    # %% steer

    @classmethod
    def steer_set(cls, sid: SID, value: int, *, runtime: float = None):
        """ 设置舵机状态 \\
        ## Parameter 
        `status` -  挡板状态
        `baffle_id` - 舵机ID
        `runtime` - 定时时间，默认为即时执行 """
        match sid:
            case SID.BAFFLE_0 | SID.BAFFLE_1 | SID.BAFFLE_2 | SID.BAFFLE_3:
                assert 0 <= value <= 100, f'挡板[{sid.value}]的值[{value}]非法'
            case SID.ARM_UPDOWN_0 | SID.ARM_UPDOWN_1:
                assert 0 <= value <= cls.height_max, f'伸缩值非法'
            case SID.ARM_ROTATE:
                assert 0 <= value <= 170, f'旋转值非法'

        OrderProcessor.receive(
            f'{CID.STEERING.value}:{sid.value:02d}:{value:03d}', runtime)

    @classmethod
    def board_rotate(cls, rotation: int = None,  *, runtime: float = None):
        """ 设置底板状态 
        `rotation` - 顺时针-水平旋转角度"""
        if not rotation is None:
            cls.steer_set(SID.BOARD_HR, rotation+50, runtime=runtime)  # 旋转

    @classmethod
    def board_slope(cls, slope: int = None, *, runtime: float = None):
        """ 设置底板状态 
        `slope` - 顺时针-垂直倾斜角度"""
        if not slope is None:
            cls.steer_set(SID.BOARD_VT, slope+50, runtime=runtime)  # 倾斜

    # %% arm

    @classmethod
    def arm_move(cls, x, y, v, *, runtime: float = None):
        """ 设置步进电机 """
        assert 0 <= x <= cls.x_max, 'X坐标值非法'
        assert 0 <= y <= cls.y_max, 'Y坐标值非法'
        assert 1000 <= v <= cls.v_max, 'V速度值非法'
        OrderProcessor.receive(
            f'{CID.STEPPING.value}:{x}:{y}:{v}', runtime)

    @classmethod
    def arm_move_reset(cls, *, runtime: float = None):
        OrderProcessor.receive('CALIBRAT')

    @classmethod
    def arm_updown(cls, height: int | str | float, *, runtime: float = None):
        """ 控制上下高度
        `height` - 爪子并拢时距离底板的高度 """
        if isinstance(height, int):
            value = height
        elif isinstance(height, float):
            value = int((height - int(height)) * cls.height_max)
        elif height == 'max':
            value = cls.height_max
        cls.steer_set(SID.ARM_UPDOWN_0, value, runtime=runtime)
        cls.steer_set(SID.ARM_UPDOWN_1, value, runtime=runtime)

    @classmethod
    def arm_rorate(cls, rotation: int, *, runtime: float = None):
        """ 控制旋转角度 
        `rotation` - 水平旋转角度"""
        cls.steer_set(SID.ARM_ROTATE, rotation, runtime=runtime)

    @classmethod
    def arm_claw(cls, closing: int, *, runtime: float = None):
        """ 控制爪子的张角大小
        `closing` - 爪子闭合幅度 """
        cls.steer_set(SID.ARM_CLAW, 100-closing, runtime=runtime)

    # %% 压缩(亚索yaso)

    @classmethod
    def yaso_press(cls, target: float, torsion: float, damp: float, *, runtime: float = None, ignore_assert: bool = False):
        """ 设置宇树电机
        `target` - 目标位置，调节缩进距离，推进板距离推进终点板的距离，单位cm
        `torsion` - 位置系数，调节推进扭力
        `damp` - 阻尼系数，调节减速阻力"""
        if not ignore_assert:
            assert 0 <= target <= cls.yaso_max, '缩进距离值非法'
            assert 0 <= torsion <= 1, '扭力系数值非法'
            assert 0 <= damp <= 1, '阻尼系数值非法'
        # 将推进距离转化为转动弧度
        angle = -target
        OrderProcessor.receive(
            f'{CID.UNITREE.value}:{angle}:{torsion}:{damp}', runtime)
