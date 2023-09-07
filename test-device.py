import tkinter as tk
import device
from time import time

device.init()

device.baffle_set_all(1)
#device.reset_arm()
#device.DeviceDriver.yaso_press(0,0.01,0.01)

def test(event=None):
    """  """
    #device.reset_move()
    device.sequence_begin(runtime=time()+1)#开始
    device.arm_move(4000,4000)
    device.arm_pick_up(45,0,10)
    device.arm_move(4000,7500)
    device.arm_throw_down(0)
    device.arm_move(100,100)
    device.reset_arm()
    # # t = time()
    # # device.DeviceDriver.yaso_press(9.99,0.99,0.005,runtime=t)
    # # device.DeviceDriver.yaso_press(0,0.5,0.01,runtime=t+0.5)
    device.sequence_finish()#结束
    
#device.reset_move()
# device.DeviceDriver.arm_updown(0.2)
# device.DeviceDriver.arm_claw(20)
# device.arm_move(480,750)


# %% 等待结束
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
win.bind('<KeyRelease-space>',test)
win.mainloop()
