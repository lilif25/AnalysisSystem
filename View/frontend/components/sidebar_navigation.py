import streamlit as st

def create_custom_sidebar():
    """
    创建一个美观的自定义侧边导航栏
    """
    # 初始化导航状态
    if 'current_page' not in st.session_state:
        st.session_state.current_page = '首页'
    
    # 侧边栏标题
    st.sidebar.title("🔍 多模态分析")
    
    # 定义导航菜单项
    menu_items = {
        "首页": "🏠 首页",
        "文本分析": "📝 文本分析",
        "图像分析": "🖼️ 图像分析",
    }
    
    # 反向映射用于查找ID
    title_to_id = {v: k for k, v in menu_items.items()}
    
    # 获取当前选中的索引
    current_index = 0
    options = list(menu_items.values())
    if st.session_state.current_page in menu_items:
        current_label = menu_items[st.session_state.current_page]
        if current_label in options:
            current_index = options.index(current_label)
            
    # 使用 Radio 组件作为导航
    selected_label = st.sidebar.radio(
        "导航菜单",
        options=options,
        index=current_index,
        label_visibility="collapsed"
    )
    
    # 更新状态
    selected_id = title_to_id[selected_label]
    if selected_id != st.session_state.current_page:
        # 如果从其他页面切换回"文本分析"，且之前处于数据清空状态或正在查看历史，则需要重置掉可能存在的历史预览数据
        if selected_id == "文本分析" and (st.session_state.get('data_cleared', False) or st.session_state.get('viewing_history', False)):
            if 'custom_comment_data' in st.session_state:
                del st.session_state['custom_comment_data']
            if 'viewing_history' in st.session_state:
                st.session_state['viewing_history'] = False
            # 确保data_cleared为True，这样回到页面时是欢迎页
            st.session_state['data_cleared'] = True

        st.session_state.current_page = selected_id
        # 切换页面时关闭 AI 助手
        if "ai_assistant_open" in st.session_state:
            st.session_state.ai_assistant_open = False
        st.rerun()
    
    # 添加分隔线
    st.sidebar.markdown("---")
    
    # 返回当前选中的页面
    return st.session_state.current_page
