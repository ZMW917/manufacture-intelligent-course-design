# -*- coding: utf-8 -*-
"""
后端 API 测试（用 fastapi.testclient.TestClient 直连 src.main:app，离线可过）。

覆盖点：
  1. GET  /api/health             —— 200 且含 status 字段。
  2. POST /api/predict            —— 模型未训练则 400 且中文错误提示；否则 200 且含
                                     density_rf 字段（容错断言，两种结果均判通过）。
  3. POST /api/anomaly            —— job_id=0（已知含异常），200 且含 level 字段、
                                     anomaly_indices 为 list。
  4. GET  /api/history/predictions —— 200 且含 items / total。
  5. GET  /api/sensors/jobs       —— 200 且 job_ids == [0,1,2,3,4,5]。

说明：health / anomaly / history / jobs 均不依赖训练权重，离线即可通过；
predict 采用容错断言，未训练与已训练两种状态都能通过。
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """模块级 TestClient：延迟导入 app，确保 conftest 的 sys.path 先生效。"""
    from src.main import app
    with TestClient(app) as c:
        yield c


def _contains_chinese(text):
    """判断字符串中是否含中文字符。"""
    return any("一" <= ch <= "鿿" for ch in str(text))


def test_health(client):
    """GET /api/health 返回 200 且含 status 字段。"""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body


def test_predict(client):
    """POST /api/predict：未训练 -> 400 + 中文错误；已训练 -> 200 + density_rf。"""
    payload = {
        "laser_power_W": 280.0,
        "scan_speed_mm_s": 900.0,
        "layer_thickness_um": 50.0,
        "hatch_spacing_um": 100.0,
    }
    resp = client.post("/api/predict", json=payload)

    if resp.status_code == 400:
        # 后端模型未训练：应返回 400 且带中文错误提示
        detail = resp.json().get("detail", "")
        assert _contains_chinese(detail), "未训练时错误提示应包含中文"
    else:
        # 已训练：正常返回 200 且含 density_rf 字段
        assert resp.status_code == 200
        body = resp.json()
        assert "density_rf" in body


def test_anomaly(client):
    """POST /api/anomaly（job_id=0，已知含异常）：200 且含 level、anomaly_indices。"""
    resp = client.post("/api/anomaly", json={"job_id": 0})
    assert resp.status_code == 200
    body = resp.json()
    assert "level" in body
    assert isinstance(body.get("anomaly_indices"), list), "anomaly_indices 应为 list"


def test_history_predictions(client):
    """GET /api/history/predictions 返回 200 且含 items / total。"""
    resp = client.get("/api/history/predictions")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body


def test_sensors_jobs(client):
    """GET /api/sensors/jobs 返回 200 且 job_ids == [0,1,2,3,4,5]。"""
    resp = client.get("/api/sensors/jobs")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("job_ids") == [0, 1, 2, 3, 4, 5]
