import streamlit as st
import sys
import os

# 尝试导入 AI 助手
try:
    # 适配不同的导入路径
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.ai_assistant import ai_assistant_dialog
except ImportError:
    def ai_assistant_dialog(): st.error("AI助手组件加载失败")

def render_header(title, subtitle=None):
    """
    渲染统一的页面头部，包含标题、副标题和AI助手按钮
    """
    col_header, col_btn = st.columns([6, 1])
    
    with col_header:
        st.title(title)
        if subtitle:
            st.markdown(f"<p style='color: #6c757d; margin-top: -15px; font-size: 1.1rem;'>{subtitle}</p>", unsafe_allow_html=True)
            
    with col_btn:
        st.write("") # Spacer for alignment
        st.write("") 
        
        # 使用 session_state 控制对话框显示状态
        if "ai_assistant_open" not in st.session_state:
            st.session_state.ai_assistant_open = False
            
        if st.button("🤖 AI助手", help="点击开启AI智能分析助手", key="header_ai_btn"):
            st.session_state.ai_assistant_open = True
            
        if st.session_state.ai_assistant_open:
            ai_assistant_dialog()
            
    st.markdown("---")
