# -*- coding: utf-8 -*-
"""
全局配置：路径、标签映射、特征列。
供后端、算法模块、训练脚本共用（所有模块从这里 import，避免硬编码绝对路径）。
"""
import os

# 项目根目录：src/config.py 的上一级目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROC_DIR = os.path.join(DATA_DIR, "processed")
IMAGES_DIR = os.path.join(RAW_DIR, "images")
MODELS_DIR = os.path.join(BASE_DIR, "models")
DB_PATH = os.path.join(BASE_DIR, "app.db")

# 质量标签：0=致密/良好 1=气孔 2=裂纹/未熔合
LABEL_NAMES = {0: "致密/良好", 1: "气孔", 2: "裂纹/未熔合"}
NUM_CLASSES = 3

# 工艺参数特征列（前端表单输入 + 回归模型输入）
PARAM_COLS = ["laser_power_W", "scan_speed_mm_s", "layer_thickness_um", "hatch_spacing_um"]

# 传感器时序列
SENSOR_COLS = ["melt_pool_temp_C", "oxygen_ppm"]

# 训练产物路径
CNN_MODEL_PATH = os.path.join(MODELS_DIR, "cnn_model.pth")
REGRESSOR_PATH = os.path.join(MODELS_DIR, "regressor.joblib")


def ensure_dirs():
    """确保 models/、processed/ 等目录存在。"""
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(PROC_DIR, exist_ok=True)
