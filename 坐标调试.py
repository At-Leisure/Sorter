import time
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

x, y = 0, 0
verify = 1


# def moveByMeshGrid():
#     global x, y
#     import random
#     device.init()
#     i = 0
#     x_bios = int(random.random()*500)
#     y_bios = int(random.random()*500)
#     for xx in range(0,6000+1,1000):
#         for yy in range(0,7000+1,1000):
#             if i == 0:
#                 device.arm_move(0,0)
#                 time.sleep(5)
#                 device.reset_move()
#                 time.sleep(1)

#             x = xx + x_bios
#             y = yy + y_bios
#             print('----', x, y)
#             device.arm_move(x, y)

#             i += 1
#             i %= 5
#             time.sleep(4.5)


# if not verify:
#     Thread(target=moveByMeshGrid, daemon=True).start()

x, y = 1000, 5000
device.init()
camera.init()
time.sleep(5)
device.arm_move(x, y)

W_raw, H_raw = 1280, 1024
ratio = 0.7
W_new, H_new = int(W_raw*ratio), int(H_raw*ratio)


def transform(cx, cy):#《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《《坐标转换》
    tx = 1200 + (637-cx)*10
    ty = 2300 + (cy-350)*10
    tx += 0  # 手动修正
    ty += 0  # 手动修正
    return int(tx), int(ty)


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
        image_pil = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
        image_tk = ImageTk.PhotoImage(image_pil.resize((W_new, H_new)))
        lbl.config(image=image_tk)
        lbl.image = image_tk


Thread(target=update_scene, daemon=True).start()


win.mainloop()
