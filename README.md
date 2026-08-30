# manufacture-intelligent-course-design
制造智能技术课程设计，基于Vibe‑Coding开发工业场景智能应用，包含前端、后端、数据库、算法模块；课程设计全部源码、prompt日志、过程文档
# 制造智能课程设计

制造智能技术课程设计，基于Vibe-Coding开发工业场景智能应用，包含前端、后端、数据库、算法模块；课程设计全部源码、prompt日志、过程文档

## 数据来源

- 数据名称：Surface Defect Detection Dataset（表面缺陷检测数据集）
- 来源：https://github.com/stephan-akermann/surface-defect-detection
- 用途：训练模型分辨工件是合格还是有缺陷
- 原始图片位置：`/data/raw`
- 处理后图片位置：`/data/processed`

## 数据预处理

1. 将所有图片统一缩放至 224x224 像素
2. 将 .tif 格式转换为 .jpg 格式
3. 根据文件名自动生成标签（defect=有缺陷，ok/good=合格）
4. 生成 index.csv 索引文件，记录每张图片的信息
