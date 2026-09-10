# -*- coding: utf-8 -*-
"""
LPBF 数据预处理脚本
流程：读取原始数据 → 缺失值/异常值处理 → 特征提取 → 标准化 → 输出处理后数据
输出：data/processed/features.csv 与 data/processed/sensor_features.csv
"""
import os
import numpy as np
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..", "data")
RAW = os.path.join(BASE, "raw")
PROC = os.path.join(BASE, "processed")
os.makedirs(PROC, exist_ok=True)


def load_params():
    df = pd.read_csv(os.path.join(RAW, "process_params.csv"))
    return df


def clean_params(df):
    """缺失值/异常值处理：删除含 NaN 行，按 3σ 剔除明显离群工艺参数"""
    df = df.dropna().copy()
    for col in ["laser_power_W", "scan_speed_mm_s", "energy_density_J_mm3"]:
        mu, sigma = df[col].mean(), df[col].std()
        df = df[(df[col] - mu).abs() <= 3 * sigma]
    return df


def add_features(df):
    """构造派生特征：功率密度、线能量、能量密度对数等"""
    df = df.copy()
    df["power_density"] = df["laser_power_W"] / (df["scan_speed_mm_s"] * df["hatch_spacing_um"] * 1e-6)
    df["line_energy_J_mm"] = df["laser_power_W"] / df["scan_speed_mm_s"]
    df["log_energy_density"] = np.log1p(df["energy_density_J_mm3"])
    return df


def normalize(df, cols):
    """Z-score 标准化"""
    df = df.copy()
    for c in cols:
        mu, sigma = df[c].mean(), df[c].std()
        df[c + "_z"] = (df[c] - mu) / (sigma + 1e-8)
    return df


def process_sensor():
    """传感器时序：按 job 分段提取统计特征，并做孤立森林风格的离群标记"""
    sdf = pd.read_csv(os.path.join(RAW, "sensor_timeseries.csv"))
    feats = []
    for job, g in sdf.groupby("job_id"):
        temp = g["melt_pool_temp_C"]
        # 3σ 离群点标记（用于异常检测基线）
        mu, sigma = temp.mean(), temp.std()
        n_out = int((np.abs(temp - mu) > 3 * sigma).sum())
        feats.append({
            "job_id": job,
            "temp_mean": temp.mean(),
            "temp_std": temp.std(),
            "temp_min": temp.min(),
            "temp_max": temp.max(),
            "oxygen_mean": g["oxygen_ppm"].mean(),
            "n_3sigma_outliers": n_out,
            "anomaly_flag": int(n_out > 0),
        })
    fdf = pd.DataFrame(feats)
    return fdf


def main():
    df = load_params()
    n0 = len(df)
    df = clean_params(df)
    df = add_features(df)
    num_cols = ["laser_power_W", "scan_speed_mm_s", "layer_thickness_um",
                "hatch_spacing_um", "energy_density_J_mm3",
                "power_density", "line_energy_J_mm", "log_energy_density"]
    df = normalize(df, num_cols)

    out_csv = os.path.join(PROC, "features.csv")
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    sdf = process_sensor()
    sdf.to_csv(os.path.join(PROC, "sensor_features.csv"), index=False, encoding="utf-8-sig")

    print(f"参数表预处理：{n0} -> {len(df)} 行（清洗后）")
    print(f"输出：{out_csv}")
    print(f"传感器特征：{len(sdf)} 个任务，异常任务 {sdf['anomaly_flag'].sum()} 个")
    print("特征列：", list(df.columns))


if __name__ == "__main__":
    main()
