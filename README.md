# 基于机器视觉与深度学习的激光增材制造（LPBF）熔池在线监测与成形质量智能预测系统

《制造智能技术》课程设计项目（智造24-1-28 邹明吾）。

面向金属增材制造（激光粉末床熔融，LPBF）的质量控制场景，构建一套 B/S 架构的智能应用，对熔池图像与工艺/传感器数据进行采集、监测、预测与预警，实现"图像上传 → 熔池监测 → 成形质量预测 → 异常预警"的完整业务闭环。

## 技术方向覆盖（对应《制造智能技术》课程专题）

| 课程专题方向 | 本项目方法 | 系统作用 |
|---|---|---|
| 计算机视觉 / 机器视觉 | OpenCV 图像预处理、ROI 提取、增强 | 熔池图像清洗与特征可视化 |
| 深度学习 | CNN（ResNet-18）图像缺陷/质量分类 | 图像级成形质量判定 |
| 机器学习 | 随机森林、SVR 工艺参数回归 | 参数驱动的致密度/孔隙率预测 |
| 数据挖掘 | 孤立森林 + 统计过程控制（SPC） | 传感器时序异常检测与预警 |

## 技术栈

- **前端**：Vue 3 + Element Plus + ECharts
- **后端**：Python 3.9+ + FastAPI
- **数据库**：SQLite
- **算法**：PyTorch、scikit-learn、OpenCV、NumPy、Pandas
- **测试**：pytest
- **Vibe Coding**：Claude Code（Harness）+ DeepSeek-v4（模型）

## 目录结构

```
├── README.md            # 项目说明（本文件）
├── 选题说明.md          # 选题说明
├── 方案设计.md          # 方案设计
├── 学习笔记.md          # 学习笔记
├── 选题汇总.md          # 61 个同学选题汇总（选题调研产物）
├── requirements.txt     # Python 依赖清单
├── conftest.py          # pytest 根配置（保证 import src.*）
├── data/                # 数据（raw 原始样例 + processed 预处理后）
├── prompt/              # AI 对话记录（JSON）
├── src/                 # 后端与算法模块
│   ├── config.py        #   全局配置（路径/标签/特征列）
│   ├── database.py      #   SQLite 三张表 + 增查
│   ├── schemas.py       #   Pydantic 请求模型
│   ├── train.py         #   训练入口（python -m src.train）
│   ├── main.py          #   FastAPI 应用（7 个接口）
│   └── algorithms/      #   算法模块
│       ├── image_preprocess.py   # OpenCV 图像预处理/ROI 提取
│       ├── cnn_classifier.py     # CNN（ResNet-18）熔池图像分类
│       ├── regression.py         # RF/SVR 工艺参数回归
│       └── anomaly_detector.py   # 孤立森林 + SPC 异常检测
├── frontend/            # 前端（Vue3 + Vite + Element Plus + ECharts）
│   └── src/views/       #   熔池监测 / 质量预测 / 异常预警 / 历史记录
├── tests/               # pytest 自动化测试
├── models/              # 训练产物（cnn_model.pth / regressor.joblib）
└── scripts/
    ├── generate_sample_data.py   # 生成合成样例数据
    ├── preprocess.py             # 数据预处理
    └── run_backend.py            # 一键启动后端
```

## 数据说明

数据集分两部分，详见 [data/README.md](data/README.md)：

1. **公开基准数据集**（真实数据，需自行下载，不随仓库提交）：
   - 主数据集：NIST AM-Bench 2022（增材制造基准，<https://www.nist.gov/ambench>），含 LPBF 熔池几何/温度与成形性能数据；
   - 辅助数据集：公开 LPBF 熔池监测数据集（Zenodo / ModelScope / 飞桨 AI Studio 检索）。
2. **本地样例数据集**（合成数据，随仓库提交，仅供离线 demo 与自动化测试）：由 `scripts/generate_sample_data.py` 生成，**非真实企业数据**。

## 快速开始

> 💡 **Windows 一键启动**：直接双击根目录的 `一键启动.bat`，脚本会自动检查依赖、训练模型（如缺失），并同时启动后端与前端两个服务窗口。

### 0. 环境准备

```bash
# Python 3.9+，安装后端与算法依赖
pip install -r requirements.txt

# 前端依赖（首次）
cd frontend && npm install && cd ..
```

### 1. 数据准备（可选，仓库已包含合成样例）

```bash
python scripts/generate_sample_data.py   # 生成合成样例数据
python scripts/preprocess.py             # 预处理，输出 data/processed/
```

### 2. 训练模型

```bash
python -m src.train        # 训练 CNN + RF/SVR，产物写入 models/
```

### 3. 启动后端（FastAPI，端口 8000）

```bash
python scripts/run_backend.py
# 或：uvicorn src.main:app --host 0.0.0.0 --port 8000
# 自动文档：http://localhost:8000/docs
```

### 4. 启动前端（Vite，端口 5173）

```bash
cd frontend && npm run dev
# 浏览器打开 http://localhost:5173
```

### 5. 运行测试

```bash
pytest tests/ -q
```

## 功能模块

| 模块 | 后端接口 | 前端页面 |
|---|---|---|
| 熔池图像在线监测 | POST /api/classify | 熔池监测（上传图像 → CNN 分类 + ROI 回显） |
| 工艺参数质量预测 | POST /api/predict | 质量预测（工艺参数 → RF/SVR 致密度/孔隙率） |
| 传感器时序异常检测 | POST /api/anomaly | 异常预警（ECharts 时序 + 异常区间 + 预警等级） |
| 历史记录查询 | GET /api/history/* | 历史记录（预测/图像记录分页） |

## 进度

- [x] 选题与方案设计（`选题说明.md` / `方案设计.md`）
- [x] 数据资源整理（`data/`，含合成样例数据与预处理）
- [x] 学习笔记与 AI 工具学习（`学习笔记.md` / `prompt/`）
- [x] 详细开发（`src/` 后端与算法模块 + `frontend/` 前端 + `tests/` 测试，训练与测试全通过）
- [ ] 集成调试与设计报告撰写
- [ ] 演示视频与答辩 PPT
