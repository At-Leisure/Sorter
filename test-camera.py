
#
import cv2
#
import camera.api as CAPI

CAPI.camera_init()
while 1:
    im = CAPI.extract()
    resized_im = cv2.resize(im,(1280//2,1024//2))
    info,scaned_im = CAPI.scan_from(resized_im)
    print(info)
    cv2.imshow('im',scaned_im)
    cv2.waitKey(2000)