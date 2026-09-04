from sentence_transformers import SentenceTransformer
import chromadb
import os

# ================= 新增：引入大模型接口 =================
# 假设你使用了 OpenAI 的接口。如果你的网络无法访问 OpenAI，可以替换为其他本地模型（如 Ollama 等）
# 如果还没安装，请在终端执行: pip install openai
from openai import OpenAI

# 初始化 OpenAI 客户端 (如果你没有 API Key，请去 OpenAI 官网申请一个，或者使用其他兼容 OpenAI 格式的本地服务)
# 注意：如果只是纯本地测试且没有网络，你需要使用本地大模型（例如 Ollama），这里以 OpenAI 为例
client = OpenAI(
    api_key="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",  # 请替换成你自己的 API Key
    base_url="https://api.openai.com/v1"  # 如果用的是国内中转站，请替换为对应的 base_url
)
# ====================================================

print("="*60)
print("🤖 RAG 智能问答系统")
print("="*60)

# 1. 加载嵌入模型
print("\n📥 加载嵌入模型...")
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print("   ✅ 模型加载完成")

# 2. 连接向量数据库
print("\n💾 连接向量数据库...")
client_db = chromadb.PersistentClient(path="./chroma_db")
collection = client_db.get_collection("knowledge_base")
print(f"   ✅ 数据库连接成功，共有 {collection.count()} 条记录")

# 3. 问答函数
def ask_question(question, top_k=3):
    """根据问题检索相关文档，并使用大模型生成回答"""
    
    print(f"\n📝 正在检索问题: {question}")
    print("-" * 50)
    
    # 将问题转换为向量
    question_embedding = model.encode(question).tolist()
    
    # 从向量数据库检索最相关的片段
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k
    )
    
    # 提取检索到的文档
    retrieved_docs = results['documents'][0]
    
    print(f"   ✅ 检索到 {len(retrieved_docs)} 个相关片段")
    
    # 组合上下文
    context = "\n\n".join(retrieved_docs)
    
    # 构造提示词
    prompt = f"""你是一个智能问答助手。请根据以下参考内容回答用户的问题。

参考内容:
{context}

用户问题: {question}

请基于参考内容给出准确、完整的回答。如果参考内容中没有相关信息，请明确告知用户。
回答时请保持简洁、专业。
【注意】请用你自己的话总结归纳，不要大段照抄参考内容！"""

    # ================= 新增：调用大模型生成回答 =================
    try:
        # 调用 OpenAI 接口 (GPT-3.5 或 4)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # 根据需要替换模型名称，如 gpt-4o
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.5  # 控制回答的创造性，0.5 比较稳妥
        )
        
        # 提取大模型生成的最终回答
        answer = response.choices[0].message.content
        
        return {
            "question": question,
            "answer": answer,
            "retrieved_docs": retrieved_docs
        }
        
    except Exception as e:
        return {
            "question": question,
            "answer": f"❌ 大模型调用失败，请检查 API Key 或网络连接。报错信息: {e}",
            "retrieved_docs": retrieved_docs
        }
    # ========================================================

# 4. 交互式问答
print("\n" + "="*60)
print("💬 开始问答 (输入 'exit' 退出)")
print("="*60)

while True:
    question = input("\n❓ 请输入您的问题: ").strip()
    
    if question.lower() in ['exit', 'quit', '退出']:
        print("👋 再见！")
        break
    
    if not question:
        print("⚠️ 请输入有效的问题")
        continue
    
    try:
        result = ask_question(question, top_k=3)
        
        print("\n" + "="*60)
        print("🤖 智能回答:")
        print("-" * 60)
        # 这里只打印大模型生成的最终回答，不再打印原始检索摘要
        print(result['answer'])
        print("="*60)
        
        # 如果你想看看检索到了什么，可以取消下面这行的注释
        # print(f"\n(参考依据: {[doc[:50] for doc in result['retrieved_docs']]})")
        
    except Exception as e:
        print(f"❌ 出错了: {e}")