# backend_api.py
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import chromadb
from openai import OpenAI

app = FastAPI()

# 1. 加载模型和数据库（启动时加载一次，不用每次都加载）
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
client_db = chromadb.PersistentClient(path="./chroma_db")
collection = client_db.get_collection("knowledge_base")

# 2. 设置大模型 (如果之前能用 OpenAI，这里就用 OpenAI；如果你换成了国内的 API，把 base_url 换掉即可)
client = OpenAI(
    api_key="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",  # 换成你的真实 Key！
    base_url="https://api.openai.com/v1"
)

# 3. 定义接收数据的格式
class Query(BaseModel):
    question: str

# 4. 定义接口 /ask (前端就是向这个地址发请求)
@app.post("/ask")
def ask(query: Query):
    question = query.question
    
    # --- 检索部分 ---
    q_emb = model.encode(question).tolist()
    results = collection.query(query_embeddings=[q_emb], n_results=3)
    docs = results['documents'][0]
    context = "\n\n".join(docs)

    # --- 构建提示词 ---
    prompt = f"""你是一个智能问答助手。请根据以下参考内容回答用户的问题。
参考内容:
{context}
用户问题: {question}
请用你自己的话总结归纳，不要照抄原文。"""

    # --- 调用大模型生成 ---
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # 或者 deepseek-chat
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content
        return {"answer": answer, "sources": docs}  # 把答案和来源一起返回给前端
    except Exception as e:
        return {"answer": f"大模型调用失败: {e}", "sources": docs}

# 启动方式: uvicorn backend_api:app --reload