from time import time,sleep
#
import cv2
#
import camera as CMR
#import device as DAPI

CMR.init()


while 1:
    im = CMR.extract()
    infos,im = CMR.scan_from(im)
    print(eval(str(infos)))
    cv2.imshow('im',im)
    cv2.waitKey(200)