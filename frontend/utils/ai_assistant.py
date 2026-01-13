import streamlit as st
import uuid
import sys
import os
import pandas as pd

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
        
        # 1. 先渲染历史消息
        with chat_container:
            for msg in current_session["messages"]:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
        
        # 输入框
        prompt = st.chat_input("请输入您的问题...", key="ai_chat_input")
        
        if prompt:
            # 2. 立即渲染用户消息
            with chat_container:
                with st.chat_message("user"):
                    st.write(prompt)

            # 更新会话状态
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
                    
                    # --- 构建上下文 (数据感知) ---
                    context_messages = []
                    
                    # 1. 文本分析数据
                    # 优先使用筛选后的数据(用户当前看到的)，如果没有则使用原始导入数据
                    target_df = None
                    df_source_name = "未命名"
                    
                    if 'ca_filtered_df' in st.session_state and st.session_state['ca_filtered_df'] is not None:
                        target_df = st.session_state['ca_filtered_df']
                        df_source_name = "当前筛选后数据"
                    elif 'custom_comment_data' in st.session_state and st.session_state['custom_comment_data'] is not None:
                        target_df = st.session_state['custom_comment_data']
                        df_source_name = "原始导入数据"
                        
                    if target_df is not None:
                        try:
                            # 限制上下文大小，避免Token溢出
                            columns = ", ".join(map(str, target_df.columns.tolist()))
                            row_count = len(target_df)
                            
                            # 获取数据摘要
                            # 1. 简要统计
                            stats_info = ""
                            if 'sentiment' in target_df.columns:
                                sentiment_counts = target_df['sentiment'].value_counts().to_dict()
                                stats_info += f"情感分布: {sentiment_counts}; "
                            if 'rating' in target_df.columns:
                                avg_rating = target_df['rating'].mean()
                                stats_info += f"平均评分: {avg_rating:.2f}; "
                            
                            # 2. 采样几条评论 (如果包含 comment 列)
                            sample_text = ""
                            if 'comment' in target_df.columns:
                                sample_rows = target_df.head(3)
                                sample_text = sample_rows[['comment', 'sentiment', 'rating']].to_string(index=False) if {'sentiment', 'rating'}.issubset(target_df.columns) else sample_rows['comment'].to_string(index=False)
                            else:
                                sample_text = target_df.head(3).to_string(index=False)

                            context_messages.append(f"[{df_source_name}快照]\n总行数: {row_count}\n列名: {columns}\n统计概览: {stats_info}\n数据采样(前3行):\n{sample_text}")
                        except Exception as e:
                            print(f"Context error (text): {e}")

                    # 2. 图像分析结果
                    if 'image_analysis_context' in st.session_state:
                        try:
                            img_ctx = st.session_state['image_analysis_context']
                            img_data = img_ctx.get('data', {})
                            filename = img_ctx.get('filename', 'unknown')
                            
                            if img_ctx.get('type') == 'analysis':
                                objs = [o.get('name') for o in img_data.get('objects', [])]
                                scene = img_data.get('scene', '未识别场景')
                                cls_dict = img_data.get('classification', {})
                                top_cls = max(cls_dict, key=cls_dict.get) if cls_dict else '无分类'
                                context_messages.append(f"[当前图像分析结果]\n文件名: {filename}\n场景描述: {scene}\n识别对象: {', '.join(objs)}\n分类: {top_cls}")
                            elif img_ctx.get('type') == 'ocr':
                                text = img_data.get('ocr_text', '无文字')
                                context_messages.append(f"[当前图像OCR结果]\n文件名: {filename}\n提取文本(前500字):\n{text[:500]}") 
                        except Exception as e:
                             print(f"Context error (image): {e}")

                    full_prompt = prompt
                    if context_messages:
                        context_str = "\n\n".join(context_messages)
                        full_prompt = f"【系统提示：请结合以下当前上下文信息来回答用户问题】\n{context_str}\n\n用户问题：{prompt}"

                    # 3. 渲染 AI 消息 (流式或等待)
                    with chat_container:
                        with st.chat_message("assistant"):
                            with st.spinner("AI正在思考..."):
                                response = model.predict(full_prompt, history=history)
                            
                            if response.get("status") == "success":
                                ai_reply = response.get("text", "")
                                st.write(ai_reply)
                            else:
                                ai_reply = f"调用失败: {response.get('text')}"
                                if "API Key" in str(response.get("text")) or "InvalidApiKey" in str(response.get("text")):
                                    ai_reply += "\n\n请在左侧【模型配置】中输入有效的 DashScope API Key。"
                                st.error(ai_reply)
                            
                except Exception as e:
                    ai_reply = f"发生错误: {str(e)}"
                    with chat_container:
                        with st.chat_message("assistant"):
                            st.error(ai_reply)
            else:
                ai_reply = "模型组件加载失败，请检查环境配置。"
                with chat_container:
                    with st.chat_message("assistant"):
                        st.error(ai_reply)
            
            current_session["messages"].append({"role": "assistant", "content": ai_reply})
            # st.rerun() # Removed to prevent loop

