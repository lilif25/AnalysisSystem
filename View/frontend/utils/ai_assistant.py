import streamlit as st
import uuid
import sys
import os

# Add models path
current_dir = os.path.dirname(os.path.abspath(__file__))
# View/frontend/utils -> View/frontend -> View -> View/models
models_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'models')
if models_dir not in sys.path:
    sys.path.append(models_dir)

try:
    from text.qwen_model import QwenModel
except ImportError:
    QwenModel = None

# -----------------------------------------------------------------------------
# AI 助手对话框组件
# -----------------------------------------------------------------------------
@st.dialog("🤖 AI 智能助手", width="large")
def ai_assistant_dialog():
    # 自定义样式
    st.markdown("""
        <style>
        .stButton button {
            border-radius: 8px;
            height: auto;
            padding: 0.5rem 1rem;
        }
        div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
            gap: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.caption("我是您的专属数据分析助手，您可以问我关于评论分析的任何问题。")
    
    # 初始化会话状态
    if "ai_sessions" not in st.session_state:
        st.session_state.ai_sessions = {
            "session_default": {"title": "默认对话", "messages": [{"role": "assistant", "content": "您好！我是AI助手，有什么可以帮您？"}]}
        }
    if "current_ai_session" not in st.session_state:
        st.session_state.current_ai_session = "session_default"

    # 布局：左侧历史，右侧对话
    col_history, col_chat = st.columns([1, 3], gap="medium")
    
    with col_history:
        # 侧边栏容器
        with st.container(border=True):
            st.markdown("### ⚙️ 设置")
            with st.expander("模型配置", expanded=False):
                default_key = os.getenv("DASHSCOPE_API_KEY", "")
                api_key = st.text_input("API Key", value=default_key, type="password", key="dialog_api_key", help="请输入阿里云 DashScope API Key")
                model_name = st.selectbox("模型", ["qwen-turbo", "qwen-plus", "qwen-max"], key="dialog_model_select")
            
            if st.button("➕ 新建对话", use_container_width=True, type="primary"):
                new_id = f"session_{str(uuid.uuid4())[:8]}"
                st.session_state.ai_sessions[new_id] = {"title": "新对话", "messages": [{"role": "assistant", "content": "您好！有什么可以帮您？"}]}
                st.session_state.current_ai_session = new_id
                st.rerun()
            
            st.markdown("---")
            
            st.markdown("### 🕒 历史对话")
            # 历史会话列表容器，限制高度并允许滚动
            with st.container(height=300):
                # 逆序显示，最新的在上面
                session_ids = list(st.session_state.ai_sessions.keys())
                for s_id in reversed(session_ids):
                    s_info = st.session_state.ai_sessions[s_id]
                    # 高亮当前会话
                    is_active = s_id == st.session_state.current_ai_session
                    type_ = "secondary" # 默认样式
                    
                    # 使用 emoji 区分状态
                    icon = "🟢" if is_active else "💬"
                    label = f"{icon} {s_info['title']}"
                    
                    if st.button(label, key=f"btn_{s_id}", use_container_width=True, type=type_, help=s_info['title']):
                        st.session_state.current_ai_session = s_id
                        st.rerun()
        
 
                
    with col_chat:
        # 确保获取有效的 session_id
        if st.session_state.current_ai_session not in st.session_state.ai_sessions:
             st.session_state.current_ai_session = list(st.session_state.ai_sessions.keys())[0]
             
        current_session_id = st.session_state.current_ai_session
        current_session = st.session_state.ai_sessions[current_session_id]
        
        # 当前对话标题
        st.markdown(f"#### 💬 {current_session['title']}")
        
        # 聊天记录容器 - 增加高度
        chat_container = st.container(height=500, border=True)
        
        # 输入框逻辑前置，以便在同一帧渲染新消息
        prompt = st.chat_input("请输入您的问题...", key="ai_chat_input")
        
        if prompt:
            # 用户消息
            current_session["messages"].append({"role": "user", "content": prompt})
            
            # 更新标题（如果是第一条用户消息）
            if len(current_session["messages"]) == 2: # 0 is init assistant, 1 is user
                current_session["title"] = prompt[:10] + "..." if len(prompt) > 10 else prompt
            
            # AI 回复
            if QwenModel:
                try:
                    # 优先使用输入框的API Key，否则尝试环境变量
                    current_api_key = api_key if api_key else os.getenv("DASHSCOPE_API_KEY")
                    
                    model = QwenModel(api_key=current_api_key, model_name=model_name)
                    
                    # 准备历史记录 (排除刚刚添加的当前问题)
                    history = current_session["messages"][:-1]
                    
                    with st.spinner("AI正在思考..."):
                        response = model.predict(prompt, history=history)
                    
                    if response.get("status") == "success":
                        ai_reply = response.get("text", "")
                    else:
                        ai_reply = f"调用失败: {response.get('text')}"
                        if "API Key" in str(response.get("text")) or "InvalidApiKey" in str(response.get("text")):
                            ai_reply += "\n\n请在左侧【模型配置】中输入有效的 DashScope API Key。"
                            
                except Exception as e:
                    ai_reply = f"发生错误: {str(e)}"
            else:
                ai_reply = "模型组件加载失败，请检查环境配置。"
            
            current_session["messages"].append({"role": "assistant", "content": ai_reply})
            st.rerun()
            
        # 渲染消息 (包含刚刚添加的新消息)
        with chat_container:
            for msg in current_session["messages"]:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
