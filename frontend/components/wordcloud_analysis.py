import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud, ImageColorGenerator
import jieba
import re
from collections import Counter
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
import io
import base64
import sys
import os

# 添加 utils 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(os.path.dirname(current_dir), 'utils')
if utils_dir not in sys.path:
    sys.path.append(utils_dir)

try:
    from layout import render_header
except ImportError:
    def render_header(title, subtitle=None): st.title(title)

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def show_wordcloud_analysis(backend_url=None):
    """
    显示内容词云分析页面
    """
    render_header("内容词云分析", "可视化展示文本核心关键词")
    
    # 示例数据加载
    @st.cache_data
    def load_sample_data():
        # 创建示例评论数据
        np.random.seed(42)
        n_samples = 300
        
        # 示例评论内容
        comments = [
            "这个产品真的很棒，质量非常好，使用体验很棒！",
            "服务态度很好，解决问题很及时，非常满意。",
            "界面设计简洁美观，操作简单，用户体验很好。",
            "功能很实用，解决了我的问题，值得推荐。",
            "性价比很高，比同类产品好很多，会继续支持。",
            "客服响应速度快，专业水平高，解答问题很清楚。",
            "产品更新很及时，每次都有新功能，越来越好了。",
            "包装很精美，送人自用都很合适，品质有保障。",
            "产品质量有问题，用了几天就坏了，很失望。",
            "客服态度不好，问题解决不了，体验很差。",
            "界面设计复杂，操作困难，用户体验不好。",
            "功能不实用，有很多bug，使用起来很麻烦。",
            "价格太高，性价比低，不值得购买。",
            "物流太慢，等了很久才收到，包装也不好。",
            "产品与描述不符，实际效果很差，不推荐。",
            "售后服务差，有问题找不到人解决，很糟糕。",
            "产品还可以，没有特别惊喜，但也没有太大问题。",
            "服务一般，解决了基本问题，但还有改进空间。",
            "界面设计普通，功能基本满足需求，使用起来还行。",
            "价格适中，质量一般，性价比还可以接受。",
            "物流速度正常，包装普通，整体体验一般。",
            "产品功能基本满足需求，但有些地方可以优化。",
            "服务态度还可以，解决问题效率一般，有待提高。",
            "整体感觉一般，没有特别满意的地方，也没有特别不满。",
            "这个产品的设计很人性化，考虑到了用户的需求，使用起来非常方便。",
            "客服团队非常专业，无论什么时候联系都能得到及时回复。",
            "产品的质量超出预期，细节处理得很好，能感受到用心。",
            "价格虽然不便宜，但考虑到质量和功能，性价比很高。",
            "界面简洁大方，没有多余的功能，专注于核心体验，很喜欢。",
            "使用过程中遇到了一些小问题，但客服很快就帮我解决了，很满意。",
            "产品功能很全面，满足了我所有的需求，推荐给朋友。",
            "包装很用心，产品保护得很好，开箱体验很棒。",
            "产品用了不到一周就出现问题了，质量有待提高。",
            "客服回复很慢，等了两天才得到回复，体验很不好。",
            "界面设计过于复杂，找功能很困难，需要简化。",
            "功能虽然多，但很多都不实用，应该精简一下。",
            "价格偏高，同类产品中有更便宜的选择，性价比不高。",
            "物流包装破损，产品有划痕，很影响使用体验。",
            "实际产品与图片描述有差异，感觉被误导了，不推荐。",
            "售后服务态度差，问题一直得不到解决，很失望。",
            "产品中规中矩，没有特别突出的地方，但也没有明显缺点。",
            "服务还可以，解决了问题，但过程有点曲折，有待改进。",
            "界面设计一般，功能齐全但不够美观，还有提升空间。",
            "价格合理，质量符合预期，整体体验还行。",
            "物流速度正常，包装普通，产品完好无损。",
            "功能基本满足需求，但有些地方不够人性化，需要优化。",
            "服务态度一般，解决问题效率不高，需要提高专业性。",
            "整体体验普通，没有特别满意的地方，但也没有不满。",
            "产品的创新点很多，解决了传统产品的痛点，很惊喜。",
            "客服团队训练有素，无论多复杂的问题都能耐心解答。",
            "产品质量一流，每个细节都处理得很好，物超所值。",
            "虽然价格不低，但考虑到品质和功能，完全值得这个价格。",
            "界面设计简约而不简单，每个功能都恰到好处，使用体验极佳。",
            "使用中遇到的问题都能快速得到解决，售后服务很到位。",
            "产品功能强大且实用，大大提高了我的工作效率，强烈推荐。",
            "从包装到产品本身都体现了高端品质，开箱就是一种享受。",
            "产品刚用两天就出现故障，质量控制明显有问题。",
            "客服态度恶劣，不仅不解决问题，还推卸责任，非常失望。",
            "界面设计混乱，功能分布不合理，使用起来非常困难。",
            "功能华而不实，很多都是噱头，实际使用价值很低。",
            "价格虚高，产品质量配不上这个价格，性价比极低。",
            "物流包装简陋，产品在运输过程中受损，影响使用。",
            "收到的产品与描述严重不符，感觉受到了欺骗，强烈不推荐。",
            "售后服务形同虚设，投诉无门，问题永远得不到解决。",
            "产品表现平平，没有特别出彩的地方，但也没有明显缺陷。",
            "服务态度一般，虽然解决了问题，但过程不够顺畅，有待改进。",
            "界面设计中规中矩，功能齐全但缺乏亮点，还有提升空间。",
            "价格适中，质量符合价位，整体体验符合预期。",
            "物流速度正常，包装一般，产品完好，没有惊喜也没有失望。",
            "功能基本满足需求，但用户体验不够流畅，需要进一步优化。",
            "服务态度还可以，但专业性有待提高，解决问题的效率不高。"
        ]
        
        # 生成随机评论数据
        all_comments = []
        sentiments = []
        ratings = []
        categories = []
        
        for i in range(n_samples):
            # 随机选择一条评论
            comment = np.random.choice(comments)
            
            # 随机添加一些变化
            if np.random.random() > 0.7:
                extra_words = np.random.choice([
                    "强烈推荐", "还会购买", "值得信赖", "有待改进", 
                    "希望优化", "建议增加", "体验很好", "非常满意",
                    "不太满意", "问题很多", "功能强大", "设计精美"
                ])
                comment += " " + extra_words
            
            all_comments.append(comment)
            
            # 根据评论内容确定情感倾向
            if any(word in comment for word in ["棒", "好", "满意", "推荐", "支持", "惊喜", "喜欢"]):
                sentiments.append('positive')
                ratings.append(np.random.randint(4, 6))
            elif any(word in comment for word in ["问题", "差", "失望", "麻烦", "不好", "糟糕", "不满"]):
                sentiments.append('negative')
                ratings.append(np.random.randint(1, 3))
            else:
                sentiments.append('neutral')
                ratings.append(np.random.randint(3, 5))
            
            # 随机分配类别
            categories.append(np.random.choice(['产品', '服务', '界面', '功能', '价格']))
        
        # 创建日期
        dates = pd.date_range(start='2023-01-01', periods=n_samples, freq='D')
        np.random.shuffle(dates.values)
        
        # 创建DataFrame
        df = pd.DataFrame({
            'id': range(1, n_samples + 1),
            'comment': all_comments,
            'sentiment': sentiments,
            'rating': ratings,
            'date': dates[:n_samples],
            'category': categories
        })
        
        return df
    
    # 加载数据
    df = load_sample_data()
    
    # 侧边栏控制面板
    st.sidebar.markdown("### 词云设置")
    
    # 情感筛选
    sentiment_filter = st.sidebar.multiselect(
        "选择情感类型",
        options=df['sentiment'].unique(),
        default=df['sentiment'].unique()
    )
    
    # 类别筛选
    category_filter = st.sidebar.multiselect(
        "选择类别",
        options=df['category'].unique(),
        default=df['category'].unique()
    )
    
    # 词云形状
    wordcloud_shape = st.sidebar.selectbox(
        "词云形状",
        options=["矩形", "圆形", "椭圆"],
        index=0
    )
    
    # 最大词汇数
    max_words = st.sidebar.slider(
        "最大词汇数",
        min_value=50,
        max_value=200,
        value=100,
        step=10
    )
    
    # 词云配色方案
    color_scheme = st.sidebar.selectbox(
        "配色方案",
        options=["viridis", "plasma", "inferno", "magma", "Blues", "Reds", "Greens"],
        index=0
    )
    
    # 确保颜色映射名称使用正确的大小写格式
    # matplotlib要求某些颜色映射名称首字母大写
    valid_colormaps = {
        "viridis": "viridis",
        "plasma": "plasma", 
        "inferno": "inferno",
        "magma": "magma",
        "blues": "Blues",
        "reds": "Reds", 
        "greens": "Greens",
        "Blues": "Blues",
        "Reds": "Reds",
        "Greens": "Greens"
    }
    color_scheme = valid_colormaps.get(color_scheme, color_scheme)
    
    # 应用过滤器
    filtered_df = df[
        (df['sentiment'].isin(sentiment_filter)) &
        (df['category'].isin(category_filter))
    ].copy()
    
    # 显示数据概览
    st.markdown("### 数据概览")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("总评论数", len(filtered_df))
    
    with col2:
        total_words = sum(len(comment.split()) for comment in filtered_df['comment'])
        st.metric("总词数", total_words)
    
    with col3:
        avg_words = total_words / len(filtered_df) if len(filtered_df) > 0 else 0
        st.metric("平均词数/评论", f"{avg_words:.1f}")
    
    # 中文分词函数
    def chinese_word_cut(text):
        # 只保留中文字符
        text = re.sub(r'[^\u4e00-\u9fa5]', '', text)
        # 使用jieba进行分词
        words = jieba.cut(text)
        # 过滤掉停用词和短词
        stop_words = ['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这']
        return [word for word in words if len(word) > 1 and word not in stop_words]
    
    # 对所有评论进行分词
    all_words = []
    for comment in filtered_df['comment']:
        all_words.extend(chinese_word_cut(comment))
    
    # 统计词频
    word_counts = Counter(all_words)
    
    # 显示高频词汇
    st.markdown("### 高频词汇分析")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 词汇频次表")
        top_words = word_counts.most_common(20)
        top_words_df = pd.DataFrame(top_words, columns=['词汇', '频次'])
        st.dataframe(top_words_df)
    
    with col2:
        st.markdown("#### 词汇频次图")
        fig_words = px.bar(
            x=[word[0] for word in top_words],
            y=[word[1] for word in top_words],
            title="高频词汇分布",
            labels={'x': '词汇', 'y': '频次'},
            color=[word[1] for word in top_words],
            color_continuous_scale=color_scheme
        )
        fig_words.update_xaxes(tickangle=45)
        st.plotly_chart(fig_words, use_container_width=True)
    
    # 生成词云
    st.markdown("### 词云图")
    
    # 根据选择设置词云形状
    if wordcloud_shape == "圆形":
        mask = np.zeros((800, 800), dtype=np.uint8)
        for i in range(800):
            for j in range(800):
                if (i-400)**2 + (j-400)**2 > 350**2:
                    mask[i, j] = 255
    elif wordcloud_shape == "椭圆":
        mask = np.zeros((800, 800), dtype=np.uint8)
        for i in range(800):
            for j in range(800):
                if ((i-400)/400)**2 + ((j-400)/250)**2 > 1:
                    mask[i, j] = 255
    else:  # 矩形
        mask = None
    
    # 创建词云
    wordcloud = WordCloud(
        font_path='simhei.ttf',  # 使用黑体
        background_color='white',
        max_words=max_words,
        mask=mask,
        contour_width=1,
        contour_color='steelblue',
        colormap=color_scheme
    ).generate_from_frequencies(word_counts)
    
    # 显示词云
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    
    # 将图像转换为base64以便在Streamlit中显示
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=300)
    buf.seek(0)
    img_bytes = buf.getvalue()
    encoded = base64.b64encode(img_bytes).decode('utf-8')
    html_img = f'<img src="data:image/png;base64,{encoded}" class="img-fluid">'
    st.markdown(html_img, unsafe_allow_html=True)
    plt.close()
    
    # 按情感分类的词云
    st.markdown("### 按情感分类的词云")
    
    # 获取不同情感的数据
    positive_comments = filtered_df[filtered_df['sentiment'] == 'positive']['comment']
    negative_comments = filtered_df[filtered_df['sentiment'] == 'negative']['comment']
    neutral_comments = filtered_df[filtered_df['sentiment'] == 'neutral']['comment']
    
    # 创建三列布局
    col1, col2, col3 = st.columns(3)
    
    # 正面情感词云
    with col1:
        st.markdown("#### 正面情感词云")
        positive_words = []
        for comment in positive_comments:
            positive_words.extend(chinese_word_cut(comment))
        positive_word_counts = Counter(positive_words)
        
        if positive_word_counts:
            positive_wordcloud = WordCloud(
                font_path='simhei.ttf',
                background_color='white',
                max_words=50,
                colormap='Greens'
            ).generate_from_frequencies(positive_word_counts)
            
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.imshow(positive_wordcloud, interpolation='bilinear')
            ax.axis('off')
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=200)
            buf.seek(0)
            img_bytes = buf.getvalue()
            encoded = base64.b64encode(img_bytes).decode('utf-8')
            html_img = f'<img src="data:image/png;base64,{encoded}" class="img-fluid">'
            st.markdown(html_img, unsafe_allow_html=True)
            plt.close()
        else:
            st.info("没有正面情感评论数据")
    
    # 负面情感词云
    with col2:
        st.markdown("#### 负面情感词云")
        negative_words = []
        for comment in negative_comments:
            negative_words.extend(chinese_word_cut(comment))
        negative_word_counts = Counter(negative_words)
        
        if negative_word_counts:
            negative_wordcloud = WordCloud(
                font_path='simhei.ttf',
                background_color='white',
                max_words=50,
                colormap='Reds'
            ).generate_from_frequencies(negative_word_counts)
            
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.imshow(negative_wordcloud, interpolation='bilinear')
            ax.axis('off')
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=200)
            buf.seek(0)
            img_bytes = buf.getvalue()
            encoded = base64.b64encode(img_bytes).decode('utf-8')
            html_img = f'<img src="data:image/png;base64,{encoded}" class="img-fluid">'
            st.markdown(html_img, unsafe_allow_html=True)
            plt.close()
        else:
            st.info("没有负面情感评论数据")
    
    # 中性情感词云
    with col3:
        st.markdown("#### 中性情感词云")
        neutral_words = []
        for comment in neutral_comments:
            neutral_words.extend(chinese_word_cut(comment))
        neutral_word_counts = Counter(neutral_words)
        
        if neutral_word_counts:
            neutral_wordcloud = WordCloud(
                font_path='simhei.ttf',
                background_color='white',
                max_words=50,
                colormap='Blues'
            ).generate_from_frequencies(neutral_word_counts)
            
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.imshow(neutral_wordcloud, interpolation='bilinear')
            ax.axis('off')
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=200)
            buf.seek(0)
            img_bytes = buf.getvalue()
            encoded = base64.b64encode(img_bytes).decode('utf-8')
            html_img = f'<img src="data:image/png;base64,{encoded}" class="img-fluid">'
            st.markdown(html_img, unsafe_allow_html=True)
            plt.close()
        else:
            st.info("没有中性情感评论数据")
    
    # 按类别分类的词云
    st.markdown("### 按类别分类的词云")
    
    # 获取不同类别的数据
    categories = filtered_df['category'].unique()
    
    # 创建两列布局
    for i in range(0, len(categories), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(categories):
                category = categories[i + j]
                with cols[j]:
                    st.markdown(f"#### {category}类词云")
                    category_comments = filtered_df[filtered_df['category'] == category]['comment']
                    category_words = []
                    for comment in category_comments:
                        category_words.extend(chinese_word_cut(comment))
                    category_word_counts = Counter(category_words)
                    
                    if category_word_counts:
                        category_wordcloud = WordCloud(
                            font_path='simhei.ttf',
                            background_color='white',
                            max_words=50,
                            colormap='viridis'
                        ).generate_from_frequencies(category_word_counts)
                        
                        fig, ax = plt.subplots(figsize=(6, 5))
                        ax.imshow(category_wordcloud, interpolation='bilinear')
                        ax.axis('off')
                        
                        buf = io.BytesIO()
                        plt.savefig(buf, format='png', bbox_inches='tight', dpi=200)
                        buf.seek(0)
                        img_bytes = buf.getvalue()
                        encoded = base64.b64encode(img_bytes).decode('utf-8')
                        html_img = f'<img src="data:image/png;base64,{encoded}" class="img-fluid">'
                        st.markdown(html_img, unsafe_allow_html=True)
                        plt.close()
                    else:
                        st.info(f"没有{category}类评论数据")
    
    # 词汇趋势分析
    st.markdown("### 词汇趋势分析")
    
    # 选择要分析的词汇
    top_10_words = [word[0] for word in word_counts.most_common(10)]
    selected_words = st.multiselect(
        "选择要分析趋势的词汇",
        options=top_10_words,
        default=top_10_words[:5]
    )
    
    if selected_words:
        # 按月份统计词汇出现频率
        filtered_df['month'] = filtered_df['date'].dt.to_period('M')
        
        word_trends = {}
        for word in selected_words:
            monthly_counts = []
            for month in filtered_df['month'].unique():
                month_comments = filtered_df[filtered_df['month'] == month]['comment']
                count = sum(1 for comment in month_comments if word in comment)
                monthly_counts.append(count)
            word_trends[word] = monthly_counts
        
        # 创建趋势图
        months = [str(month) for month in filtered_df['month'].unique()]
        fig_trend = go.Figure()
        
        for word, counts in word_trends.items():
            fig_trend.add_trace(
                go.Scatter(
                    x=months,
                    y=counts,
                    mode='lines+markers',
                    name=word
                )
            )
        
        fig_trend.update_layout(
            title="词汇出现频率趋势",
            xaxis_title="月份",
            yaxis_title="出现次数",
            height=500
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
    
    # 下载词频数据
    st.markdown("### 数据下载")
    
    # 创建词频DataFrame
    word_freq_df = pd.DataFrame(word_counts.most_common(), columns=['词汇', '频次'])
    
    # 转换为CSV
    csv = word_freq_df.to_csv(index=False, encoding='utf-8-sig')
    
    # 提供下载按钮
    st.download_button(
        label="下载词频数据 (CSV)",
        data=csv,
        file_name="word_frequency.csv",
        mime="text/csv",
        key='download-csv'
    )
    
    st.markdown("---")
    st.success("词云分析完成！")