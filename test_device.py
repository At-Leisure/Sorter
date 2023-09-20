import device
import time

device.init()

device.baffle_set_all(1)

device.reset_move()
device.reset_arm()
def test():
    """ 测试 """
    # device.sequence_begin()#开始
    # device.arm_move(4000,4000)
    # device.arm_pick_up(45,0,10)
    # device.arm_move(4000,7500)
    # device.arm_throw_down(0)
    # device.arm_move(0,0)
    # device.reset_arm()
    # # # t = time()
    # # # device.DeviceDriver.yaso_press(9.99,0.99,0.005,runtime=t)
    # # # device.DeviceDriver.yaso_press(0,0.5,0.01,runtime=t+0.5)
    # device.sequence_finish()#结束
    t = time.time()
    device.device_driver.DeviceDriver.yaso_press(10,0.5,0.001,runtime=t)
    device.device_driver.DeviceDriver.yaso_press(0,0.5,0.001,runtime=t+0.5)

    
    
# device.arm_move(0,0)

    
#device.arm_move(0,0)
device.wait_tkinter(test).mainloop() 