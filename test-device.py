import tkinter as tk
from time import time
import device.api as DeviceAPI

DeviceAPI.init()


def test(event=None):
    DeviceAPI.reset_move()
    DeviceAPI.sequence_begin(runtime=time()+1)#开始
    DeviceAPI.arm_move(4500,4500)
    DeviceAPI.arm_pick_up(45,0,10)
    DeviceAPI.arm_move(1000,6500)
    DeviceAPI.arm_throw_down()
    DeviceAPI.arm_move(0,0)
    DeviceAPI.reset_arm()
    DeviceAPI.sequence_finish()#结束

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
