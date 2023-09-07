import ctypes

# 加载动态链接库
mylib = ctypes.CDLL('./device/speed.so')

# 定义函数原型
mylib.TimeCalculate.argtypes = [ctypes.c_int16, ctypes.c_int16, ctypes.c_int16]
mylib.TimeCalculate.restype = ctypes.c_float



def timeCalculate(dx: int, dy: int, v: int) -> float:
    """ 输入位置的变化量和速度，返回移动耗时。注：此函数一般计算耗时为0.0秒"""
    return mylib.TimeCalculate(dx,dy,v)



if __name__ == '__main__':
    # 调用C++函数
    result = timeCalculate(5000, 5000, 10000)
    print(result)
