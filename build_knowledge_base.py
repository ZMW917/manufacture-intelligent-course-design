import chromadb
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 1. 准备你已有的文本片段（假设已经切分好了）
# 这里用一个简单示例，你可以替换成自己从PDF加载的内容
raw_text = """
制造智能是智能制造的核心领域，涉及人工智能、大数据、物联网等技术。
它通过感知、分析、决策、执行实现制造过程的优化。
"""

# 2. 文本切分（如果还没有切分的话）
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,  # 每块字符数
    chunk_overlap=20 # 块间重叠
)
texts = text_splitter.split_text(raw_text)

# 3. 初始化ChromaDB（使用内存模式，适合课程设计演示）
client = chromadb.Client()
collection = client.create_collection(name="manufacturing_kb")

# 4. 添加文档到向量库
collection.add(
    documents=texts,  # 文本内容
    ids=[f"doc_{i}" for i in range(len(texts))]  # 唯一ID
)

print(f"成功将 {len(texts)} 个文档片段存入向量库")