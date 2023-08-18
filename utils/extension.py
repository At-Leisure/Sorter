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


@asEnumClass()
class OrderID:
    """ 指令序号枚举 """
    # 舵机，步进电机，压缩装置
    SERVO, PLANE, PRESS = range(3)


@asEnumClass()
class ServoID:
    """ 舵机序号枚举 """
    # 挡板-0,1,2,3
    BAFFLE_0, BAFFLE_1, BAFFLE_2, BAFFLE_3 = range(4)
    # 底板-水平,垂直
    BOARD_VT, BOARD_HR = range(4, 6)
    # 压缩(亚索yaso)出口,YASO_EXIT
    range(6, 8)
    # 机械臂上下-1,2，机械臂旋转，机械爪
    ARM_UPDOWN_0, ARM_UPDOWN_1, ARM_ROTATE, ARM_CLAW = range(8, 12)


class SerialMotor(serial.Serial):
    """ 封装串口 """

    def __init__(self, port: str, rate: int = 100_0000, *args, **kwargs) -> None:
        """ 封装串口的使用
        ## Parameter
        `port` - 串口号
        `rate` - 波特率
        ## Example
        >>> smt = SerialMotor("COM3",152000) #创建对象
        >>> smt.append_string('information') #发送字符串"""

        serial.Serial.__init__(self, port, rate, *args, **kwargs)
        self.send_list_ = []  # 发送队列 [(指令,时间戳),...]
        self.gain_list_ = []  # 接受队列 [(指令,时间戳),...]
        self.serobj_ = None

        # 开启线程-时刻监听串口输入信号，子线程随主线程结束而结束
        self.thread = Thread(target=self.__run, daemon=True, name='监听串口')
        self.thread.start()

    def deinit(self):
        """ 析构函数 """
        self.serobj_.close()

    def append_string(self, cmd: str):
        """ 追加新指令 """
        self.send_list_.append((cmd, time.time()))  # 给添加的指令附加一个时间戳

    def __run(self):
        """ 不断监听从串口发向主机的信号 """
        while True:
            # 监听信号
            gain_string = self.read_all().decode('utf-8')  # 接收来自单片机的信息
            if gain_string != '':  # 如果收到信号
                time_tick = time.time()
                self.gain_list_.append(
                    (gain_string, time_tick))  # 给添加的指令附加一个时间戳
                print(
                    f'GAIN {{tick: {time_tick:16.5f}, string: {gain_string}}}')
                
                # 提示容器存量，防止未进行清理容器
                print(f'INFO container{{tosend: {len(self.send_list_)}, gained: {len(self.gain_list_)}}}\n')
                
            #处理积存的接受单片机的信息

            #发送信号
            # 处理积存的发向单片机的信息，从队列中拿出指令，向串口发送该指令
            delete_list = [] #此次需要清除的发送指令
            for string, tick in self.send_list_:
                if len(self.send_list_):  # 存在积存的信号
                    # 判断指令类型
                    if string[0] == str(OrderID.SERVO):  # 0-舵机
                        time.sleep(0.01)#延时0.01s后直接发送
                        delete_list.append(self.send_list_.index((string, tick)))#将该指令对应的下标加入清除列表
                        print(f'SEND {{tick: {tick:16.5f}, string: {string}}}')
                        self.write(string.encode('utf8'))
                    elif string[0] == str(OrderID.PLANE):  # 1-电机
                        ...
                    elif string[0] == str(OrderID.PRESS):  # 2-压缩
                        ...
                    else:
                        pass
                    
                    # 提示容器存量，防止未进行清理容器
                    print(f'INFO container{{tosend: {len(self.send_list_)}, gained: {len(self.gain_list_)}}}\n')
                    
            #保证前面的下标不变，进行从后往前清除使用过的指令
            for i in sorted(delete_list,reverse=True):#从小到大排序
                print(i)
                self.send_list_.pop(i)#从后往前删除
                
            
            # 延时，等待下一次信息
            time.sleep(0.001)
            
            



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
        ser_port = str(comports()[0]).split()[0]
    elif os_name() == 'Linux':
        ser_port = comports()[0]
    else:
        raise OSError()

    smt = SerialMotor(ser_port)
    
    smt.append_string(f'{OrderID.SERVO}{ServoID.BAFFLE_0}:0')
    smt.append_string(f'{OrderID.SERVO}{ServoID.BAFFLE_1}:0')
    smt.append_string(f'{OrderID.SERVO}{ServoID.BAFFLE_2}:0')
    smt.append_string(f'{OrderID.SERVO}{ServoID.BAFFLE_3}:0')

    time.sleep(1)
    
    smt.append_string(f'{OrderID.SERVO}{ServoID.BAFFLE_0}:100')
    smt.append_string(f'{OrderID.SERVO}{ServoID.BAFFLE_1}:100')
    smt.append_string(f'{OrderID.SERVO}{ServoID.BAFFLE_2}:100')
    smt.append_string(f'{OrderID.SERVO}{ServoID.BAFFLE_3}:100')
    
    time.sleep(1)
    
    smt.append_string(f'{OrderID.SERVO}{ServoID.BAFFLE_0}:0')
    smt.append_string(f'{OrderID.SERVO}{ServoID.BAFFLE_1}:0')
    smt.append_string(f'{OrderID.SERVO}{ServoID.BAFFLE_2}:0')
    smt.append_string(f'{OrderID.SERVO}{ServoID.BAFFLE_3}:0')

    time.sleep(1)
    
    smt.append_string(f'{OrderID.SERVO}{ServoID.BAFFLE_0}:100')
    smt.append_string(f'{OrderID.SERVO}{ServoID.BAFFLE_1}:100')
    smt.append_string(f'{OrderID.SERVO}{ServoID.BAFFLE_2}:100')
    smt.append_string(f'{OrderID.SERVO}{ServoID.BAFFLE_3}:100')
    
    time.sleep(1)
    smt.write(b'CALIBRAT')
    time.sleep(1)
    smt.write(b'12000:2000:5000')
    time.sleep(5)
