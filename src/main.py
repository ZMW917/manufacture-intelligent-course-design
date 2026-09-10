# -*- coding: utf-8 -*-
"""
FastAPI 后端服务（端口 8000）。

输入 → 处理 → 输出：
  图像上传   → cv2 解码 + 预处理(ROI/增强) + CNN 分类 → 质量等级（写 image_records）
  工艺参数   → RF/SVR 回归 → 致密度/孔隙率（写 process_records + prediction_history）
  传感器时序 → 孤立森林 + 3σ → 异常检测结果

启动时 init_db() 建表；CNN/回归模型懒加载（模型文件存在才加载，否则 models_loaded=false，
对应接口返回 HTTP 400 并提示先训练）。
"""
import os

import cv2
import numpy as np
import pandas as pd
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.config import (
    RAW_DIR,
    NUM_CLASSES,
    CNN_MODEL_PATH,
    REGRESSOR_PATH,
    ensure_dirs,
)
from src.database import (
    init_db,
    insert_process_record,
    insert_prediction,
    insert_image_record,
    list_predictions,
    list_images,
)
from src.schemas import PredictRequest, AnomalyRequest
from src.algorithms.image_preprocess import preprocess_image, encode_base64
from src.algorithms.cnn_classifier import CNNClassifier
from src.algorithms.regression import QualityRegressor
from src.algorithms.anomaly_detector import AnomalyDetector

# 确保目录并建库建表
ensure_dirs()
init_db()

app = FastAPI(title="LPBF 熔池质量监测系统")

# 允许前端独立 dev 服务器跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 模型懒加载 ----------
# CNN：模型文件存在才加载
cnn_classifier = None
if os.path.exists(CNN_MODEL_PATH):
    try:
        cnn_classifier = CNNClassifier(model_path=CNN_MODEL_PATH, num_classes=NUM_CLASSES)
    except Exception:
        cnn_classifier = None

# 回归：模型文件存在才加载（使用契约中的 load() 方法）
regressor = None
if os.path.exists(REGRESSOR_PATH):
    try:
        regressor = QualityRegressor()
        regressor.load(REGRESSOR_PATH)
    except Exception:
        regressor = None

# 孤立森林无监督、无需训练产物，随用随拟合
anomaly_detector = AnomalyDetector()


# ---------- 1) 健康检查 ----------
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "models_loaded": {
            "cnn": cnn_classifier is not None,
            "regressor": regressor is not None,
            "anomaly": anomaly_detector is not None,
        },
    }


# ---------- 2) 熔池图像分类 ----------
@app.post("/api/classify")
async def classify(file: UploadFile = File(...)):
    if cnn_classifier is None:
        raise HTTPException(status_code=400, detail="模型未训练，请先运行 python -m src.train")

    data = await file.read()
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="无法解析上传的图片文件")

    # 预处理：提取 ROI 与增强图像
    pre = preprocess_image(img)
    input_img = pre.get("enhanced", pre.get("gray", img))
    result = cnn_classifier.predict(input_img)

    # ROI 编码为 base64（用于前端展示）
    roi = pre.get("roi")
    roi_base64 = encode_base64(roi) if roi is not None else None

    # 写图像分类记录
    insert_image_record(
        image_name=file.filename or "unknown.png",
        quality_label=int(result["label"]),
        label_name=result["label_name"],
        confidence=float(result["confidence"]),
    )

    return {
        "label": int(result["label"]),
        "label_name": result["label_name"],
        "confidence": float(result["confidence"]),
        "probs": result["probs"],
        "roi_base64": roi_base64,
    }


# ---------- 3) 工艺参数质量预测 ----------
@app.post("/api/predict")
def predict(req: PredictRequest):
    if regressor is None:
        raise HTTPException(status_code=400, detail="模型未训练，请先运行 python -m src.train")

    params = {
        "laser_power_W": req.laser_power_W,
        "scan_speed_mm_s": req.scan_speed_mm_s,
        "layer_thickness_um": req.layer_thickness_um,
        "hatch_spacing_um": req.hatch_spacing_um,
    }
    result = regressor.predict(params)

    # 写工艺参数记录
    record_id = insert_process_record({
        "laser_power_W": req.laser_power_W,
        "scan_speed_mm_s": req.scan_speed_mm_s,
        "layer_thickness_um": req.layer_thickness_um,
        "hatch_spacing_um": req.hatch_spacing_um,
        "energy_density_J_mm3": result.get("energy_density_J_mm3"),
    })

    # 写预测历史：RF、SVR 各一行
    insert_prediction(record_id, float(result["density_rf"]), float(result["porosity_rf"]), "RF")
    insert_prediction(record_id, float(result["density_svr"]), float(result["porosity_svr"]), "SVR")

    return result


# ---------- 4) 传感器时序异常检测 ----------
@app.post("/api/anomaly")
def anomaly(req: AnomalyRequest):
    csv_path = os.path.join(RAW_DIR, "sensor_timeseries.csv")
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="传感器时序数据文件不存在")

    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    job_df = df[df["job_id"] == req.job_id][["time_step", "melt_pool_temp_C", "oxygen_ppm"]]
    if job_df.empty:
        raise HTTPException(status_code=404, detail=f"job_id={req.job_id} 不存在")

    return anomaly_detector.detect(job_df)


# ---------- 5) 历史记录：预测 ----------
@app.get("/api/history/predictions")
def history_predictions(limit: int = 50, offset: int = 0):
    items, total = list_predictions(limit, offset)
    return {"items": items, "total": total}


# ---------- 6) 历史记录：图像 ----------
@app.get("/api/history/images")
def history_images(limit: int = 50, offset: int = 0):
    items, total = list_images(limit, offset)
    return {"items": items, "total": total}


# ---------- 7) 传感器可用 job 列表 ----------
@app.get("/api/sensors/jobs")
def sensors_jobs():
    csv_path = os.path.join(RAW_DIR, "sensor_timeseries.csv")
    if not os.path.exists(csv_path):
        return {"job_ids": []}

    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    job_ids = sorted(int(x) for x in df["job_id"].unique())
    return {"job_ids": job_ids}
