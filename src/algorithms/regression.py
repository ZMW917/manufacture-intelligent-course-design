# -*- coding: utf-8 -*-
"""
LPBF 激光增材制造 · 熔池质量回归模块（机器学习回归，对应方案设计 3.5 节）

输入 → 处理 → 输出
==================
输入：
  - 训练：process_params.csv（工艺参数 + 致密度 density + 质量标签）
  - 预测：4 个工艺参数的 dict（见 predict 签名）

处理：
  1) 特征 = 4 个工艺参数 config.PARAM_COLS（激光功率/扫描速度/层厚/扫描间距）
     + 派生的体能量密度 energy_density_J_mm3 = laser_power / (scan_speed * layer_thickness * hatch_spacing * 1e-6)
  2) 对特征做 Z-score 标准化（保存训练集 mean/std，预测时复用同一统计量）
  3) 训练 RandomForestRegressor(n_estimators=100, random_state=42) 与 SVR(kernel='rbf')
     分别回归致密度 density；孔隙率 porosity = 1 - density
  4) 训练产物（rf / svr / 特征 mean / std / 特征重要性）用 joblib 保存为 dict

输出：
  - train:  {'rf_r2_density': float, 'svr_r2_density': float, 'rf_importances': dict}
  - predict: {'density_rf', 'density_svr', 'porosity_rf', 'porosity_svr',
              'energy_density_J_mm3', 'feature_importances'}
"""
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn.svm import SVR

from src.config import PARAM_COLS, ensure_dirs

# 派生的能量密度特征名（与 process_params.csv 中的列名一致）
ENERGY_DENSITY_COL = "energy_density_J_mm3"


def compute_energy_density(laser_power, scan_speed, layer_thickness, hatch_spacing):
    """按体能量密度公式派生特征：P / (v * t * h * 1e-6)，单位 J/mm^3。"""
    denom = scan_speed * layer_thickness * hatch_spacing * 1e-6
    if denom <= 0:
        raise ValueError("scan_speed / layer_thickness / hatch_spacing 必须为正数，"
                         "无法计算能量密度")
    return float(laser_power) / denom


