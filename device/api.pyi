""" 命名空间 - 分拣操作API - 高层封装  """

from time import time
import tkinter as tk

from .tools import *
from .device_driver import DeviceDriver

OPEN, CLOSE = 1, 0


def init(): ...
def baffle_set(status: bool, sid: SID, *, runtime: float = None): ...
def baffle_set_all(status: bool, *, runtime: float = None): ...
def arm_move(x, y, v=10_000, *, runtime: float = None): ...
def arm_pick_up(rotation: int, height: int | str | float,
                spread: int = None, *, runtime: float = None) -> float: ...


def arm_throw_down(*, runtime: float = None) -> float: ...
def reset_arm(*, runtime: float = None): ...
def reset_move(*, runtime: float = None): ...
def sequence_begin(*, runtime: float = None): ...
def sequence_finish(): ...
def wait_ending(test_func=None) -> tk.Tk:...