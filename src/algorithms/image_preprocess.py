# -*- coding: utf-8 -*-
"""
LPBF 激光增材制造 · 熔池图像预处理模块（机器视觉方向，对应方案设计 3.5 节）

输入 → 处理 → 输出
==================
输入：
  - 单张熔池灰度图（H×W）或彩色图（H×W×3 / H×W×4），numpy ndarray

处理：
  1) 灰度化：彩色图转 8-bit 单通道灰度，浮点图按数值范围归一映射到 [0,255]
  2) 高斯去噪：cv2.GaussianBlur 抑制高斯噪声，保护熔池亮斑边缘
  3) Otsu 阈值分割：自适应阈值把熔池（亮斑前景）与背景分离，取前景外接框作为 ROI
     （ROI 小于 16×16 或无前景时，回退到整幅图）
  4) 直方图均衡增强：cv2.equalizeHist 提升 ROI 对比度，便于前端回显与 CNN 提取特征

输出：
  - dict：{'gray': 灰度图, 'denoised': 去噪图, 'roi': ROI 裁剪图,
           'roi_bbox': (x, y, w, h), 'enhanced': 增强图}
  - encode_base64 另外把 8-bit 单通道图编码为 base64 PNG（供前端回显）

依赖：numpy + OpenCV（cv2），不联网、可离线运行。
"""
import base64

import cv2
import numpy as np

# ROI 最小边长（像素），小于该值视为分割失败，回退到全图
MIN_ROI_SIZE = 16


def _to_gray_uint8(image):
    """把任意输入图统一转换为 8-bit 单通道灰度图。"""
    arr = np.asarray(image)

    if arr.ndim == 3:
        if arr.shape[2] == 3:
            arr = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
        elif arr.shape[2] == 4:
            arr = cv2.cvtColor(arr, cv2.COLOR_BGRA2GRAY)
        else:  # 通道数不是 3/4 时，退化为取第一个通道
            arr = arr[:, :, 0]
    elif arr.ndim != 2:
        raise ValueError("输入图像需为 H×W 或 H×W×3 的 numpy 数组，实际维度: %d" % arr.ndim)

    if arr.dtype != np.uint8:
        # 浮点图：若最大值 <=1 视为 [0,1] 区间，否则按 [min,max] 线性映射到 [0,255]
        arr = arr.astype(np.float32)
        if arr.max() <= 1.0:
            arr = arr * 255.0
        else:
            lo, hi = arr.min(), arr.max()
            if hi > lo:
                arr = (arr - lo) / (hi - lo) * 255.0
            else:
                arr = np.zeros_like(arr)
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    return arr


def preprocess_image(image):
    """对单张熔池图执行「灰度化 -> 高斯去噪 -> Otsu ROI -> 直方图均衡增强」。

    :param image: H×W 或 H×W×3 的 numpy 数组
    :return: {'gray','denoised','roi','roi_bbox':(x,y,w,h),'enhanced'}
    """
    # 1) 灰度化
    gray = _to_gray_uint8(image)
    h, w = gray.shape[:2]

    # 2) 高斯去噪（5×5 核，抑制合成数据中的高斯噪声）
    denoised = cv2.GaussianBlur(gray, (5, 5), 0)

    # 3) Otsu 阈值分割，提取熔池（亮斑）前景区域的外接框作为 ROI
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    ys, xs = np.where(binary > 0)

    if xs.size == 0:
        # 无前景（全黑图），回退全图
        x, y, bw, bh = 0, 0, w, h
        roi = denoised
    else:
        x0, x1 = int(xs.min()), int(xs.max())
        y0, y1 = int(ys.min()), int(ys.max())
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        if bw < MIN_ROI_SIZE or bh < MIN_ROI_SIZE:
            # ROI 小于 16×16，视为分割不可靠，回退全图
            x, y, bw, bh = 0, 0, w, h
            roi = denoised
        else:
            x, y = x0, y0
            roi = denoised[y:y + bh, x:x + bw]

    # 4) 直方图均衡增强（对 ROI 做对比度拉伸）
    enhanced = cv2.equalizeHist(roi)

    return {
        "gray": gray,
        "denoised": denoised,
        "roi": roi,
        "roi_bbox": (x, y, bw, bh),
        "enhanced": enhanced,
    }


def encode_base64(img):
    """将 8-bit 单通道 numpy 灰度图编码为 base64 PNG 字符串（供前端 <img> 回显）。

    :param img: H×W（单通道）numpy 数组
    :return: base64 字符串（不含 "data:image/png;base64," 前缀）
    """
    arr = _to_gray_uint8(img)
    ok, buf = cv2.imencode(".png", arr)
    if not ok:
        raise ValueError("图像编码为 PNG 失败")
    return base64.b64encode(buf.tobytes()).decode("ascii")
