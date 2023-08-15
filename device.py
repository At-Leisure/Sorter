""" 外设控制 """
import serial  # 调用串口
from serial.tools.list_ports import comports
import sys

assert len(comports()),sys.exit(print('未检测到串口'))
ser = serial.Serial(port="COM3", baudrate= 115200)#创建串口对象
assert ser.is_open(),'串口未连接'

class BasicServoMotor:
    """ 舵机-基类 """

    def __init__(self, min_value, max_value, initial_value=None, *, id_=None) -> None:
        assert isinstance(id_, int), f'设备id设置非法'
        assert min_value < max_value, f'赋值顺序错误，请尝试改为 ServoMotor{(max_value,min_value)}'
        self.id = id_
        self._min_v = min_value
        self._max_v = max_value
        if isinstance(initial_value, type(None)):
            self.current_v = min_value
        else:
            assert min_value < initial_value < max_value, f'初始值不合规，合理范围为{[min_value,max_value]}'
            self.current_v = initial_value
        self.__execute_device()  # 初始化外设

    def show_info(self):
        print(
            f"""ServoMotor{{ id:{self.id}, max:{self._max_v}, min:{self._min_v}, current:{self.current_v}  }}""")

    def __execute_device(self):
        """ 私有方法，不允许外部调用\n
        TODO 发出串口指令，驱动外设 """
        s = f'<C>{self.id}:{self.current_v}<D>'
        print('send', s)
        ser.write(s.encode('utf-8'))

    def set_value(self, v):
        assert self._min_v < v < self._max_v, f'ServoMotor: 赋值不在合理范围，{v} 不在 {[self._min_v,self._max_v]} 区间'
        self.current_v = v
        self.__execute_device()


class PlaneSystem:
    """ 平面移动-基类 """

    def __init__(self, max_x, max_y, max_v) -> None:
        self.current_x = 0
        self.current_y = 0
        self.current_v = 0
        self._min_x = 0
        self._min_y = 0
        self._min_v = 0
        self._max_x = max_x
        self._max_y = max_y
        self._max_v = max_v
        self.__execute_device()  # 初始化外设

    def show_info(self):
        print(
            f"PlaneSystem{{ x:{{min:{self._max_x}, max:{self._max_x}, current:{self.current_x}}}}}\n"
            + f"           {{ y:{{min:{self._max_y}, max:{self._max_y}, current:{self.current_y}}}}}")

    def __execute_device(self):
        """ 私有方法，不允许外部调用\n
        TODO 发出串口指令，驱动外设 """
        s = f'<C>{self.current_x}:{self.current_y}:{self.current_v}<D>'
        print('send',s)
        ser.write(s.encode('utf-8'))

    def set_value(self, *, x, y, v):
        assert self._min_x < x < self._max_x, f'PlaneSystem: 赋值不在合理范围，x={x} 不在 {[self._min_x,self._max_x]} 区间'
        assert self._min_y < y < self._max_y, f'PlaneSystem: 赋值不在合理范围，y={y} 不在 {[self._min_y,self._max_y]} 区间'
        assert self._min_v < v < self._max_v, f'PlaneSystem: 赋值不在合理范围，v={v} 不在 {[self._min_v,self._max_v]} 区间'
        self.current_x = x
        self.current_y = y
        self.current_v = v
        self.__execute_device()


if __name__ == '__main__':
    a = BasicServoMotor(1, 20, 15, id_=0)
    b = PlaneSystem(4000, 4000, 500)

    a.set_value(5)
    b.set_value(x=5, y=5, v=50)

    a.show_info()
    b.show_info()
