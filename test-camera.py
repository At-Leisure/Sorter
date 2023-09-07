from time import time,sleep
#
import cv2
#
import camera.api as CAPI
#import device as DAPI

CAPI.camera_init()


while 1:
    im = CAPI.extract()
    infos,im = CAPI.scan_from(im)
    cv2.imshow('im',im)
    cv2.waitKey(1)