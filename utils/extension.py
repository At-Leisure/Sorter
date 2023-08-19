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
        self.gain_list_ = [('PMOR', 0)]  # 接受队列 [(指令,时间戳),...]
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
            # 发送信号 - 处理积存的发向单片机的信息，从队列中拿出指令，向串口发送该指令
            delete_list = []  # 此次需要清除的发送指令
            for string, tick in self.send_list_:
                if len(self.send_list_):  # 存在积存的信号
                    # 判断指令类型
                    if string[0] == str(OrderID.SERVO):  # 0-舵机
                        time.sleep(0.01)  # 延时0.01s后直接发送
                        delete_list.append(self.send_list_.index(
                            (string, tick)))  # 将该指令对应的下标加入清除列表
                        print(f'SEND {{tick: {tick:16.5f}, string: {string}}}')
                        self.write(string.encode('utf8'))

                    elif string[0] == str(OrderID.PLANE):  # 1-电机
                        # 在接收列表中查找是否有移动完成回馈，并采用最近一次的完成反馈
                        can_move = False
                        for s, t in reversed(self.gain_list_):
                            if s == 'PMOR':
                                can_move = True
                                break  # 只用最近的反馈
                        if can_move:
                            time.sleep(0.01)  # 延时0.01s后直接发送
                            delete_list.append(self.send_list_.index(
                                (string, tick)))  # 将该指令对应的下标加入清除列表
                            print(
                                f'SEND {{tick: {tick:16.5f}, string: {string}}}')
                            self.write(string.encode('utf8'))

                            # 清除电机的所有完成反馈
                            self.gain_list_ = [
                                (s, t) for s, t in self.gain_list_ if s != 'PMOR']

                        break  # 一次仅允许执行一次关于电机的指令

                    elif string[0] == str(OrderID.PRESS):  # 2-压缩
                        ...

                    else:  # 复位或其他，直接发送
                        delete_list.append(self.send_list_.index(
                            (string, tick)))  # 加入清除列表
                        print(
                            f'SEND {{tick: {tick:16.5f}, string: {string}}}')
                        self.write(string.encode('utf8'))

                    # 提示容器存量，防止未进行清理容器
                    print(
                        f'SEND - INFO container{{tosend: {len(self.send_list_)}, gained: {len(self.gain_list_)}}}\n')
                    print(
                        f'SEND - INFO send:{[s for s,t in self.send_list_]}, gain:{[s for s,t in self.gain_list_]}')

            # 保证前面的下标不变，进行从后往前清除使用过的指令
            for i in sorted(delete_list, reverse=True):  # 从小到大排序
                self.send_list_.pop(i)  # 从后往前删除

            # 等待回馈

            time.sleep(0.01)

            # 监听信号
            gain_string = self.read_all().decode(
                'utf-8')[:-1]  # 接收来自单片机的信息，去除后缀'\x00'
            if (gain_string  # 收到消息
                    and not gain_string[0].isdigit()  # 拒收数字开头的消息
                    and not gain_string == 'CALIBRAT'  # 拒收电机复位消息
                    ):  # 收到信号 - 筛选信号

                time_tick = time.time()
                self.gain_list_.append(
                    (gain_string, time_tick))  # 给添加的指令附加一个时间戳
                print(
                    f'GAIN {{tick: {time_tick:16.5f}, string: {gain_string}}}')

                # 提示容器存量，防止未进行清理容器

                print(
                    f'GAIN - INFO container{{tosend: {len(self.send_list_)}, gained: {len(self.gain_list_)}}}\n')
                print(
                    f'GAIN - INFO send:{[s for s,t in self.send_list_]}, gain:{[s for s,t in self.gain_list_]}')

            # 延时，等待下一次信息
            time.sleep(0.01)


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

    def __execute_device(self):
        """ 私有方法，发出串口指令，驱动外设 """
        self.sermtr_.append_string(f'{OrderID.SERVO}{self.id_}:{self.value_}')

    def rotate_to(self, v):
        assert self.min_ <= self.value_ <= self.max_, '范围超出'
        self.value_ = v
        self.__execute_device()


class PlaneMotor:
    """ 平面移动-基类 """

    def __init__(self, *, serial_object: SerialMotor = None, max_x: int = None, max_y: int = None, min_v: int = None, max_v: int = None, reset=True) -> None:
        """  """

        # 赋初始值
        self.sermtr_ = serial_object
        self.x_max_ = max_x
        self.y_max_ = max_y
        self.v_min_ = min_v
        self.v_max_ = max_v
        self.x = 0  # 坐标x
        self.y = 0  # 坐标y
        self.v = 0  # 速度v

        # 初始复位
        if reset:
            self.call_reset()

    def call_reset(self):
        """ 发送指令复位 """
        self.sermtr_.append_string('CALIBRAT')

    def __execute_device(self):
        """ 私有方法，发送串口指令 """
        self.sermtr_.append_string(
            f'{OrderID.PLANE}{self.x}:{self.y}:{self.v}')

    def move_to(self, *, x, y, v):
        assert 0 <= x <= self.x_max_, 'x范围超出'
        assert 0 <= y <= self.y_max_, 'y范围超出'
        assert self.v_min_ <= v <= self.v_max_, 'x范围超出'
        self.x = x
        self.y = y
        self.v = v
        self.__execute_device()


# 连接串口
print(*comports())
if os_name() == "Windows":
    ser_port = str(comports()[0]).split()[0]
elif os_name() == 'Linux':
    ser_port = comports()[0]
else:
    raise OSError()
smt = SerialMotor(ser_port)  # 派生类对象

s1 = ServoMotor(serial_id=ServoID.BAFFLE_1, serial_object=smt,
                max_value=100, min_value=0, initial_value=0)

p = PlaneMotor(serial_object=smt, max_x=6500,
               max_y=6500, min_v=500, max_v=10_000, reset=1)
time.sleep(2)

p.move_to(x=1000, y=5000, v=5000)
p.move_to(x=5000, y=5000, v=5000)
p.move_to(x=5000, y=1000, v=5000)
p.move_to(x=1000, y=1000, v=5000)

time.sleep(20)
