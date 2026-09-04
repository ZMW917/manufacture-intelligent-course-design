# 示例代码
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 1. 加载文档
loader = PyPDFLoader("data/raw/你的教材.pdf") # 改成你的文件名
documents = loader.load()

# 2. 切分文档
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
texts = text_splitter.split_documents(documents)

print(f"成功将文档切分为 {len(texts)} 个片段")