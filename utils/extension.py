""" 拓展类集合 """


import serial  # 调用串口
from serial.tools.list_ports import comports
import sys
import time
from threading import Thread
import json
from function import os_name
from deco import asEnumClass

""" 串口使用示例
import serial

# 打开串口
serial_port = "COM1"  # 串口名称（根据实际情况修改）
baud_rate = 9600  # 波特率（根据实际情况修改）
ser = serial.Serial(serial_port, baud_rate)

# 发送数据
data_to_send = b"Hello, World!"  # 要发送的数据
ser.write(data_to_send)

# 接收数据
received_data = ser.read(10)  # 读取 10 个字节的数据
print("Received data:", received_data)

# 关闭串口
ser.close() """

# 枚举
@asEnumClass()
class ServoId:
    #挡板-0,1,2,3
    BAFFLE_0,BAFFLE_1,BAFFLE_2,BAFFLE_4 = range(4)
    #底板-水平,垂直
    BOARD_VT,BOARD_HR = range(4,6)
    #压缩(亚索yaso)出口,YASO_EXIT
    range(6,8)
    #机械臂上下-1,2，机械臂旋转，机械爪
    ARM_UPDOWN_0,ARM_UPDOWN_1,ARM_ROTATE,ARM_CLAW  = range(8,12)



class SerialMotor:
    """ 封装串口 """

    def __init__(self) -> None:
        self.commands_ = []  # 指令队列
        self.serobj_ = None
        # 串口对象
        try:
            print(*comports())
            if os_name() == "Windows":
                self.serobj_ = serial.Serial(
                    str(comports()[0]).split()[0], 100_0000)
            elif os_name() == 'Linux':
                self.serobj_ = serial.Serial(comports()[0], 100_0000)
            else:
                raise OSError()
        except OSError:
            class SerNone:
                pass
            self.serobj_ = SerNone()
            setattr(self.serobj_, "write", lambda s: print(f'串口未连接 {s}'))
            setattr(self.serobj_, "close", lambda s: print(f'串口未连接 {s}'))

    def deinit(self):
        """ 析构函数 """
        self.serobj_.close()

    def append(self, cmd: str):
        """ 追加新指令 """
        self.commands_.append(cmd)

    def __send(self):
        """ 从队列中拿出一个指令，向串口发送该指令 """
        if len(self.commands_) == 0:
            print('暂无可发送的指令')
            return
        ...

    def run(self):
        while True:
            for cmd in self.commands_:
                if cmd[0]=='0':
                    ...


class ServoMotor:
    """ 舵机-基类 """

    def __init__(self, *, serial_id: int = None, serial_object: SerialMotor = None, max_value: int = None, min_value: int = None, initial_value: int = None) -> None:
        """ 舵机-初始化
        ## Parameter
        `serial_id` - 串口信息id
        `serial_object` - 串口对象
        `max_value` - 发送最大值
        `min_value` -发送最小值
        `initial_value` - 初始设置值
        ## Example
        >>> a = ServoMotor(serial_id=0, serial_object=ser, max_value=100, min_value=0, initial_value=50)"""

        # 检查错误
        assert isinstance(serial_id, int), f'设备id只能为int类型'
        assert min_value <= max_value, f'最大值不能小于最小值'
        assert min_value <= initial_value <= max_value, f'初始值不能超出预定范围'

        # 赋初始值
        self.id_ = serial_id
        self.sermtr_ = serial_object
        self.max_ = max_value
        self.min_ = min_value
        self.value_ = initial_value

        # 初始化外设
        self.__execute_device()

    def show_info(self):
        print(
            f"""ServoMotor{{ id:{self.id}, max:{self._max_v}, min:{self._min_v}, current:{self.current_v}  }}""")

    def __execute_device(self):
        """ 私有方法，发出串口指令，驱动外设 """
        s = f'{0}{self.id}:{self.value_}'
        print('send', s)
        self.sermtr_.append(s)

    def rotate_to(self, v):
        assert self._min_v <= v <= self._max_v, f'ServoMotor: 赋值不在合理范围，{v} 不在 {[self._min_v,self._max_v]} 区间'
        self.current_v = v
        self.__execute_device()


class PlaneMotor:
    """ 平面移动-基类 """

    def __init__(self, *, serial_object: SerialMotor = None, max_x: int = None, max_y: int = None, min_v: int = None, max_v: int = None, reset=True) -> None:
        """  """

        # 赋初始值
        self.sermtr_ = serial_object
        self.x_max_ = max_x
        self.y_max_ = max_y
        self.x = 0  # 坐标x
        self.y = 0  # 坐标y
        self.v = 0  # 速度v

        # 初始复位
        if reset:
            self.call_reset()

        # 初始化外设
        self.__execute_device()

    def call_reset(self):
        """ 发送指令复位 """
        self.sermtr_.append('复位指令')

    def __execute_device(self):
        """ 私有方法，发送串口指令 """
        s = f'{1}{self.x}:{self.y}:{self.v}'
        print('[CMD]', s)
        self.sermtr_.append(s)

    def move_to(self, *, x, y, v):
        assert self._min_x <= x <= self._max_x, f'PlaneSystem: 赋值不在合理范围，x={x} 不在 {[self._min_x,self._max_x]} 区间'
        assert self._min_y <= y <= self._max_y, f'PlaneSystem: 赋值不在合理范围，y={y} 不在 {[self._min_y,self._max_y]} 区间'
        assert self._min_v <= v <= self._max_v, f'PlaneSystem: 赋值不在合理范围，v={v} 不在 {[self._min_v,self._max_v]} 区间'
        self.x = x
        self.y = y
        self.v = v
        self.__execute_device()


if __name__ == '__main__':
    print(*comports())
    if os_name() == "Windows":
        ser = serial.Serial(
            str(comports()[0]).split()[0], 100_0000)
    elif os_name() == 'Linux':
        ser = serial.Serial(comports()[0], 100_0000)
    else:
        raise OSError()

    ser.write(f'0{ServoId.ARM_UPDOWN_0}:0'.encode('utf8'))