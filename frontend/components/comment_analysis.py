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

def show_comment_analysis():
    """
    显示评论分析页面
    """
    render_header("评论分析", "深度挖掘用户评论中的情感与观点")
    
    # 检查是否处于"查看历史"模式
    is_viewing_history = st.session_state.get('viewing_history', False)
    
    if is_viewing_history:
        if st.button("🔙 退出历史查看", type="primary"):
            if 'custom_comment_data' in st.session_state:
                del st.session_state['custom_comment_data']
            st.session_state['viewing_history'] = False
            # 确保清空状态正确
            st.session_state['data_cleared'] = True
            st.rerun()

    
    # -------------------------------------------------------------------------
    # 数据管理功能 (上传 & 重置)
    # -------------------------------------------------------------------------
    st.sidebar.markdown("### 数据管理")
    
    # 定义历史保留文件路径
    # View/frontend/components/comment_analysis.py -> View/frontend/data/user_upload_history.csv
    frontend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(frontend_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    # 定义及创建 Historical Analysis 目录
    history_dir = os.path.join(data_dir, 'history')
    if not os.path.exists(history_dir):
        os.makedirs(history_dir)
        
    history_file_path = os.path.join(data_dir, 'user_upload_history.csv')
    
    # 尝试自动加载历史数据 (如果当前还没有加载数据且用户没有手动清空过)
    if 'custom_comment_data' not in st.session_state and not st.session_state.get('data_cleared', False):
        if os.path.exists(history_file_path):
            try:
                loaded_df = pd.read_csv(history_file_path)
                st.session_state['custom_comment_data'] = loaded_df
                # st.toast("已恢复上次分析的数据")
            except Exception as e:
                # 如果读取失败，忽略错误，等待用户重新上传
                print(f"Failed to load history: {e}")

    # 初始化 uploader_key 用于重置文件上传控件
    if 'uploader_key' not in st.session_state:
        st.session_state['uploader_key'] = 0
        
    def reset_data():
        """重置数据的回调函数"""
        if 'custom_comment_data' in st.session_state:
            # 1. 保存当前数据到 Historical Analysis
            try:
                df_to_save = st.session_state['custom_comment_data']
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                history_save_path = os.path.join(history_dir, f"analysis_{timestamp}.csv")
                df_to_save.to_csv(history_save_path, index=False)
            except Exception as e:
                print(f"Error archiving history: {e}")
            
            # 2. 从 session state 中删除
            del st.session_state['custom_comment_data']
            
        # 清除查看历史的状态
        if 'viewing_history' in st.session_state:
            st.session_state['viewing_history'] = False
        
        # 删除本地临时历史记录文件 (user_upload_history.csv)
        if os.path.exists(history_file_path):
            try:
                os.remove(history_file_path)
            except Exception as e:
                print(f"Error removing temp history file: {e}")

        # 增加 key 值，强制重新渲染 file_uploader，从而清空已上传的文件
        st.session_state['uploader_key'] += 1
        # 标记数据已清空
        st.session_state['data_cleared'] = True
        
    with st.sidebar.expander("上传新数据 (CSV/XLSX)", expanded=False):
        uploaded_file = st.file_uploader(
            "选择文件", 
            type=['csv', 'xlsx'], 
            key=f"uploader_{st.session_state['uploader_key']}"
        )
        
        if uploaded_file:
            if st.button("处理并分析"):
                with st.spinner("正在处理数据..."):
                    try:
                        if uploaded_file.name.endswith('.csv'):
                            raw_df = pd.read_csv(uploaded_file)
                        else:
                            raw_df = pd.read_excel(uploaded_file)
                        
                        processed_df = process_uploaded_data(raw_df)
                        st.session_state['custom_comment_data'] = processed_df
                        # 上传新数据意味着不再是单纯的查看历史模式
                        st.session_state['viewing_history'] = False
                        
                        # 保存到本地历史记录
                        try:
                            processed_df.to_csv(history_file_path, index=False)
                        except Exception as e:
                            st.warning(f"无法保存历史记录: {e}")

                        # 重置清空标记
                        st.session_state['data_cleared'] = False
                        st.success("数据处理完成！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"处理失败: {e}")
    
    with st.sidebar.expander("重置数据", expanded=False):
        st.button("确认重置所有数据", on_click=reset_data)
    
    # -------------------------------------------------------------------------
    # 历史分析记录 (Historical Analysis)
    # -------------------------------------------------------------------------
    if os.path.exists(history_dir):
        # 获取所有历史文件
        history_files = [f for f in os.listdir(history_dir) if f.endswith('.csv')]
        
        if history_files:
            st.sidebar.markdown("---")
            hist_expander = st.sidebar.expander("📜 历史分析记录", expanded=False)
            
            # 清空历史记录按钮
            if hist_expander.button("🗑️ 清空所有历史", key="clear_all_history"):
                for f in history_files:
                    try:
                        os.remove(os.path.join(history_dir, f))
                    except Exception as e:
                        print(f"Failed to delete {f}: {e}")
                
                # 如果当前正在查看历史，也将其清除
                if st.session_state.get('viewing_history', False):
                    if 'custom_comment_data' in st.session_state:
                         del st.session_state['custom_comment_data']
                    st.session_state['viewing_history'] = False
                    st.session_state['data_cleared'] = True
                
                st.success("历史记录已清空")
                st.rerun()

            # 按文件名倒序排列 (最新的在前，因为文件名包含时间戳)
            history_files.sort(reverse=True)
            
            for f in history_files:
                try:
                    # 从文件名解析时间戳 analysis_YYYYMMDD_HHMMSS.csv
                    ts_part = f.replace("analysis_", "").replace(".csv", "")
                    dt = datetime.datetime.strptime(ts_part, "%Y%m%d_%H%M%S")
                    display_time = dt.strftime("%Y-%m-%d %H:%M")
                    
                    if hist_expander.button(f"📊 分析记录 ({display_time})", key=f"hist_{f}"):
                        with st.spinner(f"正在加载 {display_time} 的分析记录..."):
                            try:
                                loaded_df = pd.read_csv(os.path.join(history_dir, f))
                                st.session_state['custom_comment_data'] = loaded_df
                                # 恢复为当前活跃文件，以便页面刷新后保持
                                loaded_df.to_csv(history_file_path, index=False)
                                st.session_state['data_cleared'] = False
                                st.session_state['viewing_history'] = True
                                st.rerun()
                            except Exception as load_err:
                                hist_expander.error(f"加载失败: {load_err}")
                except Exception as e:
                    # 忽略文件名格式不匹配的文件
                    continue
            
    st.sidebar.markdown("---")

    # 加载数据 (逻辑：有自定义数据 OR (有历史查看标记 AND 有数据))
    # 注意：如果 data_cleared=True，通常不再显示数据。但如果是查看历史操作触发的，我们要强制显示。
    if 'custom_comment_data' in st.session_state:
        # 即使 data_cleared=True，但如果有 custom_comment_data (由历史记录加载)，我们也显示
        # sidebar_navigation 会负责在切换页面时清理这个 custom_comment_data
        
        processed_df = st.session_state['custom_comment_data']
        
        # 转换格式以适配现有 UI
        sentiment_map = {
            "正面": "positive",
            "负面": "negative",
            "中性": "neutral"
        }
        
        # 构造符合 UI 要求的 DataFrame
        data = {
            'id': range(1, len(processed_df) + 1),
            'comment': processed_df['review_content'],
            'sentiment': processed_df['sentiment_label'].map(sentiment_map).fillna('neutral'),
            'rating': processed_df['rating'],
            'sentiment_keywords': None,
            'solution': processed_df['solution'],
            # 生成模拟日期 (因为上传的数据可能没有日期)
            'date': pd.date_range(start='2023-01-01', periods=len(processed_df), freq='H'),
            'category': processed_df['product_category']
        }
        
        # 处理日期长度
        if len(data['date']) < len(processed_df):
             # 如果生成的日期不够，进行随机采样填充
             data['date'] = np.random.choice(data['date'], len(processed_df))
        
        # 随机打乱日期
        dates = list(data['date'])
        np.random.shuffle(dates)
        data['date'] = dates
        
        df = pd.DataFrame(data)
    else:
        # 第一次进入或数据被清空
        st.info("👋 欢迎使用评论分析！\n\n请在左侧侧边栏上传您的 CSV/XLSX 评论数据文件以开始分析。")
        return
    
    # 侧边栏过滤器
    st.sidebar.markdown("### 数据筛选")
    
    # 情感筛选
    with st.sidebar.expander("选择情感类型", expanded=False):
        sentiment_filter = st.multiselect(
            "选择情感类型",
            options=df['sentiment'].unique(),
            default=df['sentiment'].unique(),
            label_visibility="collapsed"
        )
    
    # 评分筛选
    with st.sidebar.expander("评分范围", expanded=False):
        rating_filter = st.slider(
            "评分范围",
            min_value=int(df['rating'].min()),
            max_value=int(df['rating'].max()),
            value=(int(df['rating'].min()), int(df['rating'].max())),
            label_visibility="collapsed"
        )
    
    # 类别筛选
    with st.sidebar.expander("选择产品分类", expanded=False):
        category_filter = st.multiselect(
            "选择产品分类",
            options=df['category'].unique(),
            default=df['category'].unique(),
            label_visibility="collapsed"
        )
    
    # 应用过滤器
    filtered_df = df[
        (df['sentiment'].isin(sentiment_filter)) &
        (df['rating'].between(rating_filter[0], rating_filter[1])) &
        (df['category'].isin(category_filter))
    ].copy()
    
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
    
    # 情感分布图表
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### 情感分析")
    col1, col2 = st.columns(2)
    
    with col1:
        # 情感分布饼图
        sentiment_counts = filtered_df['sentiment'].value_counts()
        fig_pie = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            title="情感分布",
            color_discrete_map={'positive': 'green', 'negative': 'red', 'neutral': 'blue'}
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # 评分分布柱状图
        rating_counts = filtered_df['rating'].value_counts().sort_index()
        fig_bar = px.bar(
            x=rating_counts.index,
            y=rating_counts.values,
            title="评分分布",
            labels={'x': '评分', 'y': '数量'},
            color_discrete_sequence=px.colors.sequential.Viridis
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 类别分析
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### 产品分类分析")
    
    # 按类别分组的情感分布
    category_sentiment = filtered_df.groupby(['category', 'sentiment']).size().unstack().fillna(0)
    
    fig_category = make_subplots(
        rows=1, cols=2,
        subplot_titles=("各产品分类评论数量", "各产品分类情感分布"),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )
    
    # 各类别评论数量
    category_counts = filtered_df['category'].value_counts()
    fig_category.add_trace(
        go.Bar(x=category_counts.index, y=category_counts.values, name="评论数量"),
        row=1, col=1
    )
    
    # 各类别情感分布
    for sentiment in ['positive', 'neutral', 'negative']:
        if sentiment in category_sentiment.columns:
            fig_category.add_trace(
                go.Bar(
                    x=category_sentiment.index,
                    y=category_sentiment[sentiment],
                    name=f"{sentiment}",
                    opacity=0.7
                ),
                row=1, col=2
            )
    
    fig_category.update_layout(height=400, showlegend=True)
    st.plotly_chart(fig_category, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 时间趋势分析
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### 时间趋势分析")
    
    # 按月份聚合数据
    filtered_df['month'] = filtered_df['date'].dt.to_period('M')
    monthly_data = filtered_df.groupby('month').agg({
        'rating': 'mean',
        'sentiment': lambda x: (x == 'positive').sum() / len(x) * 100
    }).reset_index()
    monthly_data['month'] = monthly_data['month'].dt.to_timestamp()
    
    fig_time = make_subplots(
        rows=1, cols=2,
        subplot_titles=("月度平均评分", "月度正面评论比例"),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # 月度平均评分
    fig_time.add_trace(
        go.Scatter(
            x=monthly_data['month'],
            y=monthly_data['rating'],
            mode='lines+markers',
            name="平均评分",
            line=dict(color='blue')
        ),
        row=1, col=1
    )
    
    # 月度正面评论比例
    fig_time.add_trace(
        go.Scatter(
            x=monthly_data['month'],
            y=monthly_data['sentiment'],
            mode='lines+markers',
            name="正面评论比例",
            line=dict(color='green')
        ),
        row=1, col=2
    )
    
    fig_time.update_layout(height=400, showlegend=True)
    st.plotly_chart(fig_time, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 评论关键词分析
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### 关键词分析")
    
    # 文本处理与分词函数
    def process_text(text):
        if not isinstance(text, str):
            return []
            
        # 定义停用词
        stop_words = {
            # 用户指定的停用词
            '我', '你', '他', '仅', 'i', 'you', 'also', 'be', 'after',
            # 常见中文停用词
            '的', '了', '在', '是', '有', '和', '就', '不', '人', '都', 
            '一', '一个', '上', '也', '很', '到', '说', '要', '去', '会', 
            '着', '没有', '看', '好', '自己', '这', '非常', '感觉', '觉得', 
            '比较', '这个', '那个', '我们', '你们', '他们', '它', '只是', '但是',
            # 常见英文停用词
            'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
            'to', 'of', 'in', 'on', 'at', 'for', 'with', 'it', 'this', 'that', 
            'my', 'your', 'his', 'her', 'its', 'we', 'they', 'have', 'has', 'had', 
            'do', 'does', 'did', 'can', 'could', 'will', 'would', 'should', 'not', 
            'no', 'yes', 'so', 'as', 'if', 'when', 'where', 'why', 'how', 'all', 
            'any', 'some', 'very', 'good', 'bad', 'great', 'product', 'use', 'one', 
            'just', 'get', 'from', 'out', 'up', 'down', 'about', 'than', 'then', 
            'now', 'only', 'well', 'much', 'more', 'other', 'which', 'what', 
            'who', 'whom', 'whose', 'cable', 'charging', 'phone',
            # 补充英文停用词
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
        
        # 使用jieba分词 (jieba也能处理英文)
        # 为了更好的英文支持，可以先用正则提取英文单词，再用jieba处理剩下的中文
        # 这里简化处理，直接用jieba，它会将连续的英文字母作为一个词
        words = jieba.cut(text)
        
        # 过滤
        result = []
        for word in words:
            word = word.strip().lower()
            # 过滤掉长度为1的词，过滤掉停用词，过滤掉纯数字和标点
            if len(word) > 1 and word not in stop_words and not word.isdigit() and not re.match(r'^[^\w\s]+$', word):
                result.append(word)
                
        return result
    
    # 对所有评论进行分词
    all_words = []
    for comment in filtered_df['comment']:
        all_words.extend(process_text(comment))
    
    # 统计词频
    word_counts = Counter(all_words)
    top_words = word_counts.most_common(20)
    top_words_df = pd.DataFrame(top_words, columns=['词汇', '频次'])
    
    # 显示词频表
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 高频词汇")
        st.dataframe(top_words_df)
    
    with col2:
        st.markdown("#### 词频图")
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
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 情感相关的关键词
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### 情感相关关键词")
    
    # 正面评论关键词
    positive_comments = filtered_df[filtered_df['sentiment'] == 'positive']['comment']
    positive_words = []
    for comment in positive_comments:
        # 去重，每条评论中相同的词只计一次
        unique_words = set(process_text(comment))
        positive_words.extend(unique_words)
    positive_word_counts = Counter(positive_words).most_common(10)
    
    # 负面评论关键词
    negative_comments = filtered_df[filtered_df['sentiment'] == 'negative']['comment']
    negative_words = []
    for comment in negative_comments:
        # 去重，每条评论中相同的词只计一次
        unique_words = set(process_text(comment))
        negative_words.extend(unique_words)
    negative_word_counts = Counter(negative_words).most_common(10)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 正面情感词")
        positive_words_df = pd.DataFrame(positive_word_counts, columns=['词汇', '频次'])
        st.dataframe(positive_words_df)
    
    with col2:
        st.markdown("#### 负面情感词")
        negative_words_df = pd.DataFrame(negative_word_counts, columns=['词汇', '频次'])
        st.dataframe(negative_words_df)
    st.markdown('</div>', unsafe_allow_html=True)
    
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