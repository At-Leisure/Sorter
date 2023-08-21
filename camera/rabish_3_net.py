import cv2
import numpy as np
import onnxruntime
import serial
import time
import argparse
import math
CLASSES = ['recyclable',
'hazardous',
'kitchen',
'other'
]


class YOLOV5():
    def __init__(self, onnxpath):
        self.onnx_session = onnxruntime.InferenceSession(onnxpath,providers=['CPUExecutionProvider'],sess_options=onnxruntime.SessionOptions())
        self.input_name = self.get_input_name()
        self.output_name = self.get_output_name()

    # -------------------------------------------------------
    #   获取输入输出的名字
    # -------------------------------------------------------
    def get_input_name(self):
        input_name = []
        for node in self.onnx_session.get_inputs():
            input_name.append(node.name)
        return input_name

    def get_output_name(self):
        output_name = []
        for node in self.onnx_session.get_outputs():
            output_name.append(node.name)
        return output_name

    # -------------------------------------------------------
    #   输入图像
    # -------------------------------------------------------
    def get_input_feed(self, img_tensor):
        input_feed = {}
        for name in self.input_name:
            input_feed[name] = img_tensor
        return input_feed

    # -------------------------------------------------------
    #   1.cv2读取图像并resize
    #	2.图像转BGR2RGB和HWC2CHW
    #	3.图像归一化
    #	4.图像增加维度
    #	5.onnx_session 推理
    # -------------------------------------------------------
    def inference_pic(self, img_path):
        img = cv2.imread(img_path)
        or_img = cv2.resize(img, (640, 640))
        img = or_img[:, :, ::-1].transpose(2, 0, 1)  # BGR2RGB和HWC2CHW
        img = img.astype(dtype=np.float32)
        img /= 255.0
        img = np.expand_dims(img, axis=0)
        input_feed = self.get_input_feed(img)
        pred = self.onnx_session.run(None, input_feed)[0]
        return pred, or_img
    def inference_cam(self, img):
        or_img = cv2.resize(img, (640, 640))
        img = or_img[:, :, ::-1].transpose(2, 0, 1)  # BGR2RGB和HWC2CHW
        img = img.astype(dtype=np.float32)
        img /= 255.0
        img = np.expand_dims(img, axis=0)
        input_feed = self.get_input_feed(img)
        pred = self.onnx_session.run(None, input_feed)[0]
        return pred, or_img

# dets:  array [x,6] 6个值分别为x1,y1,x2,y2,score,class
# thresh: 阈值
def nms(dets, thresh):
    x1 = dets[:, 0]
    y1 = dets[:, 1]
    x2 = dets[:, 2]
    y2 = dets[:, 3]
    # -------------------------------------------------------
    #   计算框的面积
    #	置信度从大到小排序
    # -------------------------------------------------------
    areas = (y2 - y1 + 1) * (x2 - x1 + 1)
    scores = dets[:, 4]
    keep = []
    index = scores.argsort()[::-1]

    while index.size > 0:
        i = index[0]
        keep.append(i)
        # -------------------------------------------------------
        #   计算相交面积
        #	1.相交
        #	2.不相交
        # -------------------------------------------------------
        x11 = np.maximum(x1[i], x1[index[1:]])
        y11 = np.maximum(y1[i], y1[index[1:]])
        x22 = np.minimum(x2[i], x2[index[1:]])
        y22 = np.minimum(y2[i], y2[index[1:]])

        w = np.maximum(0, x22 - x11 + 1)
        h = np.maximum(0, y22 - y11 + 1)

        overlaps = w * h
        # -------------------------------------------------------
        #   计算该框与其它框的IOU，去除掉重复的框，即IOU值大的框
        #	IOU小于thresh的框保留下来
        # -------------------------------------------------------
        ious = overlaps / (areas[i] + areas[index[1:]] - overlaps)
        idx = np.where(ious <= thresh)[0]
        index = index[idx + 1]
    return keep

def calculate_distance(point1, point2):
    x_diff = point2[0] - point1[0]
    y_diff = point2[1] - point1[1]
    distance = math.sqrt(x_diff**2 + y_diff**2)
    return distance


def xywh2xyxy(x):
    # [x, y, w, h] to [x1, y1, x2, y2]
    y = np.copy(x)
    y[:, 0] = x[:, 0] - x[:, 2] / 2
    y[:, 1] = x[:, 1] - x[:, 3] / 2
    y[:, 2] = x[:, 0] + x[:, 2] / 2
    y[:, 3] = x[:, 1] + x[:, 3] / 2
    return y

# 计算向量的长度
def calculate_vector_length(vector):
    return math.sqrt(vector[0]**2 + vector[1]**2)

# 计算向量的单位向量
def calculate_unit_vector(vector):
    length = calculate_vector_length(vector)
    return (vector[0] / length, vector[1] / length)

# 计算向量之间的夹角（弧度）
def calculate_angle(vector1, vector2):
    unit_vector1 = calculate_unit_vector(vector1)
    unit_vector2 = calculate_unit_vector(vector2)
    dot_product = unit_vector1[0] * unit_vector2[0] + unit_vector1[1] * unit_vector2[1]
    angle = math.acos(dot_product)
    return angle

