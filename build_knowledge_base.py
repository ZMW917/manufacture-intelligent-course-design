from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb

print("="*60)
print("📚 开始构建知识库")
print("="*60)

# 1. 加载和切分 PDF
print("\n📄 步骤1: 加载PDF文档...")
loader = PyPDFLoader("制造智能技术课程设计任务书(1).pdf")
documents = loader.load()
print(f"   ✅ 加载了 {len(documents)} 页")

print("\n✂️ 步骤2: 切分文档...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
chunks = text_splitter.split_documents(documents)
print(f"   ✅ 切分为 {len(chunks)} 个片段")

# 提取纯文本内容
texts = [chunk.page_content for chunk in chunks]
print(f"   ✅ 提取了 {len(texts)} 条文本")

# 2. 初始化嵌入模型
print("\n🤖 步骤3: 加载嵌入模型...")
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print(f"   ✅ 模型加载完成")

# 3. 创建向量数据库
print("\n💾 步骤4: 创建向量数据库...")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="knowledge_base",
    metadata={"description": "制造智能技术课程设计知识库"}
)
print(f"   ✅ 数据库创建完成")

# 4. 生成向量并存入数据库
print("\n📤 步骤5: 生成向量并存入数据库...")
for i, text in enumerate(texts):
    embedding = model.encode(text).tolist()
    collection.add(
        ids=[f"chunk_{i}"],
        embeddings=[embedding],
        documents=[text],
        metadatas=[{"source": "制造智能技术课程设计任务书.pdf", "chunk_index": i}]
    )
    if (i + 1) % 5 == 0:
        print(f"   已处理 {i+1}/{len(texts)} 个片段")

print(f"\n✅ 成功存入 {len(texts)} 个片段到向量数据库")

# 5. 验证
print("\n🔍 步骤6: 验证数据库...")
count = collection.count()
print(f"   📊 数据库中共有 {count} 条记录")

sample = collection.peek(limit=2)
print(f"\n📖 示例数据预览:")
for i, doc in enumerate(sample['documents']):
    print(f"\n   --- 片段 {i+1} ---")
    print(f"   {doc[:150]}...")

print("\n" + "="*60)
print("✅ 知识库构建完成！")
print("="*60)