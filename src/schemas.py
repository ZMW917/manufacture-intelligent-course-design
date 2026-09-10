# -*- coding: utf-8 -*-
"""
Pydantic 请求模型（请求体校验）。

输入 → 处理 → 输出：
  HTTP JSON 请求体 → Pydantic 校验/类型转换 → 结构化对象

仅两个请求模型：
  PredictRequest  4 个工艺参数（float）
  AnomalyRequest  job_id（int）
"""
from pydantic import BaseModel


class PredictRequest(BaseModel):
    """工艺参数预测请求：4 个 float 工艺参数（与 PARAM_COLS 对齐）。"""
    laser_power_W: float
    scan_speed_mm_s: float
    layer_thickness_um: float
    hatch_spacing_um: float


class AnomalyRequest(BaseModel):
    """传感器时序异常检测请求：指定 job_id。"""
    job_id: int