def filter_box(org_box, conf_thres, iou_thres):  # 过滤掉无用的框
    # -------------------------------------------------------
    #   删除为1的维度
    #	删除置信度小于conf_thres的BOX
    # -------------------------------------------------------
    org_box = np.squeeze(org_box)
    conf = org_box[..., 4] > conf_thres
    box = org_box[conf == True]
    # -------------------------------------------------------
    #	通过argmax获取置信度最大的类别
    # -------------------------------------------------------
    cls_cinf = box[..., 5:]
    cls = []
    for i in range(len(cls_cinf)):
        cls.append(int(np.argmax(cls_cinf[i])))
    all_cls = list(set(cls))
    # -------------------------------------------------------
    #   分别对每个类别进行过滤
    #	1.将第6列元素替换为类别下标
    #	2.xywh2xyxy 坐标转换
    #	3.经过非极大抑制后输出的BOX下标
    #	4.利用下标取出非极大抑制后的BOX
    # -------------------------------------------------------
    output = []


    for i in range(len(all_cls)):
        curr_cls = all_cls[i]
        curr_cls_box = []
        curr_out_box = []
        for j in range(len(cls)):
            if cls[j] == curr_cls:
                box[j][5] = curr_cls
                curr_cls_box.append(box[j][:6])
        curr_cls_box = np.array(curr_cls_box)
        # curr_cls_box_old = np.copy(curr_cls_box)
        curr_cls_box = xywh2xyxy(curr_cls_box)
        curr_out_box = nms(curr_cls_box, iou_thres)
        for k in curr_out_box:
            output.append(curr_cls_box[k])
    output = np.array(output)
    return output

