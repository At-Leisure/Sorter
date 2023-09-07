
""" 应用程序接口-API """
# API-应用程序与外设驱动的桥梁
# 目录包含顺序: {(API): (tools, device_driver); device_driver: (tools)}

from ._api import *
from .device_driver import DeviceDriver
from .speed_api import timeCalculate