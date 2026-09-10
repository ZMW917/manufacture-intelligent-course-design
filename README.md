# 数据资源说明

本项目数据分两部分：**公开基准数据集**（真实工业数据，需自行下载）与**本地样例数据集**（合成数据，随仓库提交，供离线 demo 与自动化测试）。

## 一、公开基准数据集（主数据来源）

### 1. NIST AM-Bench 2022（增材制造基准）
- **来源**：美国国家标准与技术研究院（NIST）Additive Manufacturing Benchmark 系列
- **链接**：<https://www.nist.gov/ambench>
- **说明**：AM-Bench 提供多组经标定的增材制造基准数据，其中 LPBF（激光粉末床熔融）挑战含 **熔池几何形貌、温度场与成形件性能（致密度/缺陷）** 的对应测量数据，是增材制造过程—结构—性能建模的权威基准。
- **用途**：本项目熔池图像分类、工艺参数→致密度回归模型的训练/验证基准数据。
- **获取方式**：访问 NIST AM-Bench 页面，按 LPBF 相关 Challenge 下载对应数据集；数据集较大，请勿直接提交至仓库。

### 2. 公开 LPBF 熔池监测数据集（辅助）
- **来源**：公开发表的 LPBF 原位监测数据集（Zenodo / 学术数据集仓库）
- **检索入口**：<https://zenodo.org> 检索关键词 `LPBF melt pool monitoring dataset`；或通过魔搭 <https://modelscope.cn>、飞桨 AI Studio <https://aistudio.baidu.com> 检索"增材制造/熔池"数据集。
- **说明**：此类数据集通常含熔池红外/高速相机图像与逐层传感器（温度、氧含量）时序，用于本项目传感器时序异常检测模块的验证。

## 二、本地样例数据集（随仓库提交）

> ⚠️ 以下为 `scripts/generate_sample_data.py` **程序合成的模拟数据**，仅用于功能演示与自动化测试，**非真实企业/实验数据**。真实数据请按上文公开数据集说明获取。

| 文件/目录 | 说明 |
|---|---|
| `data/raw/images/` | 200 张合成熔池灰度图（64×64，含致密/气孔/裂纹三类形态） |
| `data/raw/process_params.csv` | 200 条工艺参数记录（激光功率、扫描速度、层厚、扫描间距、能量密度、致密度、质量标签） |
| `data/raw/sensor_timeseries.csv` | 6 个打印任务的熔池温度/氧含量时序（含 2 个注入异常任务） |
| `data/processed/features.csv` | 预处理+特征工程+标准化后的参数特征表 |
| `data/processed/sensor_features.csv` | 传感器时序按任务聚合的统计特征与 3σ 异常标记 |

## 三、数据预处理

预处理脚本：`scripts/preprocess.py`，流程：
1. **缺失/异常值处理**：删除含缺失值样本，按 3σ 剔除离群工艺参数；
2. **特征工程**：构造功率密度、线能量、能量密度对数等派生特征；
3. **标准化**：对数值特征做 Z-score 标准化；
4. **传感器聚合**：按打印任务提取均值/方差/极值等统计特征，并以 3σ 规则标记异常。

复现方式：
```bash
python scripts/generate_sample_data.py   # 重新生成样例数据（可选）
python scripts/preprocess.py             # 预处理，输出到 data/processed/
```
