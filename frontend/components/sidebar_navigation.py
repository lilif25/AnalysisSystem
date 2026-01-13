import streamlit as st

def create_custom_sidebar(backend_url=None):
    """
    创建一个美观的自定义侧边导航栏
    """
    # 初始化导航状态
    if 'current_page' not in st.session_state:
        st.session_state.current_page = '首页'
    
    # 侧边栏标题
    st.sidebar.markdown(
        """
        <h1 style='text-align: center; width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding-bottom: 20px;'>多模态分析</h1>
        """, 
        unsafe_allow_html=True
    )
    
    # 注入自定义CSS样式
    st.markdown("""
        <style>
        /* 侧边栏按钮样式优化 */
        [data-testid="stSidebar"] .stButton button {
            border: 1px solid transparent;
            transition: all 0.2s ease;
            width: 100%;
        }

        /* 选中状态(Primary)按钮样式 */
        [data-testid="stSidebar"] .stButton button[kind="primary"] {
            background-color: #4f46e5 !important;
            color: white !important;
            border-color: #4f46e5 !important;
            font-weight: 600;
        }
        [data-testid="stSidebar"] .stButton button[kind="primary"]:hover {
            background-color: #4338ca !important;
            border-color: #4338ca !important;
        }

        /* 未选中状态(Secondary)按钮样式 */
        [data-testid="stSidebar"] .stButton button[kind="secondary"] {
            background-color: transparent;
            color: #333;
            border: 1px solid transparent;
        }
        [data-testid="stSidebar"] .stButton button[kind="secondary"]:hover {
            background-color: rgba(79, 70, 229, 0.1);
            color: #4f46e5;
        }
        
        /* 调整垂直间距 */
        [data-testid="stSidebar"] .stButton {
            margin-bottom: -10px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 定义导航菜单项
    menu_items = {
        "首页": "首页",
        "文本分析": "文本分析",
        "图像分析": "图像分析",
    }
    
    # 反向映射用于查找ID
    title_to_id = {v: k for k, v in menu_items.items()}
    
    # 获取当前选中的索引
    options = list(menu_items.values())
            
    # 使用 Button 组件作为导航
    for label in options:
        page_id = title_to_id[label]
        # 判断当前按钮是否对应当前页面
        is_active = (page_id == st.session_state.current_page)
        
        # 选中项使用 primary (实心)，未选中项使用 secondary (默认/透明)
        btn_type = "primary" if is_active else "secondary"
        
        # 如果是"文本分析"且当前已激活，我们不显示普通按钮，而是显示一个类似折叠菜单的结构
        if label == "文本分析":
            if st.sidebar.button(label, key=f"nav_{page_id}", type=btn_type, use_container_width=True):
                # 点击逻辑保持不变 (若未激活则激活并刷新)
                if not is_active:
                     if page_id == "文本分析" and (st.session_state.get('data_cleared', False) or st.session_state.get('viewing_history', False)):
                        if 'custom_comment_data' in st.session_state:
                            del st.session_state['custom_comment_data']
                        if 'viewing_history' in st.session_state:
                            st.session_state['viewing_history'] = False
                        st.session_state['data_cleared'] = True
                     st.session_state.current_page = page_id
                     if "ai_assistant_open" in st.session_state:
                        st.session_state.ai_assistant_open = False
                     st.rerun()

            # 如果当前是文本分析页面，在按钮下方直接渲染子菜单(Controls)
            if is_active:
                try:
                    # 从 comment_analysis 导入 render_sidebar
                    # 注意：为了避免顶层循环导入，在函数内部导入
                    from components.comment_analysis import render_sidebar
                    with st.sidebar.container():
                        st.markdown("<div style='margin-left: 10px; border-left: 2px solid #e5e7eb; padding-left: 10px;'>", unsafe_allow_html=True)
                        render_sidebar()
                        st.markdown("</div>", unsafe_allow_html=True)
                except ImportError:
                    st.sidebar.error("无法加载侧边栏组件")
        else:
            # 其他常规按钮
            if st.sidebar.button(label, key=f"nav_{page_id}", type=btn_type, use_container_width=True):
                if not is_active:
                    st.session_state.current_page = page_id
                    if "ai_assistant_open" in st.session_state:
                         st.session_state.ai_assistant_open = False
                    st.rerun()
    
    # 添加分隔线
    
    # 添加分隔线
    st.sidebar.markdown("---")
    
    # 返回当前选中的页面
    return st.session_state.current_page
