# -*- coding: utf-8 -*-
"""
算法模块单元测试（离线可过，不依赖网络、不依赖真实训练好的模型权重）。

覆盖点：
  1. image_preprocess.preprocess_image —— 合成 64×64 椭圆灰度图，校验返回字典
     含 roi 且 ROI 尺寸 >= 16×16、roi_bbox 合法（(x,y,w,h) 不越界）。
  2. regression.QualityRegressor —— 若模型未训练（缺 models/regressor.joblib）
     则跳过；否则用构造的工艺参数断言密度预测在 [0.8, 1.0]、孔隙率 = 1 - 密度。
  3. anomaly_detector.AnomalyDetector.detect —— 构造含尖峰的温度序列，
     断言 anomaly_indices 非空、level 不为「正常」、threshold_upper > threshold_lower。
"""
import os

import numpy as np
import pandas as pd
import pytest

# 算法模块随「详细开发」阶段由其他子代理落地，这里按实现契约的精确签名导入。
from src.algorithms.image_preprocess import preprocess_image
from src.algorithms.regression import QualityRegressor
from src.algorithms.anomaly_detector import AnomalyDetector
from src.config import REGRESSOR_PATH


def _make_ellipse_image(size=64, cx=32, cy=32, rx=20, ry=16):
    """合成一张 size×size 的灰度图：中心放一个高亮椭圆，模拟熔池亮斑。"""
    yy, xx = np.mgrid[0:size, 0:size]
    mask = ((xx - cx) ** 2) / (rx ** 2) + ((yy - cy) ** 2) / (ry ** 2) <= 1.0
    img = np.zeros((size, size), dtype=np.uint8)
    img[mask] = 255
    return img


def test_preprocess_image_returns_valid_roi():
    """图像预处理：返回 roi 且尺寸 >=16×16，roi_bbox 为合法的 (x,y,w,h)。"""
    size = 64
    img = _make_ellipse_image(size=size)

    result = preprocess_image(img)

    # 返回类型与关键字段
    assert isinstance(result, dict), "preprocess_image 应返回 dict"
    assert "roi" in result, "返回字典应含 roi"
    assert "roi_bbox" in result, "返回字典应含 roi_bbox"

    # ROI 尺寸应满足 >= 16×16（椭圆长宽轴分别为 40、32，ROI 应明显大于阈值）
    roi = result["roi"]
    h, w = roi.shape[:2]
    assert h >= 16 and w >= 16, f"ROI 尺寸过小：{h}×{w}，预期 >=16×16"

    # roi_bbox 应为 (x, y, w, h) 四元组，且不越界、宽高为正
    bbox = result["roi_bbox"]
    assert isinstance(bbox, (tuple, list)) and len(bbox) == 4, \
        "roi_bbox 应为 (x, y, w, h) 四元组"
    x, y, bw, bh = bbox
    assert bw > 0 and bh > 0, "ROI 宽高必须为正"
    assert x >= 0 and y >= 0, "ROI 左上角坐标不能为负"
    assert x + bw <= size and y + bh <= size, "ROI 边界不能超出原图"


def test_regressor_predict_density_range():
    """回归：密度预测落在 [0.8, 1.0]，孔隙率 = 1 - 密度；未训练则跳过。"""
    # 未训练（缺少训练产物）时直接跳过，保证离线环境下测试可通过。
    if not os.path.exists(REGRESSOR_PATH):
        pytest.skip("回归模型未训练（缺少 models/regressor.joblib），跳过预测断言")

    params = {
        "laser_power_W": 280.0,
        "scan_speed_mm_s": 900.0,
        "layer_thickness_um": 50.0,
        "hatch_spacing_um": 100.0,
    }

    regressor = QualityRegressor(model_path=REGRESSOR_PATH)
    try:
        out = regressor.predict(params)
    except FileNotFoundError as exc:
        pytest.skip(f"回归模型依赖的训练产物缺失：{exc}")

    # 关键字段齐全
    for key in ("density_rf", "density_svr", "porosity_rf", "porosity_svr"):
        assert key in out, f"predict 返回缺少字段：{key}"

    # 致密度是物理量，理论值域为 [0, 1]；正常工艺参数下应在 [0.8, 1.0]
    assert 0.8 <= out["density_rf"] <= 1.0, f"density_rf 越界：{out['density_rf']}"
    assert 0.8 <= out["density_svr"] <= 1.0, f"density_svr 越界：{out['density_svr']}"

    # 孔隙率 = 1 - 致密度（数据中无孔隙率列，契约约定据此派生）
    assert abs(out["porosity_rf"] - (1.0 - out["density_rf"])) < 1e-6
    assert abs(out["porosity_svr"] - (1.0 - out["density_svr"])) < 1e-6


def test_anomaly_detector_detect_spike():
    """异常检测：注入尖峰后应能检出异常，且预警等级不为「正常」。"""
    n = 100
    # 基线温度 1500℃（相对平稳），在 40~44 步注入 +800℃ 尖峰
    temp = np.full(n, 1500.0, dtype=float)
    temp[40:45] += 800.0
    oxy = np.linspace(500.0, 520.0, n)

    df = pd.DataFrame({
        "time_step": np.arange(n),
        "melt_pool_temp_C": temp,
        "oxygen_ppm": oxy,
    })

    detector = AnomalyDetector()
    out = detector.detect(df)

    assert isinstance(out, dict), "detect 应返回 dict"
    assert "anomaly_indices" in out, "返回应含 anomaly_indices"
    assert len(out["anomaly_indices"]) > 0, "注入尖峰后应至少检出 1 个异常点"

    assert "level" in out, "返回应含 level"
    assert out["level"] != "正常", "含尖峰的序列不应被判定为「正常」"

    assert out["threshold_upper"] > out["threshold_lower"], \
        "上阈值应大于下阈值"
