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

        if '__init__' in attrs.keys():
            raise TypeError('命名空间不需要实例化')
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
    alternator = None

    @classmethod
    def connect(cls, alternator: Serial) -> None:
        """ 指令处理器-构造函数\\
        `alternator` - 串口交流类"""
        cls.alternator = alternator
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
                    sleep(0.001)  # 延时防止两次指令间隔时间太短导致的指令无效

# %%


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


class BaffleStatus(Enum):
    """ 挡板状态 """
    CLOSE, OPEN = range(2)


BS = BaffleStatus

# %%


class Equipment(metaclass=NamespaceMeta):
    """ 命名空间 - 设备控制 """
    x, y = 0, 0
    height_max = 110

    @classmethod
    def connect(cls, processor) -> None:
        cls.processor = processor

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
            f'{CID.STEERING.value}{sid.value:02d}:{value:03d}', runtime)

    @classmethod
    def steer_baffle(cls, status: BS, baffle_id: SID, *, runtime: float = None):
        """ 根据舵机序号，设置挡板状态"""
        value = 0 if status is BS.CLOSE else 100
        cls.steer_set(baffle_id, value, runtime=runtime)

    @classmethod
    def steer_baffle_all(cls, status: BS, *, runtime: float = None):
        """ 统一设置挡板状态 """
        for sid in (SID.BAFFLE_0, SID.BAFFLE_1, SID.BAFFLE_2, SID.BAFFLE_3):
            cls.steer_set(sid, 0 if status is BS.CLOSE else 100,
                          runtime=runtime)

    @classmethod
    def steer_board(cls, rotation: int = 0, slope: int = 0, *, runtime: float = None):
        """ 设置底板状态 
        `rotation` - 顺时针-水平旋转角度
        `slope` - 顺时针-垂直倾斜角度"""
        cls.steer_set(SID.BOARD_HR, rotation+50, runtime=runtime)  # 旋转
        cls.steer_set(SID.BOARD_VT, slope+50, runtime=runtime+0.4)  # 倾斜

    # %% motor

    @classmethod
    def motor_set(cls, x, y, v, *, runtime: float = None):
        """ 设置步进电机 """
        OrderProcessor.receive(
            f'{CID.STEPPING.value}{x}:{y}:{v}', runtime)

    @classmethod
    def motor_reset(cls, *, runtime: float = None):
        """ 通过指令让步进电机复位 """
        cls.processor.receive('CALIBRAT', time()+runtime)

    @classmethod
    def motor_move(cls, x, y, v=10_000, *, runtime: float = None) -> float:
        """ 返回移动所耗时间 
        ## Parameter
        `x` - 坐标x
        `y` - 坐标y
        `v` - 移动速度
        ## Return
        `consume` - 此次移动耗时"""
        cls.motor_set(x, y, v, runtime=runtime)

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

    # %% arm

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

    @classmethod
    def arm_reset(cls, *, runtime: float = None):
        cls.arm_rorate(0, runtime=runtime)
        cls.arm_updown('max', runtime=runtime)
        cls.arm_claw(0, runtime=runtime)

    @classmethod
    def arm_pick_up(cls, rotation: int, height: int | str | float, spread: int = None, *, runtime: float = None):
        """ 捡起物体 """
        # 下落
        cls.arm_rorate(rotation, runtime=runtime)
        cls.arm_updown(0, runtime=runtime)
        cls.arm_claw(100, runtime=runtime)
        # 抓取
        cls.arm_claw(spread, runtime=runtime+0.4)
        # 回升
        cls.arm_updown('max', runtime=runtime+0.8)

    @classmethod
    def arm_throw_down(cls, *, runtime: float = None):
        """ 丢落物体 """
        cls.arm_updown(0, runtime=runtime)  # 下落
        cls.arm_claw(100, runtime=runtime+0.4)  # 丢下
        cls.arm_updown('max', runtime=runtime+0.8)  # 回升

    # %% 压缩(亚索yaso) TODO
    @classmethod
    def yaso_reset(cls):
        ...


# %%
if __name__ == '__main__':
    OrderProcessor.connect(get_serial())
    Equipment.connect(OrderProcessor)
    # Equipment.steer_set(SID.BAFFLE_1, 100)
    # Equipment.steer_baffle(BS.CLOSE, SID.BAFFLE_2)

    # Equipment.motor_move(3000,3000)
    # Equipment.grab_set(rotation=90, spread=0, height='max')
    def test():
        Equipment.steer_baffle_all(BS.OPEN)

        Equipment.steer_baffle_all(BS.CLOSE, runtime=time()+5)
    test()

    # %% 等待结束
    import tkinter as tk
    win = tk.Tk()
    win.title('外设测试程序 - ZYF')
    win.wm_attributes('-topmost', 1)  # 置顶
    win.wm_attributes('-toolwindow', 1)  # 工具窗
    W, H = win.winfo_screenwidth(), win.winfo_screenheight()
    w, h = 300, 75
    win.geometry(f'{w}x{h}+{(W-w)//2}+{(H-h)//3}')
    win['bg'] = '#dddddc'
    btn = tk.Button(win, text='退出', fg='gray', font=(
        None, 20, 'bold'), command=win.destroy)
    btn_test = tk.Button(win, text='测试', font=(
        None, 20, 'bold'), command=test)
    btn.place(x=25, y=15, width=100, height=50)
    btn_test.place(x=10+125, y=15, width=150, height=50)
    win.mainloop()
