import streamlit as st
import pandas as pd
import numpy as np
import jieba
import re
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
import datetime

# 添加 utils 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(os.path.dirname(current_dir), 'utils')
if utils_dir not in sys.path:
    sys.path.append(utils_dir)

try:
    from utils.data_processor import process_uploaded_data, generate_response
    from utils.layout import render_header
except ImportError:
    st.error("无法导入数据处理模块，请检查路径。")
    def process_uploaded_data(df): return df
    def generate_response(label, text, category): return "无法生成"
    def render_header(title, subtitle=None): st.title(title)

def render_interactive_layout(section_id, component_map, initial_order):
    """
    通用交互式布局组件：三角分布布局 (top-center, bottom-left, bottom-right)
    :param section_id: 唯一ID
    :param component_map: 字典 { 'key': callback }
    :param initial_order: 初始顺序列表 ['key_top', 'key_bottom_left', 'key_bottom_right']
    """
    state_key = f"layout_order_{section_id}"
    
    if state_key not in st.session_state:
        st.session_state[state_key] = initial_order
    
    current_order = st.session_state[state_key]
    if not all(k in component_map for k in current_order):
        st.session_state[state_key] = initial_order
        current_order = initial_order

    # 布局逻辑
    # 采用两行布局：
    # Row 1: 顶部居中 (Top) - 占位比例 [1, 2, 1] 让中间更宽
    # Row 2: 底部左右 (Bottom-Left, Bottom-Right) - 比例 [1, 1]
    
    # Row 1
    col_t_left, col_t_center, col_t_right = st.columns([1, 2, 1])
    
    # Row 2
    col_b_left, col_b_right = st.columns(2)
    
    # 当前状态 current_order: [Item_Top(0), Item_Bottom_Left(1), Item_Bottom_Right(2)]
    
    # --- 顶部组件 (Row 1, Center) ---
    with col_t_center:
        st.markdown(f'<div id="{section_id}_Top" style="text-align: center; margin-bottom: 20px;">', unsafe_allow_html=True)
        component_map[current_order[0]]()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 底部左侧组件 (Row 2, Left) ---
    with col_b_left:
        st.markdown(f'<div id="{section_id}_Left" class="css-card">', unsafe_allow_html=True)
        # 按钮：点击左侧 -> 轮换逻辑 (逆时针/反向)
        # 使得 Left -> Top
        # Logical Cycle: Top -> Right, Right -> Left, Left -> Top
        # New Top (0) = Old Left (1)
        # New Right (2) = Old Top (0)
        # New Left (1) = Old Right (2)
        # Order: [New_0, New_1, New_2] = [Old_1, Old_2, Old_0]
        if st.button("↖️ 移至顶部", key=f"btn_cycle_{section_id}_left", use_container_width=True):
             new_order = [current_order[1], current_order[2], current_order[0]]
             st.session_state[state_key] = new_order
             st.rerun()
             
        component_map[current_order[1]]()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 底部右侧组件 (Row 2, Right) ---
    with col_b_right:
        st.markdown(f'<div id="{section_id}_Right" class="css-card">', unsafe_allow_html=True)
        # 按钮：点击右侧 -> 轮换逻辑 (顺时针/正向) ---> 符合用户描述
        # 用户描述: "Top -> Left, Left -> Right, Right -> Top"
        # New Top (0) = Old Right (2)
        # New Left (1) = Old Top (0)
        # New Right (2) = Old Left (1)
        # Order: [New_0, New_1, New_2] = [Old_2, Old_0, Old_1]
        if st.button("↗️ 移至顶部", key=f"btn_cycle_{section_id}_right", use_container_width=True):
             new_order = [current_order[2], current_order[0], current_order[1]]
             st.session_state[state_key] = new_order
             st.rerun()
             
        component_map[current_order[2]]()
        st.markdown('</div>', unsafe_allow_html=True)


