""" 工具 """
# 内置拓展模块
from dataclasses import dataclass
from platform import platform
from enum import Enum
# 第三方拓展库
from icecream import ic
from serial import Serial
from serial.tools.list_ports import comports

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

        if '__init__' in attrs.keys():
            raise TypeError('命名空间不需要实例化')
        # 返回修改好的类名
        return super().__new__(cls, name, bases, attrs)





class CommandID(Enum):
    """ 命令标号，舵机，步进，宇树 """
    STEERING, STEPPING, UNITREE = range(3)


CID = CommandID


class SteeringID(Enum):
    """ 舵机标号 """
    # 挡板-0,1,2,3
    BAFFLE_0, BAFFLE_1, BAFFLE_2, BAFFLE_3 = range(4)
    # 底板-水平,垂直
    BOARD_VT, BOARD_HR = range(4, 6)
    # 压缩(亚索yaso)出口,YASO_EXIT
    range(6, 8)
    # 机械臂上下-1,2，机械臂旋转，机械爪
    ARM_UPDOWN_0, ARM_UPDOWN_1, ARM_ROTATE, ARM_CLAW = range(8, 12)


SID = SteeringID
