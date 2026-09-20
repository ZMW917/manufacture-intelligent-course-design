# 数据资源说明

本项目数据分两部分：

1. **自建数据集**（合成熔池监测数据）——已开源至 Hugging Face，链接见第二节。随仓库提交一份副本供离线 demo 与自动化测试；
2. **公开基准数据集**（真实工业数据）——需自行下载，用于真实场景验证，链接见第一节。

本项目**未使用任何私有敏感数据**。

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

## 二、自建数据集（已开源，随仓库提交副本）

**数据集名称**：LPBF 熔池监测与成形质量合成数据集

**开源地址（Hugging Face）**：<https://huggingface.co/datasets/zoumingwu/lpbf-melt-pool-quality-dataset>

**性质声明**：本数据集为**自建数据集**，由 `scripts/generate_sample_data.py` **程序合成**，
**非真实企业数据、亦非真实实验数据**，仅供功能演示、算法验证与自动化测试使用，不可用于产线决策。
生成脚本随机种子固定（参数流 42 / 图像流 2024），结果完全可复现。

数据集将熔池图像、工艺参数与传感器时序三路数据按 `sample_id` / `job_id` 对齐，
覆盖 LPBF 过程质量控制中的分类、回归、异常检测三类任务。

| 文件/目录 | 规模 | 说明 |
|---|---|---|
| `data/raw/images/` | 200 张 | 合成熔池灰度图（64×64）。三类形态可辨识：致密=规整椭圆亮斑；气孔=亮斑内叠加 3–6 个暗色圆形孔洞；裂纹/未熔合=细长亮斑（长宽比约 2.4） |
| `data/raw/process_params.csv` | 200 条 × 8 列 | 工艺参数（激光功率/扫描速度/层厚/扫描间距）、派生体能量密度、致密度、质量标签 |
| `data/raw/sensor_timeseries.csv` | 600 条 × 4 列 | 6 个打印任务 × 100 时间步的熔池温度与氧含量时序，其中 job 0、job 3 在第 45–49 步注入温度尖峰 |
| `data/processed/features.csv` | 197 条 × 19 列 | 清洗 + 特征工程 + Z-score 标准化后的参数特征表（3σ 剔除 3 条离群样本） |
| `data/processed/sensor_features.csv` | 6 条 × 8 列 | 传感器时序按任务聚合的统计特征与 3σ 异常标记 |

**质量标签定义与分布**（200 条样本，存在类别不平衡）：

| 标签 | 类别 | 样本数 | 占比 |
|---|---|---|---|
| 0 | 致密/良好 | 151 | 75.5% |
| 1 | 气孔 | 39 | 19.5% |
| 2 | 裂纹/未熔合 | 10 | 5.0% |

**引用格式**：

```
邹明吾. LPBF 熔池监测与成形质量合成数据集[DB/OL]. Hugging Face, 2026.
https://huggingface.co/datasets/zoumingwu/lpbf-melt-pool-quality-dataset
```

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
