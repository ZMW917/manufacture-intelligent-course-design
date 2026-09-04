import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops

def preprocess_pipeline(img_path):
    # 六步预处理流水线
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)          # 灰度化
    blur = cv2.GaussianBlur(gray, (5,5), sigmaX=0)         # 高斯滤波
    clahe = cv2.createCLAHE(clipLimit=2.0)
    img_clahe = clahe.apply(blur)                          # CLAHE增强
    _, thresh = cv2.threshold(img_clahe,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU) # Otsu分割
    kernel = np.ones((3,3),np.uint8)
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel) #形态学开闭
    edges = cv2.Canny(morph, 50,150)                       # Canny边缘
    return gray, edges

def extract_features(gray, edges):
    """提取几何、GLCM纹理、灰度统计特征"""
    contours,_ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    feat_list = []
    if len(contours)>0:
        cnt = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(cnt)
        perimeter = cv2.arcLength(cnt,True)
        feat_list.extend([area, perimeter]) #几何特征

    #灰度统计
    feat_list.append(np.mean(gray))
    feat_list.append(np.std(gray))

    #GLCM纹理 24维简化示例
    glcm = graycomatrix(gray, distances=[1], angles=[0,np.pi/4,np.pi/2,3*np.pi/4], levels=256, symmetric=True)
    feat_list.append(graycoprops(glcm, 'contrast')[0,0])
    feat_list.append(graycoprops(glcm, 'correlation')[0,0])
    return np.array(feat_list).reshape(1,-1)