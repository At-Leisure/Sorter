""" 拓展类集合 """

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