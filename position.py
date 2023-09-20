import time
import enum
#
import cv2
from PIL import Image, ImageTk
#
import camera
import device
import graphic
import numpy as np
import tkinter as tk
from threading import Thread

# with open('./misc/坐标.txt', 'w', encoding='utf-8') as f:
#     pass

correcte_x = 2000
correcte_y = -500

def transform(cx, cy):  # 《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《坐标转换》
    """ 坐标转换函数：图像坐标->电机坐标 """
    global correcte_x,correcte_y
    tx = 1200 + (637-cx)*(3800/385)
    ty = 2300 + (cy-350)*(2700/275)
    tx += correcte_x  # 手动修正
    ty += correcte_y  # 手动修正
    return int(tx), int(ty)


if __name__ == '__main__':
    class Mode(enum.Enum):
        坐标拟合 = 0
        坐标修正 = 1

    used_mode = Mode.坐标修正

    match used_mode:
        case Mode.坐标拟合:
            x, y = 0, 0
            verify = 0
            camera.init()

            def moveByMeshGrid():
                global x, y
                import random
                device.init()
                i = 0
                x_bios = int(random.random()*500)
                y_bios = int(random.random()*500)
                for xx in range(0, 6000+1, 1000):
                    for yy in range(0, 7000+1, 1000):
                        if i == 0:
                            device.arm_move(0, 0)
                            time.sleep(5)
                            device.reset_move()
                            time.sleep(1)

                        x = xx + x_bios
                        y = yy + y_bios
                        print('----', x, y)
                        device.arm_move(x, y)

                        i += 1
                        i %= 5
                        time.sleep(4.5)

            if not verify:
                Thread(target=moveByMeshGrid, daemon=True).start()

            W_raw, H_raw = 1280, 1024
            ratio = 0.7
            W_new, H_new = int(W_raw*ratio), int(H_raw*ratio)

            def lbl_bind(event: tk.Event):
                click_x, click_y = int(event.x / ratio), int(event.y / ratio)
                if not verify:
                    with open('./misc/坐标.txt', 'a', encoding='utf-8') as f:
                        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                        f.write(f'{x} {y} {click_x} {click_y}\n')
                    print((click_x, click_y), (x, y))
                else:
                    turn_x, turn_y = transform(click_x, click_y)
                    device.arm_move(turn_x, turn_y)

            win = tk.Tk()
            win.geometry(f'{W_new}x{H_new}')
            lbl = tk.Label(win)
            lbl.place(x=0, y=0, width=W_new, height=H_new)
            lbl.bind('<Button-1>', lbl_bind)

            image_pil = None
            image_tk = None

            def update_scene():
                global image_pil, image_tk
                while True:
                    time.sleep(0.05)
                    im = camera.extract()
                    image_pil = Image.fromarray(
                        cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
                    image_tk = ImageTk.PhotoImage(
                        image_pil.resize((W_new, H_new)))
                    lbl.config(image=image_tk)
                    lbl.image = image_tk

            Thread(target=update_scene, daemon=True).start()

            win.mainloop()

        case Mode.坐标修正:
            camera.init()
            device.init()

            W_raw, H_raw = 1280, 1024
            ratio = 0.5
            W_new, H_new = int(W_raw*ratio), int(H_raw*ratio)

            def lbl_bind(event: tk.Event):
                if 0:
                    device.reset_arm()
                    time.sleep(0.5)
                    device.reset_move()
                    time.sleep(7)
                    click_x, click_y = 351, 811
                else:
                    click_x, click_y = int(event.x / ratio), int(event.y / ratio)
                turn_x, turn_y = transform(click_x, click_y)
                t = device.arm_move(turn_x, turn_y)
                device.device_driver.DeviceDriver.arm_updown(50,runtime=time.time()+2)
                print(f'click:{(click_x,click_y)}, moved:{(turn_x,turn_y)}')

            win = tk.Tk()
            win.geometry(f'{W_new}x{H_new+40}')
            lbl = tk.Label(win)
            lbl.place(x=0, y=0, width=W_new, height=H_new)
            lbl.bind('<Button-1>', lbl_bind)

            image_pil = None
            image_tk = None

            def update_scene():
                global image_pil, image_tk
                while True:
                    time.sleep(0.05)
                    im = camera.extract()
                    image_pil = Image.fromarray(
                        cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
                    image_tk = ImageTk.PhotoImage(
                        image_pil.resize((W_new, H_new)))
                    lbl.config(image=image_tk)
                    lbl.image = image_tk

            Thread(target=update_scene, daemon=True).start()
            
            entry_dx = tk.Entry(win)
            entry_dx.insert(0,f'{correcte_x}')
            entry_dy = tk.Entry(win)
            entry_dy.insert(0,f'{correcte_y}')
            
            def entry_bt_func():
                global correcte_x,correcte_y
                dxx = int(entry_dx.get())
                dyy = int(entry_dy.get())
                correcte_x,correcte_y = dxx,dyy
                print(dxx,dyy)
            
            entry_bt = tk.Button(win,text='确认改参',command=entry_bt_func)
            
            entry_dx.place(x=0,y=H_new,width=W_new//3,height=40)
            entry_dy.place(x=W_new//3,y=H_new,width=W_new//3,height=40)
            entry_bt.place(x=W_new//3*2,y=H_new,width=W_new//3,height=40)
            
            win.mainloop()
