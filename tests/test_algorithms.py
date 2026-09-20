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
from src.algorithms.cnn_classifier import CNNClassifier
from src.algorithms.regression import QualityRegressor
from src.algorithms.anomaly_detector import AnomalyDetector
from src.config import (
    REGRESSOR_PATH,
    CNN_MODEL_PATH,
    IMAGES_DIR,
    RAW_DIR,
    LABEL_NAMES,
)


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


def test_cnn_predict_matches_training_pipeline():
    """CNN：对若干已知样本预测正确，守住 predict() 必须执行与训练一致的预处理。

    对应的是开发中真实踩过的坑：预处理链路在训练与推理之间不一致，离线评估准确率
    0.99，而线上接口实际只有 0.375。本用例约束 predict() 内部必须走
    image_preprocess 提取 ROI 再送网络。实测若绕过这一步（把原始图直接喂给网络），
    这 6 个样本只判对 2 个、全量 200 样本准确率由 0.99 跌至 0.05，故断言必然失败。

    注：本用例只能守住「推理端预处理不被摘掉」；训练端是否同样预处理，
    需靠 train() 的调用链保证，测试内不做重训。
    """
    if not os.path.exists(CNN_MODEL_PATH):
        pytest.skip("CNN 模型未训练（缺少 models/cnn_model.pth），跳过预测断言")

    labels_csv = os.path.join(RAW_DIR, "process_params.csv")
    if not os.path.exists(labels_csv):
        pytest.skip("缺少 data/raw/process_params.csv，跳过")

    import pandas as pd
    df = pd.read_csv(labels_csv, encoding="utf-8-sig")

    clf = CNNClassifier(model_path=CNN_MODEL_PATH, num_classes=3)

    correct = total = 0
    # 每个类别取前 2 个样本，覆盖三类形态
    for label in (0, 1, 2):
        for sid in df[df["quality_label"] == label]["sample_id"].head(2):
            img_path = os.path.join(IMAGES_DIR, "sample_%03d.png" % int(sid))
            if not os.path.exists(img_path):
                continue
            out = clf.predict(img_path)
            assert out["label_name"] in LABEL_NAMES.values()
            assert 0.0 <= out["confidence"] <= 1.0
            assert len(out["probs"]) == 3
            total += 1
            correct += int(out["label"] == label)

    assert total > 0, "未找到可用的样例图像"
    # 训练/推理链路一致时，这几张形态清晰的样本应全部判对
    assert correct == total, (
        "分类结果与标签不符（%d/%d 正确）。请检查 CNNClassifier 的预处理链路"
        "是否与训练时一致（train 与 predict 都应经 image_preprocess 提取 ROI）"
        % (correct, total)
    )


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
