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
import json
from streamlit.components.v1 import html
import datetime

# 添加 utils 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(os.path.dirname(current_dir), 'utils')
if utils_dir not in sys.path:
    sys.path.append(utils_dir)

# Add models path
models_dir = os.path.join(os.path.dirname(current_dir), 'models')
if models_dir not in sys.path:
    sys.path.append(models_dir)

try:
    from text.qwen_model import QwenModel
except ImportError:
    QwenModel = None

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
    使用 HTML+CSS+JS 实现的客户端真·悬浮交互布局 (支持 N 个图表轮播)
    特性：点击左侧/右侧触发轮换，带平滑动画，无需后端重绘。
    """
    # 1. 准备数据: 执行回调并将 Plotly Figure 转换为 JSON
    chart_data = {}
    valid_keys = []
    
    # Use initial_order as the source of truth for the sequence
    for key in initial_order:
        if key in component_map:
            try:
                fig = component_map[key]()
                if fig:
                    fig_dict = json.loads(fig.to_json())
                    # Clean up layout for CSS card
                    if 'layout' in fig_dict:
                        fig_dict['layout'].pop('width', None)
                        fig_dict['layout'].pop('height', None)
                        fig_dict['layout']['autosize'] = True
                        fig_dict['layout']['margin'] = dict(l=20, r=20, t=40, b=20)
                        fig_dict['layout']['paper_bgcolor'] = 'rgba(0,0,0,0)'
                    
                    chart_data[key] = fig_dict
                    if key not in valid_keys:
                        valid_keys.append(key)
            except Exception as e:
                print(f"Error rendering {key}: {e}")

    chart_data_js = json.dumps(chart_data)
    order_list_js = json.dumps(valid_keys)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 10px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background: transparent;
                overflow: hidden;
            }}
            .container {{
                position: relative;
                width: 100%;
                height: 480px; /* Increased height for better fit */
                perspective: 1200px;
                display: flex;
                justify-content: center;
                align-items: flex-start;
                padding-top: 20px;
            }}
            
            /* 卡片基础样式 */
            .chart-card {{
                position: absolute;
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                transition: all 0.6s cubic-bezier(0.25, 0.8, 0.25, 1);
                overflow: hidden;
                box-sizing: border-box;
                display: block;
                /* Default to hidden state to prevent flash */
                opacity: 0;
                transform: scale(0.8) translateY(50px);
                z-index: 0;
                pointer-events: none;
            }}
            
            /* 状态类 - 通过JS切换 */
            
            /* Center / Top Card */
            .chart-card.pos-top {{
                opacity: 1;
                width: 55%; 
                height: 400px;
                transform: translateX(0) scale(1);
                z-index: 20;
                left: 22.5%; /* (100-55)/2 */
                top: 0;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                border: 2px solid #3b82f6;
                pointer-events: auto;
            }}

            /* Left Background Card */
            .chart-card.pos-left {{
                opacity: 0.7;
                width: 45%;
                height: 360px;
                transform: translateX(-60%) scale(0.9) perspective(1000px) rotateY(15deg);
                z-index: 10;
                left: 22.5%; /* Origin same as center, moved by transform */
                top: 20px;
                filter: brightness(0.95);
                pointer-events: none; /* Let clicks pass through to layer */
            }}

            /* Right Background Card */
            .chart-card.pos-right {{
                opacity: 0.7;
                width: 45%;
                height: 360px;
                transform: translateX(60%) scale(0.9) perspective(1000px) rotateY(-15deg);
                z-index: 10;
                left: 22.5%; /* Origin same as center, moved by transform */
                top: 20px;
                filter: brightness(0.95);
                pointer-events: none;
            }}
            
            /* Hidden Card */
            .chart-card.hidden {{
                opacity: 0;
                transform: translateY(50px) scale(0.8);
                z-index: 0;
                pointer-events: none;
                display: none; /* remove from layout flow entirely if needed */
            }}

            .plot-container {{
                width: 100%;
                height: 100%;
            }}

            /* 交互层 - 用于捕捉点击 */
            .nav-area {{
                position: absolute;
                top: 0;
                height: 100%;
                width: 30%;
                z-index: 30;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.3s;
            }}
            
            .nav-left {{
                left: 0;
            }}
            
            .nav-right {{
                right: 0;
            }}
            
            .nav-area:hover {{
                background: rgba(0,0,0,0.02);
            }}
            
            /* Chevron Arrows */
            .arrow {{
                font-size: 40px;
                color: rgba(0,0,0,0.2);
                font-weight: bold;
                transition: color 0.3s;
            }}
            .nav-area:hover .arrow {{
                color: rgba(59, 130, 246, 0.6);
            }}

        </style>
    </head>
    <body>
        <div class="container" id="container">
            <!-- Navigation Areas -->
            <div class="nav-area nav-left" id="btnLeft">
                <div class="arrow">‹</div>
            </div>
            <div class="nav-area nav-right" id="btnRight">
                <div class="arrow">›</div>
            </div>
        </div>

        <script>
            const chartData = {chart_data_js};
            const orderList = {order_list_js}; // All available keys
            let activeIndex = 0; 
            
            const container = document.getElementById('container');
            const cardElements = {{}};
            const plots = {{}};

            // Initialize all cards
            orderList.forEach(key => {{
                if (!chartData[key]) return;
                
                const card = document.createElement('div');
                card.id = 'card-' + key;
                card.className = 'chart-card hidden'; 
                
                const plotDiv = document.createElement('div');
                plotDiv.className = 'plot-container';
                card.appendChild(plotDiv);
                
                // Add title overlay if needed, or rely on plotly title
                
                container.appendChild(card);
                cardElements[key] = card;
                
                // Render Plotly
                const spec = chartData[key];
                const config = {{displayModeBar: false, responsive: true, staticPlot: true}}; 
                
                Plotly.newPlot(plotDiv, spec.data, spec.layout, config).then(gd => {{
                    plots[key] = gd;
                }});
            }});

            function updateLayout() {{
                const total = orderList.length;
                if (total === 0) return;
                
                // Calculate indices
                const centerIdx = activeIndex;
                const leftIdx = (activeIndex - 1 + total) % total;
                const rightIdx = (activeIndex + 1) % total;
                
                const centerKey = orderList[centerIdx];
                const leftKey = orderList[leftIdx];
                const rightKey = orderList[rightIdx];
                
                // Reset/Assign classes
                // We iterate all to ensure ones that should be hidden get 'hidden' class
                orderList.forEach(key => {{
                    const el = cardElements[key];
                    if (!el) return;
                    
                    // Remove all pos classes first
                    el.classList.remove('pos-top', 'pos-left', 'pos-right', 'hidden');
                    
                    if (key === centerKey) {{
                        el.classList.add('pos-top');
                        el.style.display = 'block';
                    }} else if (key === leftKey) {{
                        el.classList.add('pos-left');
                        el.style.display = 'block';
                    }} else if (key === rightKey) {{
                        el.classList.add('pos-right');
                        el.style.display = 'block';
                    }} else {{
                        el.classList.add('hidden');
                        // Optional: delay display:none to allow transition out? 
                        // For simplicity, we keep display:block but opacity:0 from css
                        // Actually, 'hidden' class sets display:none or opacity:0
                    }}
                }});
                
                // Trigger resize for the visible ones to ensure they fit their new container size
                // (Center is larger than sides)
                setTimeout(() => {{
                    [centerKey, leftKey, rightKey].forEach(k => {{
                        if (plots[k]) Plotly.Plots.resize(plots[k]);
                    }});
                }}, 605); // slightly after transition
            }}

            function moveNext() {{
                activeIndex = (activeIndex + 1) % orderList.length;
                updateLayout();
            }}
            
            function movePrev() {{
                activeIndex = (activeIndex - 1 + orderList.length) % orderList.length;
                updateLayout();
            }}

            // Event Listeners
            document.getElementById('btnRight').addEventListener('click', moveNext);
            document.getElementById('btnLeft').addEventListener('click', movePrev);
            
            // Keyboard nav
            document.addEventListener('keydown', (e) => {{
                if (e.key === 'ArrowRight') moveNext();
                if (e.key === 'ArrowLeft') movePrev();
            }});

            // Initial render
            // Small delay to ensure container is ready
            setTimeout(updateLayout, 100);

        </script>
    </body>
    </html>
    """
    
    html(html_code, height=520, scrolling=False)


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
                            st.session_state.ai_assistant_open = False # 防止AI助手自动弹出
                            with st.spinner(f"加载 {display_time}..."):
                                try:
                                    loaded_df = pd.read_csv(os.path.join(history_dir, f))
                                    st.session_state['custom_comment_data'] = loaded_df
                                    # 不要覆盖当前的工作数据，否则退出历史查看后无法找回
                                    # loaded_df.to_csv(history_file_path, index=False) 
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