lenth = 0
def draw(image, box_data):
    # -------------------------------------------------------
    #	取整，方便画框
    # -------------------------------------------------------
    if box_data.shape[0] == 0:
        print("No objects detected.")
        return
    boxes = box_data[..., :4].astype(np.int32)
    scores = box_data[..., 4]
    classes = box_data[..., 5].astype(np.int32)
    global lenth
    lenth = len(classes)
    count = 1
    results = []
    for box, score, cl in zip(boxes, scores, classes):
        top, left, right, bottom = box

        x_min, y_min, x_max, y_max = box
        step_50 = 25
        step_40 = 20
        step_30 = 15
        step_20 = 10
        step_10 = 5

        if y_min - step_50 > 0 and y_max + step_50 < 640 and x_max + step_50 < 640 and x_min - step_50 > 0:
            cropped_image = image[y_min - step_50: y_max + step_50, x_min - step_50: x_max + step_50]
        elif y_min - step_40 > 0 and y_max + step_40 < 640 and x_max + step_40 < 640 and x_min - step_40 > 0:
            cropped_image = image[y_min - step_40: y_max + step_40, x_min - step_40: x_max + step_40]
        elif y_min - step_30 > 0 and y_max + step_30 < 640 and x_max + step_30 < 640 and x_min - step_30 > 0:
            cropped_image = image[y_min - step_30: y_max + step_30, x_min - step_30: x_max + step_30]
        elif y_min - step_20 > 0 and y_max + step_20 < 640 and x_max + step_20 < 640 and x_min - step_20 > 0:
            cropped_image = image[y_min - step_20: y_max + step_20, x_min - step_20: x_max + step_20]
        elif y_min - step_10 > 0 and y_max + step_10 < 640 and x_max + step_10 < 640 and x_min - step_10 > 0:
            cropped_image = image[y_min - step_10: y_max + step_10, x_min - step_10: x_max + step_10]
        else:
            cropped_image = image[y_min : y_max , x_min : x_max ]
        min_side_length,max_side_length,angle = fangxiang(cropped_image,box)
        #cv2.imshow("cropped_image",cropped_image)
        cv2.rectangle(image, (top, left), (right, bottom), (255, 0, 0), 2)
        cv2.circle(image, ((top + right) // 2, (left + bottom) // 2), 5, (0, 0, 255), -1)
        cv2.putText(image, '{0} {1:.2f}'.format(CLASSES[cl], score),
                    (top, left),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 0, 255), 2)
        result = (str(count), str(CLASSES[cl]), [str((top + right) // 2), str((left + bottom) // 2)], [str(int(min_side_length)),str(int(max_side_length))],str(int(angle)))
        results.append(result)
        #text = str(count) + " "+str(CLASSES[cl])+" " + str((top + right) // 2) + " " + str((left + bottom) // 2) + " " + str(int(min_side_length)) + " " + str(int(max_side_length)) + " " + str(int(angle))
        #print(results)
        #ser.write(text.encode('utf-8'))
        #print(count)
        count+=1
    return results


def GausBlur(src):
    dst = cv2.GaussianBlur(src, (5, 5), 1.5)
    #cv2.imshow('GausBlur', dst)
    return dst

def Gray_img(src):
    gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    #cv2.imshow('gray', gray)
    return gray


def process(src,image,img_box):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hsv = cv2.medianBlur(hsv, 5)

    mask = cv2.inRange(hsv, (0, 0, 1), (0, 0, 255))  # inrange

    line = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5), (-1, -1))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, line)

    contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_num = len(contours)

    i = 0
    #print(lenth)
    while i < contours_num:

        if i > 0:
            break
        c = sorted(contours, key=cv2.contourArea, reverse=True)[i]  # 排序，key为排序比较元素，true为降序

        rect = cv2.minAreaRect(c)
        box = np.intp(cv2.boxPoints(rect))
        area = cv2.contourArea(box)

        max_side_length = 0
        min_side_length = 1000000  # 初始设置为无穷大
        start_point = ()
        end_point = ()

        # 计算矩形边长，并记录最长边的起点和终点
        for i in range(4):
            side_length = calculate_distance(box[i], box[(i + 1) % 4])
            if side_length > max_side_length:
                max_side_length = side_length
                start_point = box[i]
                end_point = box[(i + 1) % 4]
            if side_length < min_side_length:
                min_side_length = side_length
        # 计算矩形的短边长度
        # print("矩形的短边长度为：", min_side_length)
        # print("矩形的最长边长度为：", max_side_length)
        # 计算起点到终点的向量
        vector = (end_point[0] - start_point[0], end_point[1] - start_point[1])
        # 计算起点到X轴正方向的向量
        reference_vector = (1, 0)

        # 计算起点到终点向量和X轴正方向向量的夹角
        angle = calculate_angle(vector, reference_vector)

        # 将弧度转换为角度
        angle_degrees = math.degrees(angle)

        # print("起点坐标：", start_point)
        # print("终点坐标：", end_point)
        # print("旋转矩形的角度：", angle_degrees)
        cv2.line(src,start_point,end_point,(0,255,255),3)
        cv2.drawContours(image, [box], -1, (0, 255, 0), 3)
        #cv2.drawContours(src, [box], -1, (0, 255, 0), 3)
        #cv2.putText(src, str(i + 1), (box[0][0], box[0][1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 111, 111), 3)

        i += 1

    return image,min_side_length,max_side_length,angle_degrees
def fangxiang(src,box):
    min_side_length = 0
    max_side_length = 0
    angle = 0
    if src is not None and np.any(src):
        gaus_img = GausBlur(src)
        gray_img = Gray_img(gaus_img)
        thres_img = threshold_img(gray_img)
        cv2.imwrite('pic/pic.png', thres_img)
        image = cv2.cvtColor(thres_img, cv2.COLOR_GRAY2BGR)
        none_v,min_side_length,max_side_length,angle = process(src,image,box)
    #cv2.imshow('result', result)
    return min_side_length,max_side_length,angle
def threshold_img(src):
    ret, binary = cv2.threshold(src, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_TRIANGLE)
    # print("threshold value %s" % ret)
    #cv2.imshow('threshold', binary)
    return binary

# def serget(port,bps,time):#port：端口号，bps：波特率，time：超时时间
#     try:
#         ser = serial.Serial(port, bps, timeout=time)# 打开串口
#         print('串口已连接，当前串口：{0}'.format(port))
#         print("串口详情参数：", ser)
#         return ser
#     except Exception as e:  # 如果出现异常
#         print("串口连接失败，失败分析:", e)
# def serload(ser,timeout = 5):
#     start_time = time.time()
#     while True:
#         if ser.in_waiting:
#             str1 = ser.readline().decode('GBK')  # 读一行，以/n结束。
#             char1 = print(ser.read(size=1).hex()) # 从串口读size个字节
#             print(str1)
#             start_time = time.time()  # 更新接收到数据的时间戳
#         if time.time() - start_time > timeout:
#             break


model = YOLOV5('./camera/best_2000.onnx')

def scan_image(img_path):
    """ 从本地图片获取信息 """
    output, or_img = model.inference_pic(img_path)
    outbox = filter_box(output, 0.4, 0.4)
    results = draw(or_img, outbox)
    #cv2.imshow('or_img', or_img)
    return results

def scan_video(img):
    """ 从图片数据获取信息 """
    output, or_img = model.inference_cam(img)
    outbox = filter_box(output, 0.4, 0.4)
    results = draw(or_img, outbox)
    cv2.imshow('or_img', or_img)
    return results
    



if __name__ == "__main__":
    results = []
    onnxruntime.get_device()
    model = YOLOV5('./camera/best_2000.onnx')
    #ser=serget("COM7",9600,1)
    #serload(ser)
    #ser.close()  # 关闭串口
    #cv2.imwrite('res.jpg', or_img)
    # 使用指定图像路径
    results=scan_image('./camera/sample.jpg')
    print(results)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# ret, frame = capture.read()
# x = 200
# y = 100
# width = 800
# height = 800
#
# # 截取指定位置和大小的图像内容
# frame = frame[y:y + height, x:x + width]
# cv2.imshow('s', frame)