def render_sidebar():
    """
    渲染侧边栏控制组件 (数据管理、筛选等)
    返回: filtered_df (筛选后的数据), 或 None
    """
    # -------------------------------------------------------------------------
    # 侧边栏：文本分析 (控制项)
    # -------------------------------------------------------------------------
    
    # 1. 数据管理
    with st.sidebar.expander("数据管理", expanded=False):
        # 定义历史保留文件路径
        frontend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(frontend_dir, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        history_dir = os.path.join(data_dir, 'history')
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)
            
        history_file_path = os.path.join(data_dir, 'user_upload_history.csv')
        
        # 自动加载历史
        if 'custom_comment_data' not in st.session_state and not st.session_state.get('data_cleared', False):
            if os.path.exists(history_file_path):
                try:
                    loaded_df = pd.read_csv(history_file_path)
                    st.session_state['custom_comment_data'] = loaded_df
                except Exception as e:
                    print(f"Failed to load history: {e}")

        if 'uploader_key' not in st.session_state:
            st.session_state['uploader_key'] = 0
            
        def reset_data():
            if 'custom_comment_data' in st.session_state:
                try:
                    df_to_save = st.session_state['custom_comment_data']
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    history_save_path = os.path.join(history_dir, f"analysis_{timestamp}.csv")
                    df_to_save.to_csv(history_save_path, index=False)
                except Exception as e:
                    print(f"Error archiving history: {e}")
                del st.session_state['custom_comment_data']
            
            if 'viewing_history' in st.session_state:
                st.session_state['viewing_history'] = False
            
            if os.path.exists(history_file_path):
                try:
                    os.remove(history_file_path)
                except Exception as e:
                    print(f"Error removing temp history file: {e}")

            st.session_state['uploader_key'] += 1
            st.session_state['data_cleared'] = True
            
        st.markdown("#### 上传新数据")
        uploaded_file = st.file_uploader(
            "选择文件 (CSV/XLSX)", 
            type=['csv', 'xlsx'], 
            key=f"uploader_{st.session_state['uploader_key']}",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            if st.button("处理并分析", use_container_width=True):
                with st.spinner("正在处理数据..."):
                    try:
                        if uploaded_file.name.endswith('.csv'):
                            raw_df = pd.read_csv(uploaded_file)
                        else:
                            raw_df = pd.read_excel(uploaded_file)
                        
                        processed_df = process_uploaded_data(raw_df)
                        st.session_state['custom_comment_data'] = processed_df
                        st.session_state['viewing_history'] = False
                        
                        try:
                            processed_df.to_csv(history_file_path, index=False)
                        except Exception as e:
                            st.warning(f"无法保存历史记录: {e}")

                        st.session_state['data_cleared'] = False
                        st.success("数据处理完成！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"处理失败: {e}")
        
        if st.button("🗑️ 重置所有数据", on_click=reset_data, use_container_width=True):
            pass
            
    # 2. 历史记录
    if os.path.exists(history_dir):
        history_files = [f for f in os.listdir(history_dir) if f.endswith('.csv')]
        if history_files:
            with st.sidebar.expander("历史记录", expanded=False):
                if st.button("清空历史", key="clear_all_history", use_container_width=True):
                    for f in history_files:
                        try:
                            os.remove(os.path.join(history_dir, f))
                        except Exception as e:
                            print(f"Failed to delete {f}: {e}")
                    if st.session_state.get('viewing_history', False):
                        if 'custom_comment_data' in st.session_state:
                            del st.session_state['custom_comment_data']
                        st.session_state['viewing_history'] = False
                        st.session_state['data_cleared'] = True
                    st.success("历史记录已清空")
                    st.rerun()

                history_files.sort(reverse=True)
                for f in history_files:
                    try:
                        ts_part = f.replace("analysis_", "").replace(".csv", "")
                        dt = datetime.datetime.strptime(ts_part, "%Y%m%d_%H%M%S")
                        display_time = dt.strftime("%Y-%m-%d %H:%M")
                        
                        if st.button(f"{display_time}", key=f"hist_{f}", use_container_width=True):
                            with st.spinner(f"加载 {display_time}..."):
                                try:
                                    loaded_df = pd.read_csv(os.path.join(history_dir, f))
                                    st.session_state['custom_comment_data'] = loaded_df
                                    loaded_df.to_csv(history_file_path, index=False)
                                    st.session_state['data_cleared'] = False
                                    st.session_state['viewing_history'] = True
                                    st.rerun()
                                except Exception as load_err:
                                    st.error(f"加载失败: {load_err}")
                    except:
                        continue

    # 3. 数据准备 (Dataframe Construction)
    df = None
    if 'custom_comment_data' in st.session_state:
        processed_df = st.session_state['custom_comment_data']
        sentiment_map = {"正面": "positive", "负面": "negative", "中性": "neutral"}
        
        # 构造 UI 用的 DF
        data = {
            'id': range(1, len(processed_df) + 1),
            'comment': processed_df['review_content'],
            'sentiment': processed_df['sentiment_label'].map(sentiment_map).fillna('neutral'),
            'rating': processed_df['rating'],
            'category': processed_df['product_category'],
            'solution': processed_df.get('solution', [None]*len(processed_df))
        }
        
        # Date 处理
        if 'date' in processed_df.columns:
             data['date'] = pd.to_datetime(processed_df['date'])
        else:
             # Mock dates
             mock_dates = pd.date_range(start='2023-01-01', periods=len(processed_df), freq='H')
             if len(mock_dates) < len(processed_df):
                 mock_dates = np.random.choice(mock_dates, len(processed_df))
             mock_dates_list = list(mock_dates)
             np.random.shuffle(mock_dates_list)
             data['date'] = mock_dates_list
             
        df = pd.DataFrame(data)
    
    # 4. 筛选器
    filtered_df = None
    if df is not None:
        with st.sidebar.expander("数据筛选", expanded=True):
            st.caption("情感类型")
            sentiment_filter = st.multiselect(
                "Select Sentiment",
                options=df['sentiment'].unique(),
                default=df['sentiment'].unique(),
                label_visibility="collapsed"
            )
            
            st.caption("评分范围")
            rating_filter = st.slider(
                "Select Rating",
                min_value=int(df['rating'].min()),
                max_value=int(df['rating'].max()),
                value=(int(df['rating'].min()), int(df['rating'].max())),
                label_visibility="collapsed"
            )
            
            st.caption("产品分类")
            category_filter = st.multiselect(
                "Select Category",
                options=df['category'].unique(),
                default=df['category'].unique(),
                label_visibility="collapsed"
            )
            
            # Apply
            filtered_df = df[
                (df['sentiment'].isin(sentiment_filter)) &
                (df['rating'].between(rating_filter[0], rating_filter[1])) &
                (df['category'].isin(category_filter))
            ].copy()
            
    # Save to session (vital for show_comment_analysis)
    st.session_state['ca_filtered_df'] = filtered_df
    return filtered_df


def show_comment_analysis():
    """
    显示评论分析页面 (内容区域)
    """
    render_header("评论分析", "深度挖掘用户评论中的情感与观点")
    
    # 检查是否处于"查看历史"模式
    is_viewing_history = st.session_state.get('viewing_history', False)
    
    if is_viewing_history:
        if st.button("🔙 退出历史查看", type="primary"):
            if 'custom_comment_data' in st.session_state:
                del st.session_state['custom_comment_data']
            st.session_state['viewing_history'] = False
            st.session_state['data_cleared'] = True
            st.rerun()

    # 从 Session State 获取筛选后的数据
    filtered_df = st.session_state.get('ca_filtered_df', None)
    
    if filtered_df is None:
        st.info("👋 欢迎使用评论分析！\n\n请在左侧侧边栏上传您的 CSV/XLSX 评论数据文件以开始分析。")
        return
    
    # 显示数据概览
    st.markdown("### 数据概览")
    
    # 使用 Plotly Indicator 创建仪表盘样式
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        fig = go.Figure(go.Indicator(
            mode = "number",
            value = len(filtered_df),
            title = {"text": "总评论数"},
            domain = {'x': [0, 1], 'y': [0, 1]}
        ))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        avg_rating = filtered_df['rating'].mean()
        fig = go.Figure(go.Indicator(
            mode = "number",
            value = avg_rating,
            title = {"text": "平均评分"},
            number = {'valueformat': ".2f"},
            domain = {'x': [0, 1], 'y': [0, 1]}
        ))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        positive_pct = (filtered_df['sentiment'] == 'positive').sum() / len(filtered_df) * 100
        fig = go.Figure(go.Indicator(
            mode = "number",
            value = positive_pct,
            title = {"text": "正面评论比例(%)"},
            number = {'valueformat': ".1f"},
            domain = {'x': [0, 1], 'y': [0, 1]}
        ))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)
        
    with col4:
        negative_pct = (filtered_df['sentiment'] == 'negative').sum() / len(filtered_df) * 100
        fig = go.Figure(go.Indicator(
            mode = "number",
            value = negative_pct,
            title = {"text": "负面评论比例(%)"},
            number = {'valueformat': ".1f"},
            domain = {'x': [0, 1], 'y': [0, 1]}
        ))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 显示原始数据表格
    with st.expander("查看原始数据"):
        st.dataframe(filtered_df)
    
    # 新增：定义各个图表的渲染函数
    def render_sentiment_pie():
        sentiment_counts = filtered_df['sentiment'].value_counts()
        fig_pie = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            title="情感分布",
            color_discrete_map={'positive': 'green', 'negative': 'red', 'neutral': 'blue'}
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    def render_rating_bar():
        rating_counts = filtered_df['rating'].value_counts().sort_index()
        fig_bar = px.bar(
            x=rating_counts.index,
            y=rating_counts.values,
            title="评分分布",
            labels={'x': '评分', 'y': '数量'},
            color_discrete_sequence=px.colors.sequential.Viridis
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    def render_sentiment_summary_table():
        st.markdown("#### 情感统计摘要")
        sentiment_summary = filtered_df.groupby('sentiment').agg({
            'rating': 'mean',
            'id': 'count'
        }).rename(columns={'rating': '平均评分', 'id': '评论数'})
        st.dataframe(sentiment_summary, use_container_width=True)

    # ---------------- 情感分析交互式布局 ----------------
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### 情感分析 (交互布局)")
    
    render_interactive_layout(
        section_id="sentiment_analysis",
        component_map={
            'pie_chart': render_sentiment_pie,
            'bar_chart': render_rating_bar,
            'summary_table': render_sentiment_summary_table
        },
        initial_order=['pie_chart', 'bar_chart', 'summary_table']
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 类别分析定义
    def render_category_count_bar():
        category_counts = filtered_df['category'].value_counts()
        fig_cat_count = px.bar(
            x=category_counts.index, 
            y=category_counts.values,
            title="各产品分类评论数量",
            labels={'x': '产品分类', 'y': '评论数量'}
        )
        st.plotly_chart(fig_cat_count, use_container_width=True)

    def render_category_sentiment_bar():
        category_sentiment = filtered_df.groupby(['category', 'sentiment']).size().unstack().fillna(0)
        cat_sentiment_long = category_sentiment.reset_index().melt(
            id_vars='category', 
            var_name='sentiment', 
            value_name='count'
        )
        color_map = {'positive': '#00CC96', 'negative': '#EF553B', 'neutral': '#636EFA'}
        fig_cat_sentiment = px.bar(
            cat_sentiment_long,
            x='category',
            y='count',
            color='sentiment',
            title="各产品分类情感分布",
            color_discrete_map=color_map,
            barmode='group',
            labels={'category': '产品分类', 'count': '数量', 'sentiment': '情感'}
        )
        st.plotly_chart(fig_cat_sentiment, use_container_width=True)

    def render_category_table():
        st.markdown("#### 分类统计详情")
        cat_summary = filtered_df.groupby('category').agg({
            'rating': 'mean',
            'id': 'count'
        }).rename(columns={'rating': '平均评分', 'id': '评论总数'})
        st.dataframe(cat_summary, use_container_width=True)

    # ---------------- 产品分类分析交互式布局 ----------------
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### 产品分类分析")
    
    render_interactive_layout(
        section_id="category_analysis",
        component_map={
            'cat_count_bar': render_category_count_bar,
            'cat_sentiment_bar': render_category_sentiment_bar,
            'cat_table': render_category_table
        },
        initial_order=['cat_count_bar', 'cat_sentiment_bar', 'cat_table']
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 时间趋势分析定义
    # 按月份聚合数据 (预处理)
    filtered_df['month'] = filtered_df['date'].dt.to_period('M')
    monthly_data = filtered_df.groupby('month').agg({
        'rating': 'mean',
        'sentiment': lambda x: (x == 'positive').sum() / len(x) * 100,
        'id': 'count'
    }).reset_index().rename(columns={'id': 'count'})
    monthly_data['month'] = monthly_data['month'].dt.to_timestamp()

    def render_rating_trend_line():
        fig_rating_trend = px.line(
            monthly_data,
            x='month',
            y='rating',
            title="月度平均评分",
            markers=True,
            labels={'month': '月份', 'rating': '平均评分'}
        )
        fig_rating_trend.update_traces(line_color='#636EFA')
        st.plotly_chart(fig_rating_trend, use_container_width=True)
        
    def render_sentiment_trend_line():
        fig_sentiment_trend = px.line(
            monthly_data,
            x='month',
            y='sentiment',
            title="月度正面评论比例(%)",
            markers=True,
            labels={'month': '月份', 'sentiment': '正面比例(%)'}
        )
        fig_sentiment_trend.update_traces(line_color='#00CC96')
        st.plotly_chart(fig_sentiment_trend, use_container_width=True)

    def render_monthly_table():
        st.markdown("#### 月度数据统计")
        display_monthly = monthly_data.copy()
        display_monthly['month'] = display_monthly['month'].dt.strftime('%Y-%m')
        display_monthly = display_monthly.rename(columns={
            'month': '月份', 
            'rating': '平均评分', 
            'sentiment': '正面占比(%)',
            'count': '评论数'
        })
        st.dataframe(display_monthly, use_container_width=True)

    # ---------------- 时间趋势分析交互式布局 ----------------
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### 时间趋势分析")
    
    render_interactive_layout(
        section_id="trend_analysis",
        component_map={
            'rating_line': render_rating_trend_line,
            'sentiment_line': render_sentiment_trend_line,
            'monthly_table': render_monthly_table
        },
        initial_order=['rating_line', 'sentiment_line', 'monthly_table']
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 关键词分析定义
    
    # 文本处理逻辑 (保留原函数逻辑)
    def process_text(text):
        if not isinstance(text, str):
            return []
        stop_words = {
            '我', '你', '他', '仅', 'i', 'you', 'also', 'be', 'after',
            '的', '了', '在', '是', '有', '和', '就', '不', '人', '都', 
            '一', '一个', '上', '也', '很', '到', '说', '要', '去', '会', 
            '着', '没有', '看', '好', '自己', '这', '非常', '感觉', '觉得', 
            '比较', '这个', '那个', '我们', '你们', '他们', '它', '只是', '但是',
            'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
            'to', 'of', 'in', 'on', 'at', 'for', 'with', 'it', 'this', 'that', 
            'my', 'your', 'his', 'her', 'its', 'we', 'they', 'have', 'has', 'had', 
            'do', 'does', 'did', 'can', 'could', 'will', 'would', 'should', 'not', 
            'no', 'yes', 'so', 'as', 'if', 'when', 'where', 'why', 'how', 'all', 
            'any', 'some', 'very', 'good', 'bad', 'great', 'product', 'use', 'one', 
            'just', 'get', 'from', 'out', 'up', 'down', 'about', 'than', 'then', 
            'now', 'only', 'well', 'much', 'more', 'other', 'which', 'what', 
            'who', 'whom', 'whose', 'cable', 'charging', 'phone',
            'been', 'being', 'am', 'before', 'by', 'into', 'during', 'until', 
            'against', 'among', 'through', 'over', 'between', 'since', 'without', 
            'under', 'within', 'along', 'across', 'behind', 'beyond', 'around', 
            'above', 'near', 'off', 'go', 'going', 'gone', 'went', 'make', 'made', 
            'making', 'know', 'take', 'see', 'come', 'think', 'look', 'want', 
            'give', 'used', 'using', 'find', 'tell', 'ask', 'work', 'worked', 
            'working', 'seem', 'feel', 'try', 'leave', 'call', 'he', 'him', 'she', 
            'us', 'our', 'them', 'their', 'these', 'those', 'even', 'still', 'way', 
            'too', 'really', 'usb', 'type', 'fast', 'data', 'sync', 'compatible'
        }
        words = jieba.cut(text)
        result = []
        for word in words:
            word = word.strip().lower()
            if len(word) > 1 and word not in stop_words and not word.isdigit() and not re.match(r'^[^\w\s]+$', word):
                result.append(word)
        return result
    
    # 预先计算词频
    all_words = []
    for comment in filtered_df['comment']:
        all_words.extend(process_text(comment))
    word_counts = Counter(all_words)
    top_words = word_counts.most_common(20)
    top_words_df = pd.DataFrame(top_words, columns=['词汇', '频次'])
    
    # 预先计算情感关键词
    positive_comments = filtered_df[filtered_df['sentiment'] == 'positive']['comment']
    positive_words = []
    for comment in positive_comments:
        unique_words = set(process_text(comment))
        positive_words.extend(unique_words)
    positive_word_counts = Counter(positive_words).most_common(10)
    positive_words_df = pd.DataFrame(positive_word_counts, columns=['词汇', '频次'])

    negative_comments = filtered_df[filtered_df['sentiment'] == 'negative']['comment']
    negative_words = []
    for comment in negative_comments:
        unique_words = set(process_text(comment))
        negative_words.extend(unique_words)
    negative_word_counts = Counter(negative_words).most_common(10)
    negative_words_df = pd.DataFrame(negative_word_counts, columns=['词汇', '频次'])

    def render_word_freq_bar():
        if not top_words_df.empty:
            fig_words = px.bar(
                top_words_df,
                x='词汇',
                y='频次',
                title="高频词汇分布"
            )
            fig_words.update_xaxes(tickangle=45)
            st.plotly_chart(fig_words, use_container_width=True)
        else:
            st.info("没有足够的数据生成词频图")

    def render_top_words_table():
        st.markdown("#### 高频词汇表")
        st.dataframe(top_words_df, use_container_width=True)

    def render_sentiment_words_table():
        st.markdown("#### 情感关键词 (正/负)")
        col_pos, col_neg = st.columns(2)
        with col_pos:
            st.caption("正面")
            st.dataframe(positive_words_df, use_container_width=True, height=200)
        with col_neg:
            st.caption("负面")
            st.dataframe(negative_words_df, use_container_width=True, height=200)

    # ---------------- 关键词分析交互式布局 ----------------
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### 关键词分析")

    render_interactive_layout(
        section_id="keyword_analysis",
        component_map={
            'word_bar': render_word_freq_bar,
            'word_table': render_top_words_table,
            'sentiment_table': render_sentiment_words_table
        },
        initial_order=['word_bar', 'word_table', 'sentiment_table']
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # 负面评价应对方案 (保持不变)

    
    # 负面评价应对方案
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### 负面评价应对方案")
    
    # 筛选负面评价
    negative_reviews_df = filtered_df[filtered_df['sentiment'] == 'negative'].copy()
    
    if not negative_reviews_df.empty:
        st.info(f"共发现 {len(negative_reviews_df)} 条负面评价。")
        
        # 选取所有数据
        solutions_df = negative_reviews_df.copy()
        
        # 创建一个占位符用于动态更新表格
        table_placeholder = st.empty()
        # 初始化结果列表
        results = []
        # 标记是否有新生成的数据需要保存
        has_new_generation = False
        
        # 实时调用 AI 生成建议 (边生成边展示)
        with st.spinner("🤖 AI 正在深入分析评论并生成专业应对策略..."):
            for index, row in solutions_df.iterrows():
                # 检查是否已存在有效的解决方案
                existing_solution = row.get('solution')
                suggestion = ""
                
                if pd.notna(existing_solution) and isinstance(existing_solution, str) and len(existing_solution.strip()) > 1:
                    # 使用已有结果
                    suggestion = existing_solution
                else:
                    # 生成新建议
                    suggestion = generate_response('负面', row['comment'], row['category'])
                    has_new_generation = True
                
                # 添加到结果列表
                results.append({
                    'category': row['category'],
                    'comment': row['comment'],
                    'solution': suggestion,
                    'original_index': index # 保存原始索引以便回写
                })
                
                # 实时转换为 DataFrame 并更新显示 (仅当有新生成时才频繁更新，或者是刚开始/结束时)
                if has_new_generation:
                    current_df = pd.DataFrame(results)
                    # 在占位符中渲染当前进度
                    with table_placeholder.container():
                         with st.expander("查看负面评价及AI建议 (分析中...)", expanded=True):
                            st.dataframe(
                                current_df[['category', 'comment', 'solution']].rename(columns={
                                    'category': '产品分类',
                                    'comment': '用户评论',
                                    'solution': 'AI智能建议'
                                }), # 先筛选列再重命名，避免KeyError
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "产品分类": st.column_config.TextColumn("产品分类", width="small"),
                                    "用户评论": st.column_config.TextColumn("用户评论", width="medium"),
                                    "AI智能建议": st.column_config.TextColumn("AI智能建议", width="large"),
                                }
                            )
        
        # 最终状态更新 (移除生成中标记)
        final_df = pd.DataFrame(results)
        table_placeholder.empty() # 清空占位符，重新渲染最终结果
        
        with st.expander("查看负面评价及AI建议", expanded=True):
             st.dataframe(
                final_df[['category', 'comment', 'solution']].rename(columns={
                    'category': '产品分类',
                    'comment': '用户评论',
                    'solution': 'AI智能建议'
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "产品分类": st.column_config.TextColumn("产品分类", width="small"),
                    "用户评论": st.column_config.TextColumn("用户评论", width="medium"),
                    "AI智能建议": st.column_config.TextColumn("AI智能建议", width="large"),
                }
            )
            
        # 如果生成了新数据，自动保存回历史记录
        if has_new_generation and 'custom_comment_data' in st.session_state:
            try:
                processed_df = st.session_state['custom_comment_data']
                
                # 确保有 solution 列
                if 'solution' not in processed_df.columns:
                    processed_df['solution'] = None
                
                # 回写新生成的 solution
                processed_df['solution'] = processed_df['solution'].astype(object)
                for res in results:
                    # 只有当我们确实生成了（或者为了保险起见全部覆盖）
                    # 这里的 original_index 对应 df 的索引，也对应 processed_df 的索引
                    idx = res['original_index']
                    processed_df.at[idx, 'solution'] = res['solution']
                
                # 更新 session state
                st.session_state['custom_comment_data'] = processed_df
                
                # 保存到文件
                frontend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                data_dir = os.path.join(frontend_dir, 'data')
                history_file_path = os.path.join(data_dir, 'user_upload_history.csv')
                
                if os.path.exists(os.path.dirname(history_file_path)):
                    processed_df.to_csv(history_file_path, index=False)
                    # st.toast("分析结果已自动保存")
            except Exception as e:
                print(f"Error saving analysis results: {e}")
                
    else:
        st.success("当前筛选条件下没有负面评价！")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.success("评论分析完成！")