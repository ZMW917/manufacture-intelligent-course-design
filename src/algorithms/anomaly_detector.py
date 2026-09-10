# -*- coding: utf-8 -*-
"""
LPBF 激光增材制造 · 熔池时序异常检测模块（数据挖掘，对应方案设计 3.5 节）

输入 → 处理 → 输出
==================
输入：单个打印任务（job）的时序 DataFrame，列：
      time_step, melt_pool_temp_C, oxygen_ppm

处理：
  1) 以熔池温度 melt_pool_temp_C 为核心信号，构造滑动窗口特征：
     原始值 / 窗口均值 / 窗口标准差（组成 3 维特征矩阵）
  2) 用 IsolationForest(contamination=固定低值, random_state=42) 无监督检测异常
  3) 叠加 SPC 3σ 规则（mean ± 3*std），标记超限点
  4) 二者取并集得到 anomaly_indices；连续异常点合并为 intervals
  5) 按并集异常点数分级：< warn_threshold = '正常'，< alarm_threshold = '注意'，其余 = '告警'

输出：{'time_step': list, 'melt_pool_temp_C': list, 'oxygen_ppm': list,
       'anomaly_indices': list[int], 'intervals': list[list[int,int]],
       'level': str, 'threshold_upper': float, 'threshold_lower': float}

说明：anomaly_indices / intervals 使用「行索引（0-based 位置）」表示，
     与此处 time_step=0..99 一致；前端可据此在高亮时映射到时间轴。
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

# 预警等级（方案设计定义的档位，非 config 标签，故作为模块常量）
LEVEL_NORMAL = "正常"
LEVEL_WARN = "注意"
LEVEL_ALARM = "告警"


class AnomalyDetector:
    """熔池温度时序异常检测器（IsolationForest + SPC 3σ 并集）。"""

    def __init__(self, window=5, n_sigma=3, contamination=0.01,
                 warn_threshold=3, alarm_threshold=5):
        self.window = int(window)
        self.n_sigma = float(n_sigma)
        self.contamination = contamination
        self.warn_threshold = int(warn_threshold)
        self.alarm_threshold = int(alarm_threshold)

    def detect(self, timeseries: pd.DataFrame) -> dict:
        """对单个 job 的时序执行异常检测并分级。

        :param timeseries: DataFrame，至少含 time_step, melt_pool_temp_C, oxygen_ppm
        :return: 检测结果 dict（结构见模块 docstring）
        """
        df = timeseries.reset_index(drop=True)
        time_step = [int(v) for v in df["time_step"].tolist()]
        oxygen_ppm = [float(v) for v in df["oxygen_ppm"].tolist()]
        temp = df["melt_pool_temp_C"].astype(float).reset_index(drop=True)

        # 1) SPC 3σ 上下限（对整个序列统计）
        mean = float(temp.mean())
        std = float(temp.std(ddof=0)) if len(temp) > 1 else 0.0
        threshold_upper = mean + self.n_sigma * std
        threshold_lower = mean - self.n_sigma * std

        raw = temp.values
        spc_anomaly = np.where(
            (raw > threshold_upper) | (raw < threshold_lower)
        )[0]

        # 2) 滑动窗口特征（原始值 / 均值 / 标准差），供 IsolationForest 使用
        roll_mean = temp.rolling(window=self.window, min_periods=1).mean().values
        roll_std = temp.rolling(window=self.window, min_periods=1).std(ddof=0).values
        roll_std = np.nan_to_num(roll_std, nan=0.0)
        features = np.column_stack([raw, roll_mean, roll_std])

        # 固定较低污染率，避免 'auto' 在纯噪声序列上误标约 10~25% 的点为异常
        iso = IsolationForest(contamination=self.contamination, random_state=42)
        iso_pred = iso.fit_predict(features)          # 1=正常, -1=异常
        iso_anomaly = np.where(iso_pred == -1)[0]

        # 3) 二者并集（去重 + 升序）
        anomaly_indices = sorted(set(iso_anomaly.tolist()) | set(spc_anomaly.tolist()))

        # 4) 连续异常点合并为区间 [[start, end], ...]
        intervals = self._merge_intervals(anomaly_indices)

        # 5) 预警等级（按并集异常点数分级）
        n_anomaly = len(anomaly_indices)
        if n_anomaly < self.warn_threshold:
            level = LEVEL_NORMAL
        elif n_anomaly < self.alarm_threshold:
            level = LEVEL_WARN
        else:
            level = LEVEL_ALARM

        return {
            "time_step": time_step,
            "melt_pool_temp_C": [float(v) for v in raw],
            "oxygen_ppm": oxygen_ppm,
            "anomaly_indices": anomaly_indices,
            "intervals": intervals,
            "level": level,
            "threshold_upper": threshold_upper,
            "threshold_lower": threshold_lower,
        }

    @staticmethod
    def _merge_intervals(indices):
        """把升序的异常点索引合并为连续区间 [[start, end], ...]（闭区间）。"""
        if not indices:
            return []
        intervals = []
        start = prev = indices[0]
        for idx in indices[1:]:
            if idx == prev + 1:          # 连续
                prev = idx
            else:                        # 断开，收束上一段
                intervals.append([start, prev])
                start = prev = idx
        intervals.append([start, prev])
        return intervals
