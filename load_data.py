from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 加载文档（把 example.pdf 改成你的实际文件名）
loader = PyPDFLoader("制造智能技术课程设计任务书(1).pdf")
documents = loader.load()
print(f"加载了 {len(documents)} 页文档")

# 2. 切分文档
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
chunks = text_splitter.split_documents(documents)

# 3. 输出结果
print(f"成功将文档切分为 {len(chunks)} 个片段")
print(f"第一个片段预览：{chunks[0].page_content[:100]}...")