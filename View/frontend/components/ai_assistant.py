import streamlit as st
import sys
import os

# Add models path
# View/frontend/components -> View/models
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
models_dir = os.path.join(project_root, 'View', 'models')

if models_dir not in sys.path:
    sys.path.append(models_dir)

try:
    from text.qwen_model import QwenModel
except ImportError:
    # Fallback
    pass

def show_ai_assistant():
    st.title("🤖 AI 智能助手 (Qwen)")
    st.markdown("基于通义千问大模型的智能对话助手")
    
    # Sidebar configuration
    with st.sidebar:
        st.divider()
        st.header("🤖 模型配置")
        api_key = st.text_input("DashScope API Key", type="password", help="请输入阿里云 DashScope API Key")
        model_select = st.selectbox("选择模型", ["qwen-turbo", "qwen-plus", "qwen-max"], index=0)
        
        if api_key:
            os.environ["DASHSCOPE_API_KEY"] = api_key
        
        if st.button("清除对话历史"):
            st.session_state.messages = []
            st.rerun()
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("有什么可以帮您的吗？"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Call Qwen Model
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")
            
            try:
                # Ensure QwenModel is imported
                from text.qwen_model import QwenModel
                
                model = QwenModel(api_key=api_key if 'api_key' in locals() and api_key else None, model_name=model_select)
                
                # Prepare history for model (excluding the last user message which is passed as input)
                history = st.session_state.messages[:-1]
                
                response = model.predict(prompt, history=history)
                
                if response.get("status") == "success":
                    full_response = response.get("text", "")
                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    error_msg = response.get("text", "未知错误")
                    message_placeholder.error(error_msg)
                    if "API Key missing" in error_msg:
                        st.info("请在左侧侧边栏输入您的 DashScope API Key。")
            except Exception as e:
                message_placeholder.error(f"发生错误: {str(e)}")
