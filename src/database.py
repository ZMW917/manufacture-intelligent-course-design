# -*- coding: utf-8 -*-
"""
SQLite 数据库访问层（三张表 + 增/查函数）。

输入 → 处理 → 输出：
  工艺参数 / 预测结果 / 图像分类结果 → SQLite 增查 → 记录行或 (items, total)

三张表：
  process_records    工艺参数记录（含能量密度）
  prediction_history 预测历史（RF / SVR 各一行）
  image_records      熔池图像分类记录

created_at 统一使用 datetime.now().isoformat(timespec="seconds")。
"""
import sqlite3
from datetime import datetime

from src.config import DB_PATH

# 建表语句（列名与方案设计对齐，工艺参数列名沿用 CSV 列名）
_SCHEMA = """
CREATE TABLE IF NOT EXISTS process_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  laser_power_W REAL, scan_speed_mm_s REAL, layer_thickness_um REAL, hatch_spacing_um REAL,
  energy_density_J_mm3 REAL, created_at TEXT
);
CREATE TABLE IF NOT EXISTS prediction_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  record_id INTEGER, density_pred REAL, porosity_pred REAL,
  model_type TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS image_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  image_name TEXT, quality_label INTEGER, label_name TEXT, confidence REAL, created_at TEXT
);
"""


def _now():
    """统一时间戳格式（秒级）。"""
    return datetime.now().isoformat(timespec="seconds")


def _get_conn():
    """每次调用新建连接（FastAPI 多线程安全），返回 row_factory=Row 的连接。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """建库建表（幂等）。"""
    conn = _get_conn()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def insert_process_record(d):
    """
    插入一条工艺参数记录，返回自增 id。
    d 需包含：laser_power_W, scan_speed_mm_s, layer_thickness_um, hatch_spacing_um,
              可选 energy_density_J_mm3。
    """
    conn = _get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO process_records
               (laser_power_W, scan_speed_mm_s, layer_thickness_um, hatch_spacing_um,
                energy_density_J_mm3, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                d["laser_power_W"], d["scan_speed_mm_s"],
                d["layer_thickness_um"], d["hatch_spacing_um"],
                d.get("energy_density_J_mm3"), _now(),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def insert_prediction(record_id, density_pred, porosity_pred, model_type):
    """插入一条预测历史，返回自增 id。model_type 为 'RF' 或 'SVR'。"""
    conn = _get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO prediction_history
               (record_id, density_pred, porosity_pred, model_type, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (record_id, density_pred, porosity_pred, model_type, _now()),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def insert_image_record(image_name, quality_label, label_name, confidence):
    """插入一条图像分类记录，返回自增 id。"""
    conn = _get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO image_records
               (image_name, quality_label, label_name, confidence, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (image_name, quality_label, label_name, confidence, _now()),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_predictions(limit=50, offset=0):
    """
    分页查询预测历史，返回 (items, total)。
    item 含：id, laser_power_W, density_pred, porosity_pred, model_type, created_at。
    按 id 倒序（最新在前）。
    """
    conn = _get_conn()
    try:
        total = conn.execute("SELECT COUNT(*) FROM prediction_history").fetchone()[0]
        rows = conn.execute(
            """SELECT ph.id, pr.laser_power_W, ph.density_pred, ph.porosity_pred,
                      ph.model_type, ph.created_at
               FROM prediction_history ph
               LEFT JOIN process_records pr ON ph.record_id = pr.id
               ORDER BY ph.id DESC
               LIMIT ? OFFSET ?""",
            (limit, offset),
        ).fetchall()
        items = [dict(r) for r in rows]
        return items, total
    finally:
        conn.close()


def list_images(limit=50, offset=0):
    """
    分页查询图像分类记录，返回 (items, total)。
    item 含：id, image_name, quality_label, label_name, confidence, created_at。
    按 id 倒序（最新在前）。
    """
    conn = _get_conn()
    try:
        total = conn.execute("SELECT COUNT(*) FROM image_records").fetchone()[0]
        rows = conn.execute(
            """SELECT id, image_name, quality_label, label_name, confidence, created_at
               FROM image_records
               ORDER BY id DESC
               LIMIT ? OFFSET ?""",
            (limit, offset),
        ).fetchall()
        items = [dict(r) for r in rows]
        return items, total
    finally:
        conn.close()