def show_comment_analysis(backend_url=None):
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
            # 设置为 False 以便 render_sidebar 中的自动加载逻辑生效，重新加载 default history file
            st.session_state['data_cleared'] = False
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
    
    
    # 新增：定义各个图表的渲染函数
    def render_sentiment_pie():
        sentiment_counts = filtered_df['sentiment'].value_counts().reset_index()
        sentiment_counts.columns = ['sentiment', 'count']
        
        fig_pie = px.pie(
            sentiment_counts,
            values='count',
            names='sentiment',
            color='sentiment',
            title="情感分布",
            color_discrete_map={
                'positive': '#00CC96', 
                'negative': '#EF553B', 
                'neutral': '#636EFA'
            }
        )
        return fig_pie

    def render_rating_bar():
        # 评分分布：使用更鲜艳的颜色，避免 Viridis 默认的深紫色/黑色
        rating_counts = filtered_df['rating'].value_counts().sort_index()
        fig_bar = px.bar(
            x=rating_counts.index,
            y=rating_counts.values,
            title="评分分布",
            labels={'x': '评分', 'y': '数量'},
            # 使用 Orange 或其他明亮色系，或者根据评分渐变
            color=rating_counts.index,
            color_continuous_scale='RdYlGn' # 红黄绿渐变，低分红高分绿
        )
        fig_bar.update_layout(coloraxis_showscale=False)
        return fig_bar
    
    def render_sentiment_summary_bubble():
        sentiment_summary = filtered_df.groupby('sentiment').agg({
            'rating': 'mean',
            'id': 'count'
        }).rename(columns={'rating': '平均评分', 'id': '评论数'}).reset_index()
        
        fig = px.scatter(
            sentiment_summary,
            x='sentiment',
            y='平均评分',
            size='评论数',
            color='sentiment',
            title="情感摘要 (大小=数量)",
            color_discrete_map={'positive': 'green', 'negative': 'red', 'neutral': 'blue'}
        )
        return fig

    
    # 类别分析定义
    def render_category_count_bar():
        category_counts = filtered_df['category'].value_counts()
        fig_cat_count = px.bar(
            x=category_counts.index, 
            y=category_counts.values,
            title="各产品分类评论数量",
            labels={'x': '产品分类', 'y': '评论数量'}
        )
        fig_cat_count.update_traces(marker_color='#3b82f6')
        return fig_cat_count

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
        return fig_cat_sentiment

    def render_category_treemap():
        cat_summary = filtered_df.groupby('category').agg({
            'rating': 'mean',
            'id': 'count'
        }).rename(columns={'rating': '平均评分', 'id': '评论总数'}).reset_index()
        
        fig = px.treemap(
            cat_summary,
            path=['category'],
            values='评论总数',
            color='平均评分',
            title="分类统计详情 (面积=评论数)",
            color_continuous_scale='Viridis'
        )
        return fig

    
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
        return fig_rating_trend
        
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
        return fig_sentiment_trend

    def render_monthly_kpi_card():
        display_monthly = monthly_data.copy()
        display_monthly['month_str'] = display_monthly['month'].dt.strftime('%Y-%m')
        
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.1)
        fig.add_trace(go.Scatter(x=display_monthly['month_str'], y=display_monthly['rating'], mode='lines+markers', name='评分'), row=1, col=1)
        fig.add_trace(go.Bar(x=display_monthly['month_str'], y=display_monthly['count'], name='评论数', marker_color='#3b82f6'), row=2, col=1)
        fig.add_trace(go.Scatter(x=display_monthly['month_str'], y=display_monthly['sentiment'], mode='lines+markers', name='正面率'), row=3, col=1)
        
        fig.update_layout(title="月度综合指标", showlegend=False)
        return fig


    # 高频词分析定义
    
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
            fig_words.update_traces(marker_color='#3b82f6')
            fig_words.update_xaxes(tickangle=45)
            return fig_words
        else:
            return None

    def render_top_words_treemap():
        fig = px.treemap(
            top_words_df,
            path=['词汇'],
            values='频次',
            title="高频词汇 (面积表示频次)",
            color='频次',
            color_continuous_scale='Blues'
        )
        return fig

    def render_sentiment_butterfly():
        # Top 10 Pos vs Top 10 Neg
        pos = positive_words_df.copy()
        pos['Type'] = '正面'
        neg = negative_words_df.copy()
        neg['Type'] = '负面'
        neg['频次'] = -neg['频次'] # Make negative for diverging bar
        
        combined = pd.concat([pos, neg])
        
        fig = px.bar(
            combined,
            y='词汇',
            x='频次',
            color='Type',
            orientation='h',
            title="情感关键词对比 (左负右正)",
            color_discrete_map={'正面': 'green', '负面': 'red'}
        )
        return fig

    # ---------------- 评论搜索与智能应对 ----------------
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### 评论搜索与智能应对")
    
    col_search, col_action = st.columns([4, 1])
    with col_search:
        search_keyword = st.text_input("输入关键词搜索评论...", placeholder="输入关键词搜索评论，例如：正面、负面、中性...", key="comment_search_input", label_visibility="collapsed")
    with col_action:
        do_search = st.button("搜索", use_container_width=True)
        
    if search_keyword:
        # Enhanced Filter Logic: Support Sentiment Keywords
        sentiment_map_search = {
             '正面': 'positive', 'positive': 'positive',
             '负面': 'negative', 'negative': 'negative',
             '中性': 'neutral', '中立': 'neutral', 'neutral': 'neutral'
        }
        
        lower_keyword = search_keyword.strip().lower()
        search_target_sentiment = sentiment_map_search.get(lower_keyword)
        
        if search_target_sentiment:
             search_results = filtered_df[filtered_df['sentiment'] == search_target_sentiment]
             match_msg = f"情感为 '{search_keyword}'"
        else:
             search_results = filtered_df[filtered_df['comment'].str.contains(search_keyword, case=False, na=False)]
             match_msg = f"包含 '{search_keyword}'"
        
        if not search_results.empty:
            st.success(f"找到 {len(search_results)} 条{match_msg}的评论")
            
            # 使用 container(height=...) 创建可滚动的列表视图
            # 设置合适的高度以展示约 10 条数据 (假设每条约 100px)
            search_container = st.container(height=600, border=True)
            
            with search_container:
                # Iterate all results (Container handles scrolling)
                for idx, row in search_results.iterrows():
                    # Emotion color
                    sentiment_color = "#00CC96" if row['sentiment'] == 'positive' else "#EF553B" if row['sentiment'] == 'negative' else "#636EFA"
                    sentiment_bg = "rgba(0, 204, 150, 0.1)" if row['sentiment'] == 'positive' else "rgba(239, 85, 59, 0.1)" if row['sentiment'] == 'negative' else "rgba(99, 110, 250, 0.1)"
                    sentiment_cn = "正面" if row['sentiment'] == 'positive' else "负面" if row['sentiment'] == 'negative' else "中性"
                    
                    with st.container():
                        st.markdown(f"""
                        <div style="background-color: {sentiment_bg}; padding: 12px; border-radius: 8px; margin-bottom: 12px; border-left: 5px solid {sentiment_color};">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                <span style="font-weight: bold; font-size: 0.9em; color: {sentiment_color}; background: white; padding: 2px 8px; border-radius: 4px;">{sentiment_cn}</span>
                                <span style="font-size: 0.85em; color: #666;">分类: {row['category']} | 评分: {row['rating']}</span>
                            </div>
                            <div style="font-size: 1em; color: #333; line-height: 1.5;">{row['comment']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # AI Suggestion (Only for Negative)
                        if row['sentiment'] == 'negative':
                            if st.button(f"🤖 生成智能应对建议", key=f"ai_sugg_{idx}"):
                                if QwenModel:
                                    with st.spinner("AI 正在分析并生成应对策略..."):
                                        try:
                                            api_key = os.getenv("DASHSCOPE_API_KEY")
                                            if api_key:
                                                model = QwenModel(api_key=api_key)
                                                prompt = f"针对以下电商评论生成具体的应对措施和回复建议。评论：'{row['comment']}'。分类：{row['category']}。情感：{sentiment_cn}。请给出：1.潜在问题分析 2.建议回复话术 3.改进措施。"
                                                response = model.predict(prompt)
                                                if response.get("status") == "success":
                                                    st.info(response.get("text"))
                                                else:
                                                    st.error(f"生成失败: {response.get('text')}")
                                            else:
                                                st.warning("未检测到 API Key，请检查环境配置。")
                                        except Exception as e:
                                            st.error(f"处理出错: {str(e)}")
                                else:
                                    st.warning("AI 模型组件未加载")
                        
                        st.markdown("---") # Separator
        else:
            st.warning(f"未找到包含 '{search_keyword}' 的评论")
            
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- 文本分析交互式布局 ----------------
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### 文本分析互动视图")

    render_interactive_layout(
        section_id="keyword_analysis",
        component_map={
            'pie_chart': render_sentiment_pie,
            'bar_chart': render_rating_bar,
            'summary_plot': render_sentiment_summary_bubble,
            'cat_count_bar': render_category_count_bar,
            'cat_sentiment_bar': render_category_sentiment_bar,
            'cat_treemap': render_category_treemap,
            'rating_line': render_rating_trend_line,
            'sentiment_line': render_sentiment_trend_line,
            'monthly_plot': render_monthly_kpi_card,
            'word_bar': render_word_freq_bar,
            'word_treemap': render_top_words_treemap,
            'sentiment_bar': render_sentiment_butterfly
        },
        initial_order=['pie_chart', 'bar_chart', 'summary_plot', 'cat_count_bar', 'cat_sentiment_bar', 'cat_treemap' ,'summary_plot', 'cat_count_bar', 'cat_sentiment_bar', 'cat_treemap', 'rating_line', 'sentiment_line', 'monthly_plot', 'word_bar', 'word_treemap', 'sentiment_bar']
    )
    st.markdown('</div>', unsafe_allow_html=True)