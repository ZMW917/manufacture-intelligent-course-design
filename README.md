# 基于检索增强生成的大模型智能问答系统

> 制造智能课程设计项目 · 2026年秋季学期


## 项目简介

本项目是一个基于**检索增强生成（RAG）** 技术的大模型智能问答系统，面向制造智能课程学习场景开发。系统以课程教材、教学讲义、校园规章制度等文档构建领域知识库，结合大语言模型实现准确、完整、可追溯的自然语言问答。

**核心价值**：通过检索增强生成技术，使大模型能够在回答问题时引用外部知识库，显著提升回答的准确性与可解释性，同时实现答案溯源——每个回答均可追溯到原始文档。


## 项目结构
manufacturing-rag-qa/
│
├── README.md # 项目说明文档（本文件）
│
├── src/ # 源代码目录
│ ├── data_loader/ # 数据加载模块
│ │ ├── init.py
│ │ └── loader.py # 多格式文档加载器（PDF/Word/TXT/Markdown）
│ │
│ ├── preprocessor/ # 数据预处理模块
│ │ ├── init.py
│ │ ├── cleaner.py # 文本清洗（去重/去噪/纠错）
│ │ ├── splitter.py # 文档分块（chunking）
│ │ └── standardizer.py # 格式标准化（JSON+UTF-8）
│ │
│ ├── embedding/ # 向量化模块
│ │ ├── init.py
│ │ └── embedder.py # 嵌入模型封装（调用GTE/API）
│ │
│ ├── retriever/ # 检索模块
│ │ ├── init.py
│ │ ├── vector_store.py # 向量数据库操作（ChromaDB/FAISS）
│ │ └── search.py # 语义相似度检索
│ │
│ ├── generator/ # 生成模块
│ │ ├── init.py
│ │ ├── llm_client.py # 大模型客户端（豆包/DeepSeek接口）
│ │ └── prompt_builder.py # 提示词构建
│ │
│ ├── rag_chain.py # RAG主流程编排
│ ├── config.py # 配置文件（模型参数/路径等）
│ └── main.py # 程序入口（命令行交互）
│
├── data/ # 数据目录
│ ├── public/ # 公开数据集
│ │ ├── THUCNews/ # 清华新闻分类数据集（需自行下载）
│ │ ├── LCQMC/ # 哈工大问句匹配数据集（需自行下载）
│ │ └── README.md # 数据来源说明与引用
│ │
│ ├── knowledge_base/ # 自建知识库
│ │ ├── course_materials/ # 课程教材与讲义（TXT/Markdown格式）
│ │ ├── campus_rules/ # 校园规章制度
│ │ └── lab_manuals/ # 实验室使用说明
│ │
│ ├── qa_pairs/ # 问答评测对
│ │ └── qa_dataset.json # 问题-答案标注数据
│ │
│ ├── processed/ # 预处理后数据（程序自动生成）
│ │ ├── train.json
│ │ ├── valid.json
│ │ └── test.json
│ │
│ └── README.md # 数据目录总体说明
│
├── docs/ # 文档目录
│ ├── 课程设计报告.md # 完整课程设计报告
│ ├── 选题说明.md # 选题说明文档
│ ├── 方案设计.md # 系统方案设计文档
│ └── 答辩PPT/ # 答辩演示文稿
│
├── prompt/ # AI工具提示词追溯目录
│ ├── 01_选题调研/
│ │ ├── PROMPT001_RAG原理讲解.md
│ │ └── PROMPT002_技术路线讨论.md
│ ├── 02_工具学习/
│ │ ├── PROMPT003_LangChain入门.md
│ │ └── PROMPT004_向量数据库选型.md
│ ├── 03_代码开发/
│ │ ├── PROMPT005_预处理程序生成.md
│ │ └── PROMPT006_检索模块调试.md
│ ├── 04_文档撰写/
│ │ └── PROMPT007_报告大纲生成.md
│ ├── 05_问题排查/
│ │ └── PROMPT008_编码错误修复.md
│ ├── 索引文件.json # 提示词索引（结构化元数据）
│ └── 学习笔记.md # 学习笔记与反思
│
├── tests/ # 测试目录
│ ├── test_preprocessor.py # 预处理模块测试
│ ├── test_retriever.py # 检索模块测试
│ └── test_end_to_end.py # 端到端集成测试
│
├── requirements.txt # Python依赖清单
├── .gitignore # Git忽略文件配置
├── setup.py # 项目安装脚本


## 快速开始

### 环境要求

| 要求 | 版本 |
|------|------|
| Python | 3.10+ |
| 内存 | 8GB+ |
| 存储 | 10GB+（含数据） |
| GPU（可选） | 推荐NVIDIA GPU 8GB+，CPU模式也可运行 |


### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-username/manufacturing-rag-qa.git
cd manufacturing-rag-qa

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt
```
依赖清单（requirements.txt）
# 核心框架
langchain>=0.3.0
langchain-community>=0.3.0

# 向量数据库
chromadb>=0.5.0
faiss-cpu>=1.8.0  # GPU: faiss-gpu

# 嵌入模型
sentence-transformers>=2.2.0

# 文档解析
pypdf>=4.0.0
python-docx>=1.1.0
markdown>=3.5.0
openpyxl>=3.1.0

# HTTP客户端（调用大模型API）
requests>=2.31.0

# 数据处理
numpy>=1.24.0
pandas>=2.0.0

# 工具库
tiktoken>=0.5.0
tqdm>=4.66.0
python-dotenv>=1.0.0
配置环境变量
创建 .env 文件并配置大模型API密钥：
# 豆包大模型配置（默认）
DOUBAO_API_KEY=your_api_key_here
DOUBAO_API_URL=https://ark.cn-beijing.volces.com/api/v3/chat/completions
DOUBAO_MODEL=doubao-lite-32k

# 或 DeepSeek 配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# 向量数据库路径
VECTOR_DB_PATH=./data/vector_db/
运行系统
# 1. 预处理数据
python src/main.py --preprocess

# 2. 构建向量索引
python src/main.py --build-index

# 3. 启动问答交互
python src/main.py --query "什么是智能制造？"

# 4. 启动交互式命令行问答
python src/main.py --interactive

# 5. 启动Web界面（如已实现）
使用示例
交互式问答示例
用户: 什么是智能制造？

系统回答:
智能制造是新一代信息技术与先进制造技术的深度融合，贯穿于设计、生产、
管理、服务等制造活动的各个环节。其核心特征包括数字化、网络化、智能化，
旨在实现制造过程的感知、分析、决策、执行的自适应与自优化。

【引用来源】
- 《制造智能导论》教材 第3章 第2节
- 国家智能制造标准体系建设指南（2021版）
- API调用示例
- from src.rag_chain import RAGChain

# 初始化RAG系统
rag = RAGChain()

# 提问并获取答案
result = rag.query("如何解决数控机床的刀具磨损问题？")

print(f"回答: {result['answer']}")
print(f"引用来源: {result['sources']}")
print(f"检索耗时: {result['retrieval_time_ms']}ms")
print(f"生成耗时: {result['generation_time_ms']}ms")
参考资料
技术文档
LangChain官方文档

豆包大模型开发者文档

ChromaDB文档

学术参考
Lewis, P., et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS 2020.

Gao, Y., et al. "Retrieval-Augmented Generation for Large Language Models: A Survey." arXiv:2312.10997, 2023.

数据集来源
THUCTC: http://thuctc.thunlp.org/

LCQMC: https://github.com/liyongqi/Lcqmc

许可证
本项目仅供课程设计教学使用，未经许可不得用于商业用途。
python src/main.py --web
