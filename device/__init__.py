# %% 内置拓展模块
from dataclasses import dataclass
from threading import Thread
from time import time, sleep
from platform import platform
from enum import Enum
from inspect import isfunction, isclass
import math
# %% 第三方拓展库
from icecream import ic
from serial import Serial
from serial.tools.list_ports import comports
# %% 自定义拓展库
#

# %%


class NamespaceMeta(type):
    """ 通过元类(元类须派生于type)使派生类限制为命名空间，派生类具备以下特征
    - 不需要生成实例
    - 有内部状态变量
    - 方法都是类方法"""
    def __new__(cls, name: str, bases: tuple[type], attrs: dict[str, type]):
        """ cls代表动态修改的类
        name代表动态修改的类名
        bases代表被动态修改的类的所有父类
        attr代表被动态修改的类的所有属性、方法组成的字典 """
        # 不需要生成实例 - 修改类名的new方法
        def limited_new(cls, *args, **kwargs):
            raise TypeError('命名空间不需要实例化')
        attrs['__new__'] = limited_new

        # 方法都是类方法 - 将方法都改为类方法
        for key, value in attrs.items():
            if isfunction(value):
                attrs[key] = classmethod(value)
            if key == '__init__':
                raise TypeError('命名空间不需要实例化')
            print(key)
        # 返回修改好的类名
        return super().__new__(cls, name, bases, attrs)


# %%


@dataclass
class OrderCarrier:
    """ 指令载体-结构体 """
    info_content: str = None  # 指令内容
    effective_time: float = None  # 指令生效时刻

# %%


def get_serial() -> Serial:
    """ 根据不同操作系统选择不同串口路径 """
    try:
        port = comports()[0]
        """(f"设备名称：{port.device}")
        (f"描述：{port.description}")
        (f"制造商：{port.manufacturer}")
        (f"硬件ID：{port.hwid}") """
        match platform().split('-')[0]:
            case 'Windows':
                ser = Serial(port.device, 100_0000)
            case 'Linux':
                ...
        return ser
    except:
        class NoneSer:
            def write(self, s): print('警告：串口未连接')
        return NoneSer()

# %%


class OrderProcessor(metaclass=NamespaceMeta):
    """ 命名空间 - 指令处理器 """
    orders = []  # 指令容器

    def connect(cls, alternator: Serial) -> None:
        """ 指令处理器-构造函数\\
        `alternator` - 串口交流类"""
        cls.alternator = alternator
        cls.thread = Thread(target=cls.target, daemon=True)
        cls.thread.start()

    def receive(cls, info_content: str = None, effective_time: float = time()):
        """ 接收新的指令载体
        `info_content` - 指令内容
        `effective_time` - 指令生效时刻"""
        cls.orders.append(OrderCarrier(info_content, effective_time))

    def execute(cls, info_content: str):
        """ 向单片机发出指令 """
        cls.alternator.write(info_content.encode('utf-8'))

    def target(cls):
        """ 循环遍历指令集 """
        while True:
            for carrier in cls.orders:
                # 指令休眠结束
                if time() > carrier.effective_time:
                    # 向单片机发出指令
                    cls.execute(carrier.info_content)
                    # 执行后删除该指令
                    cls.orders.remove(carrier)
                    print(carrier, len(cls.orders))

# %%


class CommandID(Enum):
    """ 命令标号，舵机，步进，宇树 """
    STEERING, STEPPING, UNITREE = range(3)


CID = CommandID


class SteeringID(Enum):
    """ 挡板标号，挡板0-3 """
    BAFFLE_0, BAFFLE_1, BAFFLE_2, BAFFLE_3 = range(4)


SID = SteeringID


class BaffleStatus(Enum):
    """ 挡板状态 """
    CLOSE, OPEN = range(2)


BS = BaffleStatus

# %%


class Equipment(metaclass=NamespaceMeta):
    """ 命名空间 - 设备控制 """
    x, y = 0, 0

    def connect(cls, processor: OrderProcessor) -> None:
        cls.processor = processor

    def set_baffle(cls, status: BS, baffle_id: SID, *, timing: float = time()):
        """ 根据舵机序号，设置挡板状态\\
        ## Parameter 
        `status` -  挡板状态
        `baffle_id` - 舵机ID
        `timing` - 定时时间，默认为即时执行 """
        order = CID.STEERING  # 指令标号
        angle = 100 if status is BS.OPEN else 0  # 预定角度
        info = f'{order.value}{baffle_id.value:02d}:{angle:03d}'  # 信息内容
        cls.processor.receive(info)  # 发送信息

    def set_board(cls):
        """ 设置底板状态 """
        ...

    def motor_reset(cls, *, timing: float = time()):
        """ 通过指令让步进电机复位 """
        cls.processor.receive('CALIBRAT', time()+timing)

    def motor_move(cls, x, y, v=10_000, *, timing=time()) -> float:
        """ 返回移动所耗时间 
        ## Parameter
        `x` - 坐标x
        `y` - 坐标y
        `v` - 移动速度
        ## Return
        `consume` - 此次移动耗时"""
        order = CID.STEPPING  # 指令标号
        info = f'{order.value}{x}:{y}:{v}'
        cls.processor.receive(info, timing)

        # 计算时间 TODO
        #
        # v_bar = (200 + v)/2
        # t = s/v
        #
        v_bar = (200+v)/2
        s = int(math.sqrt((cls.x-x)**2+(cls.y-y)**2))  # 脉冲数
        consume = s/v_bar
        # 更新状态
        cls.x, cls.y = x, y
        return consume


# %%
if __name__ == '__main__':
    ser = get_serial()
    OrderProcessor.connect(ser)
    Equipment.connect(OrderProcessor)
    e = Equipment
    # e.set_baffle(BS.OPEN, SID.BAFFLE_1)
    t = e.motor_move(5000, 5000, 5000, timing=time()+2)
    print(f'time_use {t} 秒')
    e.motor_move(0, 0, timing=time()+t+2)
    # e.motor_reset(timing=5)

    # 等待结束
    import tkinter as tk
    win = tk.Tk()
    win.title('外设测试程序 - ZYF')
    W, H = win.winfo_screenwidth(), win.winfo_screenheight()
    w, h = 300, 75
    win.geometry(f'{w}x{h}+{(W-w)//2}+{(H-h)//3}')
    win['bg'] = '#dddddc'
    btn = tk.Button(win, text='结束运行', font=(
        None, 20, 'bold'), command=win.destroy)
    btn.place(x=50, y=15, width=200, height=50)
    win.mainloop()
