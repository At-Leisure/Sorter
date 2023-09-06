from time import time
#
import cv2
#
import camera.api as CAPI
import device.api as DAPI

CAPI.camera_init()
DAPI.init()

def test():
    infos, im = CAPI.scan_from(CAPI.extract())
    for index, category, (center_x, center_y), (width, height), rotation in infos:
        center_x, center_y = int(center_x), int(center_y)
        width, height = int(width), int(height)
        rotation = int(rotation)
        
        DAPI.sequence_begin(runtime=time()+2)
        DAPI.arm_move(5000,5000)
        DAPI.arm_pick_up(rotation,0,width//10)
        DAPI.arm_move(0,3500)
        DAPI.arm_throw_down()
    
    
DAPI.wait_ending(test).mainloop()
    