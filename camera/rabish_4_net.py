import cv2
import numpy as np
import onnxruntime
import math
CLASSES = ['hazardous_battery',
'hazardous_bag',
'hazardous_box',
'hazardous_bottle',
'hazardous_inner',
'recycle_can',
'recycle_water',
'kitchen_potato',
'kitchen_turnip',
'kitchen_carrot',
'other_porcelain',
'other_cobblestone',
'other_brick'
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
        img = cv2.rotate(img,cv2.ROTATE_180)
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
        img = cv2.rotate(img, cv2.ROTATE_180)
        #img = white_balance_1(img)
        img = or_img[:, :, ::-1].transpose(2, 0, 1)  # BGR2RGB和HWC2CHW
        img = img.astype(dtype=np.float32)
        img /= 255.0
        img = np.expand_dims(img, axis=0)
        input_feed = self.get_input_feed(img)
        pred = self.onnx_session.run(None, input_feed)[0]
        return pred, or_img


def white_balance_1(img):
    '''
    第一种简单的求均值白平衡法
    :param img: cv2.imread读取的图片数据
    :return: 返回的白平衡结果图片数据
    '''
    # 读取图像
    r, g, b = cv2.split(img)
    r_avg = cv2.mean(r)[0]
    g_avg = cv2.mean(g)[0]
    b_avg = cv2.mean(b)[0]
    # 求各个通道所占增益
    k = (r_avg + g_avg + b_avg) / 3
    kr = k / r_avg
    kg = k / g_avg
    kb = k / b_avg
    r = cv2.addWeighted(src1=r, alpha=kr, src2=0, beta=0, gamma=0)
    g = cv2.addWeighted(src1=g, alpha=kg, src2=0, beta=0, gamma=0)
    b = cv2.addWeighted(src1=b, alpha=kb, src2=0, beta=0, gamma=0)
    balance_img = cv2.merge([b, g, r])
    return balance_img


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
    img_src = image.copy()
    results = []
    for box, score, cl in zip(boxes, scores, classes):
        top, left, right, bottom = box
        x_min, y_min, x_max, y_max = box
        black = image.copy()
        black = cv2.resize(black,(1280,1024))
        black_image = np.zeros_like(black)
        black_image[:, :] = [34, 28, 38]
        black_image[y_min :y_max , x_min:x_max] = img_src[y_min: y_max, x_min: x_max]
        cv2.imshow("black", black_image)
        step_50 = 10
        step_40 = 20
        step_30 = 15
        step_20 = 10
        step_10 = 5
        if y_min - step_50 > 0 and y_max + step_50 < 640 and x_max + step_50 < 640 and x_min - step_50 > 0:
            cropped_image = black_image[y_min - step_50: y_max + step_50, x_min - step_50: x_max + step_50]
            c_image = image[y_min - step_50: y_max + step_50, x_min - step_50: x_max + step_50]
        elif y_min - step_40 > 0 and y_max + step_40 < 640 and x_max + step_40 < 640 and x_min - step_40 > 0:
            cropped_image = image[y_min - step_40: y_max + step_40, x_min - step_40: x_max + step_40]
            c_image = image[y_min - step_40: y_max + step_40, x_min - step_40: x_max + step_40]
        elif y_min - step_30 > 0 and y_max + step_30 < 640 and x_max + step_30 < 640 and x_min - step_30 > 0:
            cropped_image = image[y_min - step_30: y_max + step_30, x_min - step_30: x_max + step_30]
            c_image = image[y_min - step_30: y_max + step_30, x_min - step_30: x_max + step_30]
        elif y_min - step_20 > 0 and y_max + step_20 < 640 and x_max + step_20 < 640 and x_min - step_20 > 0:
            cropped_image = image[y_min - step_20: y_max + step_20, x_min - step_20: x_max + step_20]
            c_image = image[y_min - step_20: y_max + step_20, x_min - step_20: x_max + step_20]
        elif y_min - step_10 > 0 and y_max + step_10 < 640 and x_max + step_10 < 640 and x_min - step_10 > 0:
            cropped_image = image[y_min - step_10: y_max + step_10, x_min - step_10: x_max + step_10]
            c_image = image[y_min - step_10: y_max + step_10, x_min - step_10: x_max + step_10]
        else:
            cropped_image = image[y_min : y_max, x_min: x_max ]
            c_image = image[y_min : y_max, x_min: x_max ]
        min_side_length,max_side_length,angle = fangxiang(cropped_image,c_image,box)
        #cv2.imshow("cropped_image", cropped_image)
        #cv2.rectangle(image, (top, left), (right, bottom), (255, 0, 0), 2)
        cv2.circle(image, ((top + right) // 2, (left + bottom) // 2), 5, (0, 0, 255), -1)
        cv2.putText(image, '{0} {1:.2f} {2:.2f}'.format(CLASSES[cl], score ,angle),
                    (top  , left ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 0, 255), 2)#绘制标签
        result = (str(count), str(CLASSES[cl]), [str((top + right) // 2), str( (left + bottom) // 2)], [str(int(min_side_length)),str(int(max_side_length))],str(int(angle)))
        results.append(result)
        #text = str(count) + " "+str(CLASSES[cl])+" " + str((top + right) // 2) + " " + str((left + bottom) // 2) + " " + str(int(min_side_length)) + " " + str(int(max_side_length)) + " " + str(int(angle))
        #print(results)
        #ser.write(text.encode('utf-8'))
        #print(count)
        count+=1
    return results


def white_balance_4(img):
    '''
    基于图像分析的偏色检测及颜色校正方法
    :param img: cv2.imread读取的图片数据
    :return: 返回的白平衡结果图片数据
    '''

    def detection(img):
        '''计算偏色值'''
        img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(img_lab)
        d_a, d_b, M_a, M_b = 0, 0, 0, 0
        for i in range(m):
            for j in range(n):
                d_a = d_a + a[i][j]
                d_b = d_b + b[i][j]
        d_a, d_b = (d_a / (m * n)) - 128, (d_b / (n * m)) - 128
        D = np.sqrt((np.square(d_a) + np.square(d_b)))

        for i in range(m):
            for j in range(n):
                M_a = np.abs(a[i][j] - d_a - 128) + M_a
                M_b = np.abs(b[i][j] - d_b - 128) + M_b

        M_a, M_b = M_a / (m * n), M_b / (m * n)
        M = np.sqrt((np.square(M_a) + np.square(M_b)))
        k = D / M
        print('偏色值:%f' % k)
        return

    b, g, r = cv2.split(img)
    # print(img.shape)
    m, n = b.shape
    # detection(img)

    I_r_2 = np.zeros(r.shape)
    I_b_2 = np.zeros(b.shape)
    sum_I_r_2, sum_I_r, sum_I_b_2, sum_I_b, sum_I_g = 0, 0, 0, 0, 0
    max_I_r_2, max_I_r, max_I_b_2, max_I_b, max_I_g = int(r[0][0] ** 2), int(r[0][0]), int(b[0][0] ** 2), int(
        b[0][0]), int(g[0][0])
    for i in range(m):
        for j in range(n):
            I_r_2[i][j] = int(r[i][j] ** 2)
            I_b_2[i][j] = int(b[i][j] ** 2)
            sum_I_r_2 = I_r_2[i][j] + sum_I_r_2
            sum_I_b_2 = I_b_2[i][j] + sum_I_b_2
            sum_I_g = g[i][j] + sum_I_g
            sum_I_r = r[i][j] + sum_I_r
            sum_I_b = b[i][j] + sum_I_b
            if max_I_r < r[i][j]:
                max_I_r = r[i][j]
            if max_I_r_2 < I_r_2[i][j]:
                max_I_r_2 = I_r_2[i][j]
            if max_I_g < g[i][j]:
                max_I_g = g[i][j]
            if max_I_b_2 < I_b_2[i][j]:
                max_I_b_2 = I_b_2[i][j]
            if max_I_b < b[i][j]:
                max_I_b = b[i][j]

    [u_b, v_b] = np.matmul(np.linalg.inv([[sum_I_b_2, sum_I_b], [max_I_b_2, max_I_b]]), [sum_I_g, max_I_g])
    [u_r, v_r] = np.matmul(np.linalg.inv([[sum_I_r_2, sum_I_r], [max_I_r_2, max_I_r]]), [sum_I_g, max_I_g])
    # print(u_b, v_b, u_r, v_r)
    b0, g0, r0 = np.zeros(b.shape, np.uint8), np.zeros(g.shape, np.uint8), np.zeros(r.shape, np.uint8)
    for i in range(m):
        for j in range(n):
            b_point = u_b * (b[i][j] ** 2) + v_b * b[i][j]
            g0[i][j] = g[i][j]
            # r0[i][j] = r[i][j]
            r_point = u_r * (r[i][j] ** 2) + v_r * r[i][j]
            if r_point > 255:
                r0[i][j] = 255
            else:
                if r_point < 0:
                    r0[i][j] = 0
                else:
                    r0[i][j] = r_point
            if b_point > 255:
                b0[i][j] = 255
            else:
                if b_point < 0:
                    b0[i][j] = 0
                else:
                    b0[i][j] = b_point
    return cv2.merge([b0, g0, r0])

def GausBlur(src):
    dst = cv2.GaussianBlur(src, (5, 5), 1.5)
    #cv2.imshow('GausBlur', dst)
    return dst

def Gray_img(src):
    gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    #cv2.imshow('gray', gray)
    return gray


def process(src,image,img_box,draw_or):
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
        min_side_length = float('inf')  # 初始设置为无穷大
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
        cv2.circle(src, (end_point[0], end_point[1]), 5, (0, 0, 255), -1)
        cv2.circle(src, (start_point[0], start_point[1]), 5, (255, 0, 0), -1)

        if end_point[1] < start_point[1]:
            vector = (end_point[0] - start_point[0], end_point[1] - start_point[1])
        else:
            vector = (start_point[0] - end_point[0], start_point[1] - end_point[1])

        # 计算起点到X轴正方向的向量
        reference_vector = (1, 0)

        # 计算起点到终点向量和X轴正方向向量的夹角
        angle = calculate_angle(vector, reference_vector)

        # 将弧度转换为角度
        angle_degrees = math.degrees(angle)

        # print("起点坐标：", start_point)
        # print("终点坐标：", end_point)
        # print("旋转矩形的角度：", angle_degrees)
        #cv2.line(src, start_point, end_point, (255, 0, 0), 6) #绘制偏转角
        #cv2.drawContours(src, [box], -1, (0, 255, 0), 2)
        cv2.line(draw_or, start_point, end_point, (255, 0, 0), 6)  # 绘制偏转角
        cv2.drawContours(draw_or, [box], -1, (0, 255, 0), 2)
        i += 1
    return image,min_side_length,max_side_length,angle_degrees
def fangxiang(src,draw_or,box):
    min_side_length = 10000
    max_side_length = 0
    angle = 0
    if src is not None and np.any(src):
        gaus_img = GausBlur(src)
        gray_img = Gray_img(gaus_img)
        thres_img = threshold_img(gray_img)
        #cv2.imwrite('pic/pic.png', thres_img)
        image = cv2.cvtColor(thres_img, cv2.COLOR_GRAY2BGR)
        result,min_side_length,max_side_length,angle = process(src,image,box,draw_or)
    #cv2.imshow('result', result)
    return min_side_length,max_side_length,angle
def threshold_img(src):
    ret, binary = cv2.threshold(src, 0, 255,  cv2.THRESH_TRIANGLE) #有问题加上cv2.THRESH_BINARY_INV
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

def scan_image(img_path):
    output, or_img = model.inference_pic(img_path)
    outbox = filter_box(output, 0.4, 0.4)
    results = draw(or_img, outbox)
    cv2.imshow('or_img', or_img)
    return results

def scan_video(img):
    output, or_img = model.inference_cam(img)

    outbox = filter_box(output, 0.5, 0.8)
    draw(or_img, outbox)
    cv2.imshow('or_img', or_img)




if __name__ == "__main__":
    results = []
    onnxruntime.get_device()
    model = YOLOV5('best.onnx')
    # results = scan_image('G:/my_Training_set/images/my_other_cobblestone_75.jpg')
    capture = cv2.VideoCapture(1)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1024)
    while True:
        ret, frame = capture.read()
        scan_video((frame))
        cv2.waitKey(15)

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




