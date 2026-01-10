import streamlit as st

def load_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* 全局变量 */
        :root {
            --primary-color: #4f46e5;
            --primary-hover: #4338ca;
            --background-color: #f8fafc;
            --card-background: #ffffff;
            --text-color: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --radius-md: 0.5rem;
            --radius-lg: 0.75rem;
        }

        /* 全局字体与背景 */
        html {
            font-size: 15px !important;
        }
        
        .stApp {
            font-size: 15px !important;
            background-color: var(--background-color);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: var(--text-color);
        }
        
        /* 侧边栏样式优化 */
        section[data-testid="stSidebar"] {
            background-color: var(--card-background);
            border-right: 1px solid var(--border-color);
            box-shadow: var(--shadow-sm);
        }
        
        /* 标题样式 */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-color);
            font-weight: 700;
            letter-spacing: -0.025em;
        }
        
        /* 卡片式布局容器 */
        .css-card {
            background-color: var(--card-background);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            box-shadow: var(--shadow-md);
            margin-bottom: 1.5rem;
            border: 1px solid var(--border-color);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .css-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        
        /* 按钮样式微调 */
        .stButton button {
            border-radius: var(--radius-md);
            font-weight: 600;
            transition: all 0.2s ease;
            border: 1px solid transparent;
        }
        
        /* Primary Button */
        .stButton button[kind="primary"] {
            background-color: var(--primary-color);
            color: white;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
        
        .stButton button[kind="primary"]:hover {
            background-color: var(--primary-hover);
            box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);
        }

        /* Secondary Button */
        .stButton button[kind="secondary"] {
            background-color: white;
            color: var(--text-color);
            border: 1px solid var(--border-color);
        }
        
        .stButton button[kind="secondary"]:hover {
            border-color: var(--primary-color);
            color: var(--primary-color);
            background-color: #f5f3ff;
        }
        
        /* 调整顶部内边距和宽度 */
        .block-container {
            padding-top: 3.5rem;
            padding-bottom: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 100%;
        }
        
        /* Expander 样式 */
        .streamlit-expanderHeader {
            background-color: white;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
            color: var(--text-color);
        }
        
        div[data-testid="stExpander"] {
            border: none;
            box-shadow: none;
        }
        
        /* Dataframe 样式 */
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            overflow: hidden;
            box-shadow: var(--shadow-sm);
        }
        
        /* Input fields */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            border-radius: var(--radius-md);
            border-color: var(--border-color);
        }
        
        .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
        }
        
        /* Chat Input */
        .stChatInputContainer {
            border-radius: var(--radius-lg);
            border-color: var(--border-color);
        }
        
        /* Chat Message */
        .stChatMessage {
            background-color: transparent;
        }
        
        div[data-testid="stChatMessageContent"] {
            background-color: white;
            border-radius: var(--radius-md);
            padding: 1rem;
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow-sm);
        }
        
        /* User message specific */
        div[data-testid="stChatMessage"]:nth-child(odd) div[data-testid="stChatMessageContent"] {
            background-color: #eef2ff;
            border-color: #c7d2fe;
        }

        </style>
    """, unsafe_allow_html=True)

def card_container(key=None):
    """创建一个卡片风格的容器"""
    container = st.container()
    # 注意：Streamlit 原生不支持直接给 container 加 class，
    # 这里我们通过 markdown 闭合标签的方式或者直接在组件周围包裹 HTML div 来实现是比较 hacky 的。
    # 更稳妥的方式是使用 st.container() 并在内部元素保持整洁，或者使用 streamlit-extras (如果允许)。
    # 鉴于环境限制，我们尽量通过全局 CSS 配合 st.markdown 来模拟，或者仅做视觉上的留白。
    # 这里我们简单返回 container，依靠全局背景色差来区分。
    # 为了更好的效果，我们可以用 markdown 注入一个 div wrapper，但这对后续 python 代码块的缩进要求很高。
    # 简化方案：我们尽量让页面背景是浅灰，内容块背景是白。
    return container
