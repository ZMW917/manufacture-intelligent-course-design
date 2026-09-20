# Prompt 追溯记录

本目录保存课程设计过程中与 AI 编程工具（Claude Code + DeepSeek-v4）的对话/提示词记录，按阶段持续更新。

- 记录格式：JSON（UTF-8），每个条目含 `id`、`stage`、`task`（我给 AI 的指令/提示词）、`tool`、`model`、`result_summary`（AI 产出摘要）、`notes`。
- 需在**上下文压缩前及时备份**，确保追溯完整。

## 当前记录文件

| 文件 | 阶段 | 内容 |
|---|---|---|
| `stage1_topic_research.json` | 选题调研 | 拉取 61 个同学仓库选题并汇总，用于选题避重 |
| `stage2_data_and_docs.json` | 数据与文档 | 生成样例数据、预处理、撰写选题说明/方案设计/学习笔记 |
| `stage3_detailed_dev.json` | 详细开发 | 设计契约、并行实现、集成调试、训练与验证 |
