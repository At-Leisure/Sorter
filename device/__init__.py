# %%
from dataclasses import dataclass
from threading import Thread
from time import time, sleep
from platform import platform
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
    effective_time: float = None  # 指令生效时刻
    info_content: str = None  # 指令内容

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
            ser = Serial(port.device,100_0000)
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

    def receive(self, order: OrderCarrier):
        """ 接收新的指令载体 """
        self.orders.append(order)

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
                    print(time())


# %%
if __name__ == '__main__':
    ser = get_serial()
    a = OrderProcessor(ser)
    
    a.receive(OrderCarrier(time()+1,'001:0'))
    print(time())
    
    input(f'{"="*20}输入回车，结束运行{"="*20}\n')
    
