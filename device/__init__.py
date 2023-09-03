# %%
from dataclasses import dataclass
from threading import Thread
from time import time, sleep
from platform import platform
from enum import Enum
import math
# %%
from icecream import ic
from serial import Serial
from serial.tools.list_ports import comports
# %%
# ---#

# %%


@dataclass
class OrderCarrier:
    """ 指令载体-结构体 """
    info_content: str = None  # 指令内容
    effective_time: float = None  # 指令生效时刻

# %%


def get_serial() -> Serial:
    """ 根据不同操作系统选择不同串口路径 """
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

# %%


class OrderProcessor:
    """ 指令处理器 """

    def __init__(self, alternator: Serial) -> None:
        """ 指令处理器-构造函数\\
        `alternator` - 串口交流类"""
        self.orders = []
        self.thread = Thread(target=self.target, daemon=True)
        self.thread.start()
        self.alternator = alternator

    def receive(self, info_content: str = None, effective_time: float = time()):
        """ 接收新的指令载体
        `info_content` - 指令内容
        `effective_time` - 指令生效时刻"""
        self.orders.append(OrderCarrier(info_content, effective_time))

    def execute(self, info_content: str):
        """ 向单片机发出指令 """
        self.alternator.write(info_content.encode('utf-8'))

    def target(self):
        """ 循环遍历指令集 """
        while True:
            for carrier in self.orders:
                # 指令休眠结束
                if time() > carrier.effective_time:
                    # 向单片机发出指令
                    self.execute(carrier.info_content)
                    # 执行后删除该指令
                    self.orders.remove(carrier)
                    print(carrier)

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


class Equipment:
    """ 设备控制 """

    def __init__(self, processor: OrderProcessor) -> None:
        self.processor = processor
        self.x ,self.y = 0,0

    def set_baffle(self, status: BS, baffle_id: SID, *, timing: float = time()):
        """ 根据舵机序号，设置挡板状态\\
        ## Parameter 
        `status` -  挡板状态
        `baffle_id` - 舵机ID
        `timing` - 定时时间，默认为即时执行 """
        order = CID.STEERING  # 指令标号
        angle = 100 if status is BS.OPEN else 0  # 预定角度
        info = f'{order.value}{baffle_id.value:02d}:{angle:03d}'  # 信息内容
        self.processor.receive(info)  # 发送信息

    def set_board(self):
        """ 设置底板状态 """
        ...

    def motor_reset(self, *, timing: float = time()):
        """ 通过指令让步进电机复位 """
        self.processor.receive('CALIBRAT',time()+timing)
        
    def motor_move(self,x,y,v=10_000) -> float:
        """ 返回移动所耗时间 
        ## Parameter
        `x` - 坐标x
        `y` - 坐标y
        `v` - 移动速度
        ## Return
        `consume` - 此次移动耗时"""
        order = CID.STEPPING  # 指令标号
        info = f'{order.value}{x}:{y}:{v}'
        self.processor.receive(info)
        
        #计算时间
        #v_bar = (200+v)//2
        consume = (math.sqrt((self.x-x)**2+(self.y-y)**2))/v
        self.x,self.y = x,y
        return consume


# %%
if __name__ == '__main__':
    ser = get_serial()
    a = OrderProcessor(ser)
    e = Equipment(a)
    #e.set_baffle(BS.OPEN, SID.BAFFLE_1)
    print('time_use',e.motor_move(2000,2000))
    e.motor_reset(timing=5)

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