class QualityRegressor:
    """工艺参数 -> 致密度/孔隙率 的回归模型（RandomForest + SVR 集成）。"""

    def __init__(self, model_path=None):
        self.rf = None
        self.svr = None
        self.feature_names = None      # PARAM_COLS + energy_density_J_mm3
        self.feature_mean = None       # 训练集各特征均值（Z-score 用）
        self.feature_std = None        # 训练集各特征标准差（Z-score 用）
        self.feature_importances = None  # RF 特征重要性 dict
        self.svr_y_mean = None           # SVR 目标标准化均值（缓解密度量级过小导致的 SVR 退化）
        self.svr_y_std = None            # SVR 目标标准化标准差
        self._trained = False
        if model_path is not None:
            self.load(model_path)

    # ------------------------------------------------------------------ #
    # 训练
    # ------------------------------------------------------------------ #
    def train(self, params_csv) -> dict:
        """读 process_params.csv，训练 RF + SVR，返回训练指标。

        :param params_csv: process_params.csv 路径（str）或已加载的 DataFrame
        :return: {'rf_r2_density', 'svr_r2_density', 'rf_importances'}
        """
        # 1) 读取数据（兼容路径 / DataFrame 两种入参）
        if isinstance(params_csv, pd.DataFrame):
            df = params_csv.copy()
        else:
            df = pd.read_csv(params_csv)

        # 2) 特征 = 4 个工艺参数 + 派生能量密度；目标 = 致密度 density
        x_params = df[list(PARAM_COLS)].astype(float)
        energy = x_params.apply(
            lambda r: compute_energy_density(r[PARAM_COLS[0]], r[PARAM_COLS[1]],
                                             r[PARAM_COLS[2]], r[PARAM_COLS[3]]),
            axis=1,
        )
        self.feature_names = list(PARAM_COLS) + [ENERGY_DENSITY_COL]
        X = np.column_stack([x_params.values, energy.values])
        y_density = df["density"].astype(float).values

        # 3) 划分训练/测试集（固定随机种子保证可复现）
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_density, test_size=0.2, random_state=42
        )

        # 4) Z-score 标准化：统计量只来自训练集，预测时复用
        self.feature_mean = X_train.mean(axis=0)
        self.feature_std = X_train.std(axis=0, ddof=0)
        # 防止某个特征标准差为 0 导致除零
        self.feature_std = np.where(self.feature_std == 0, 1.0, self.feature_std)
        X_train_scaled = (X_train - self.feature_mean) / self.feature_std
        X_test_scaled = (X_test - self.feature_mean) / self.feature_std

        # 5) 训练两个回归器，均预测致密度 density。
        #    SVR 对目标做标准化：density 量级极小（std≈0.02），默认 epsilon=0.1 会让 SVR 退化为近常数，
        #    故先对目标 Z-score，训练后再反变换，使 SVR 真正拟合密度随工艺参数的变化。
        self.svr_y_mean = float(y_train.mean())
        self.svr_y_std = float(y_train.std(ddof=0)) or 1.0
        y_train_scaled = (y_train - self.svr_y_mean) / self.svr_y_std

        self.rf = RandomForestRegressor(n_estimators=100, random_state=42)
        self.rf.fit(X_train_scaled, y_train)
        self.svr = SVR(kernel="rbf")
        self.svr.fit(X_train_scaled, y_train_scaled)

        # 6) 测试集 R^2（对 density 的拟合优度；SVR 预测需反变换回原始量纲）
        rf_r2 = float(r2_score(y_test, self.rf.predict(X_test_scaled)))
        svr_pred = self.svr.predict(X_test_scaled) * self.svr_y_std + self.svr_y_mean
        svr_r2 = float(r2_score(y_test, svr_pred))

        # 7) RF 特征重要性（dict：特征名 -> 重要性）
        self.feature_importances = self._importances_dict(self.rf.feature_importances_)
        self._trained = True

        return {
            "rf_r2_density": rf_r2,
            "svr_r2_density": svr_r2,
            "rf_importances": self.feature_importances,
        }

    # ------------------------------------------------------------------ #
    # 预测
    # ------------------------------------------------------------------ #
    def predict(self, params: dict) -> dict:
        """给定 4 个工艺参数，预测致密度与孔隙率。

        :param params: {"laser_power_W":.., "scan_speed_mm_s":..,
                        "layer_thickness_um":.., "hatch_spacing_um":..}
        :return: {'density_rf', 'density_svr', 'porosity_rf', 'porosity_svr',
                  'energy_density_J_mm3', 'feature_importances'}
        """
        if not self._trained:
            raise RuntimeError("模型尚未训练或加载，请先调用 train() 或 load()")

        # 1) 逐特征取值（校验缺失字段）
        try:
            laser = float(params[PARAM_COLS[0]])
            speed = float(params[PARAM_COLS[1]])
            thick = float(params[PARAM_COLS[2]])
            hatch = float(params[PARAM_COLS[3]])
        except KeyError as exc:
            raise ValueError("缺少工艺参数: %s" % exc.args[0])

        # 2) 派生能量密度特征（与训练时同一公式）
        energy = compute_energy_density(laser, speed, thick, hatch)
        x_raw = np.array([[laser, speed, thick, hatch, energy]], dtype=float)

        # 3) 用训练集 mean/std 做 Z-score 标准化
        x_scaled = (x_raw - self.feature_mean) / self.feature_std

        # 4) 预测致密度并裁剪到 [0, 1]（孔隙率 = 1 - 致密度）
        density_rf = float(np.clip(self.rf.predict(x_scaled)[0], 0.0, 1.0))
        density_svr = float(np.clip(self.svr.predict(x_scaled)[0] * self.svr_y_std + self.svr_y_mean, 0.0, 1.0))
        porosity_rf = 1.0 - density_rf
        porosity_svr = 1.0 - density_svr

        return {
            "density_rf": density_rf,
            "density_svr": density_svr,
            "porosity_rf": porosity_rf,
            "porosity_svr": porosity_svr,
            "energy_density_J_mm3": energy,
            "feature_importances": self.feature_importances,
        }

    # ------------------------------------------------------------------ #
    # 持久化
    # ------------------------------------------------------------------ #
    def save(self, path):
        """把 rf / svr / 特征统计量与重要性用 joblib 存成 dict。"""
        if not self._trained:
            raise RuntimeError("模型尚未训练，无法保存")
        ensure_dirs()
        bundle = {
            "rf": self.rf,
            "svr": self.svr,
            "feature_names": self.feature_names,
            "feature_mean": self.feature_mean,
            "feature_std": self.feature_std,
            "feature_importances": self.feature_importances,
            "svr_y_mean": self.svr_y_mean,
            "svr_y_std": self.svr_y_std,
        }
        joblib.dump(bundle, path)
        return path

    def load(self, path):
        """从 joblib 文件恢复模型与标准化统计量。"""
        if not os.path.exists(path):
            raise FileNotFoundError("模型文件不存在: %s" % path)
        bundle = joblib.load(path)
        self.rf = bundle["rf"]
        self.svr = bundle["svr"]
        self.feature_names = bundle["feature_names"]
        self.feature_mean = bundle["feature_mean"]
        self.feature_std = bundle["feature_std"]
        self.feature_importances = bundle["feature_importances"]
        self.svr_y_mean = bundle["svr_y_mean"]
        self.svr_y_std = bundle["svr_y_std"]
        self._trained = True
        return self

    # ------------------------------------------------------------------ #
    # 工具
    # ------------------------------------------------------------------ #
    def _importances_dict(self, importances) -> dict:
        """把 RF 的重要性数组转成 {特征名: 重要性(float)}。"""
        return {
            name: float(imp)
            for name, imp in zip(self.feature_names, importances)
        }
