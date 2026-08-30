# manufacture-intelligent-course-design
制造智能技术课程设计，基于Vibe‑Coding开发工业场景智能应用，包含前端、后端、数据库、算法模块；课程设计全部源码、prompt日志、过程文档
# 制造智能课程设计

制造智能技术课程设计，基于Vibe-Coding开发工业场景智能应用，包含前端、后端、数据库、算法模块；课程设计全部源码、prompt日志、过程文档
# 制造智能课程设计：基于机器视觉的工件表面缺陷检测系统

运用 Vibe Coding 开发方法，实现的一套 B/S 架构可运行 Demo 系统。系统面向制造业产品质量检测环节，围绕「数据采集 - 缺陷识别 - 结果展示 - 持续优化」全业务链条，验证制造智能技术在视觉质检场景的落地应用。

## 项目概况

- **拟定题目**：制造智能课程设计：基于机器视觉的工件表面缺陷检测系统
- **技术方向**：工业大数据预处理与特征工程、制造过程质量智能检测与控制、制造工艺追溯与参数优化（覆盖《制造智能技术》课程 3 个核心专题）
- **架构**：前端展示层（Vue3 + Element Plus + ECharts）/ 后端服务层（FastAPI）/ 算法引擎层（scikit-learn）/ 数据存储层（MySQL + SQLite）
- **核心功能**：图像数据上传 → 缺陷智能检测（2 类状态：合格/缺陷）→ 检测结果展示 → 质量统计追溯 → 检测参数优化

## 项目结构

```text
├── 选题说明.md          # 选题与目标
├── 方案设计.md          # 系统方案设计
├── 数据资源整理说明.md  # 数据资源规划（详细方案）
├── 学习笔记.md          # Vibe Coding / Git / AI 工具学习笔记
├── data/                # 数据集（原始数据 + 预处理特征）
│   ├── raw/             # 原始图像数据（表面缺陷数据集）
│   ├── processed/       # 预处理后图像 + 索引文件（index.csv）
│   └── README.md        # 数据说明文档
├── algorithms/          # 核心算法模块（三模块 + 训练产物）
│   ├── feature_extraction.py   # 模块一：图像特征提取（HOG/LBP）
│   ├── quality_detection.py    # 模块二：缺陷质量检测（分类模型）
│   ├── process_optimization.py # 模块三：工艺参数优化（超参数调优）
│   └── models/                 # 训练产物（模型文件 + 评估报告）
├── backend/             # FastAPI 后端服务
│   ├── main.py          # 应用入口
│   ├── requirements.txt # 依赖清单
│   └── app/             # 配置 + 服务层 + 路由层
├── frontend/            # Vue3 前端（四大页面）
│   ├── package.json     # 依赖与脚本
│   ├── vite.config.js   # 构建 + /api 代理配置 
│   └── src/
│       ├── views/       # 检测大屏 / 检测分析 / 质量追溯 / 数据管理
│       ├── components/  # 通用图表组件
│       └── api/         # 后端接口封装
├── tests/               # 单元测试（unittest）
├── prompt/              # AI 交流提示词追溯记录
├── task_plan.md         # 任务规划
├── findings.md          # 调研发现
└── progress.md          # 进度记录
 ```
## 数据来源

- 数据名称：Surface Defect Detection Dataset（表面缺陷检测数据集）
- 来源：https://github.com/stephan-akermann/surface-defect-detection
- 用途：训练模型分辨工件是合格还是有缺陷
- 原始图片位置：`/data/raw`
- 处理后图片位置：`/data/processed`
##数据快速复现
python data/preprocess.py      # 预处理 + 标签生成 + 划分

##核心算法与后端
对应课程三大技术方向，实现三个算法模块并封装为 FastAPI 后端服务（详见 backend/README.md）。

三大算法模块

图像特征提取	    工业大数据预处理与特征工程	     HOG/LBP 特征提取 + PCA 降维              提取128 维特征
缺陷质量检测	     质量智能检测与控制            	随机森林（主，网格搜索）+ SVM/CNN 对比	     测试集准确率 ≥ 95%
质量追溯与优化	  工艺追溯与参数优化	             特征关联分析 + 超参数网格搜索	           输出最优参数组合

##后端接口
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000   # 文档 /docs
要接口：POST /api/detect（单张图像检测）、POST /api/detect/batch（批量检测）、GET /api/stats（质量统计）、POST /api/optimize（参数优化）、GET /api/trace（检测追溯）。

##前端（Vue3 + Element Plus + ECharts）


缺陷检测大屏	     /api/stats /api/trace	         合格率/缺陷分布 + 实时检测滚动 + 质量趋势
缺陷检测分析	     /api/detect /api/detect/batch	 单张/批量图片检测 + 检测结果展示 + 置信度显示
质量追溯查询	     /api/trace	                     多条件组合检索 + 检测历史详情
数据管理	前端      localStorage                   演示 CRUD	检测记录/工单信息 增删改查
cd frontend && npm install
npm run dev            # 前端 5173，经 /api 代理到后端 8000
npm run build          # 生产构建输出 dist/

开发计划


一	               选题与需求设计	         选题说明、方案设计	                  ✅ 完成
二	               数据准备与数据库设计    	数据集、预处理脚本、数据库设计	        ✅ 完成
三	               核心算法与后端开发	       算法模块、后端接口	                  ⏳ 待开始
四	               前端开发与系统联调	       前端代码、可运行 Demo             	⏳ 待开始
五	               文档撰写与答辩准备	       设计报告、演示视频、答辩 PPT	        ⏳ 待开始


## 数据预处理

1. 将所有图片统一缩放至 224x224 像素
2. 将 .tif 格式转换为 .jpg 格式
3. 根据文件名自动生成标签（defect=有缺陷，ok/good=合格）
4. 生成 index.csv 索引文件，记录每张图片的信息

