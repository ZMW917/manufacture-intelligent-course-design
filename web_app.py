# web_app.py
import streamlit as st
import requests

st.set_page_config(page_title="制造智能课程设计", layout="wide")
st.title("🏭 制造智能问答系统")

# 记住历史对话
if "messages" not in st.session_state:
    st.session_state.messages = []

# 展示历史对话
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 输入框
if prompt := st.chat_input("请输入您的问题："):
    # 1. 把用户的问题放到屏幕上
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 把问题发给后端
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            # 这里调用的地址是后端地址
            response = requests.post("http://127.0.0.1:8000/ask", json={"question": prompt})
            data = response.json()
            
            # 3. 显示大模型给出的答案
            full_response = data['answer']
            st.markdown(full_response)
            
            # 4. 额外展示“引用的资料”，显得很专业
            st.divider()
            with st.expander("📚 查看参考来源"):
                for i, source in enumerate(data['sources']):
                    st.write(f"**片段 {i+1}:**")
                    st.write(source)

            # 把机器人的回答存进历史记录
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"请求失败！请检查后端是否启动。错误信息: {e}")

# 启动方式: streamlit run web_app.py