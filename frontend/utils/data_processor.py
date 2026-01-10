import pandas as pd
import re
import os
import sys
import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Add models path
current_dir = os.path.dirname(os.path.abspath(__file__))
# (frontend/utils) -> (frontend) -> (frontend/models)
models_dir = os.path.join(os.path.dirname(current_dir), 'models')
if models_dir not in sys.path:
    sys.path.append(models_dir)

try:
    from text.qwen_model import QwenModel
except ImportError:
    QwenModel = None

# 初始化 VADER 分析器
analyzer = SentimentIntensityAnalyzer()

def get_sentiment_score(text):
    """计算文本的情感极性（-1 到 1），使用 VADER"""
    if not text or not isinstance(text, str) or not text.strip():
        return 0.0
    return float(analyzer.polarity_scores(text)['compound'])

def extract_product_category(name):
    """从产品名称中提取物品类别（忽略品牌和修饰语）"""
    if not name:
        return "Unknown"
    
    name_lower = str(name).lower()
    
    # 定义关键词映射规则 (优先级从上到下)
    keywords = {
        'cable': 'Cable',
        'wire': 'Cable',
        'cord': 'Cable',
        'usb': 'USB Cable',
        'adapter': 'Adapter',
        'dongle': 'Adapter',
        'converter': 'Adapter',
        'charger': 'Charger',
        'power bank': 'Power Bank',
        'battery': 'Battery',
        'headphone': 'Headphones',
        'earphone': 'Headphones',
        'earbud': 'Headphones',
        'headset': 'Headphones',
        'airpods': 'Headphones',
        'tv': 'TV',
        'television': 'TV',
        'watch': 'Smartwatch',
        'smartwatch': 'Smartwatch',
        'band': 'Smart Band',
        'phone': 'Smartphone',
        'mobile': 'Smartphone',
        'tablet': 'Tablet',
        'ipad': 'Tablet',
        'tab': 'Tablet',
        'laptop': 'Laptop',
        'computer': 'Computer',
        'mouse': 'Mouse',
        'keyboard': 'Keyboard',
        'monitor': 'Monitor',
        'screen': 'Screen/Protector',
        'glass': 'Screen/Protector',
        'guard': 'Screen/Protector',
        'case': 'Case/Cover',
        'cover': 'Case/Cover',
        'speaker': 'Speaker',
        'camera': 'Camera',
        'lens': 'Camera Lens',
        'drive': 'Storage Drive',
        'card': 'Memory Card',
        'holder': 'Holder/Stand',
        'stand': 'Holder/Stand',
        'mount': 'Holder/Stand'
    }
    
    for key, category in keywords.items():
        if key in name_lower:
            return category
            
    return "Others"

def generate_response(sentiment_label, review_text, category):
    """为负面评论生成应对措施 (AI 驱动)"""
    if sentiment_label != '负面' or not review_text:
        return None
    
    # 尝试使用AI生成
    if QwenModel:
        try:
            # 优先尝试从 Streamlit session_state 获取 API Key
            api_key = None
            try:
                if st and hasattr(st, "session_state"):
                   api_key = st.session_state.get("dialog_api_key")
            except:
                pass
            
            # 如果 session 中没有，尝试从环境变量获取
            if not api_key:
                api_key = os.getenv("DASHSCOPE_API_KEY")

            if api_key:
                model = QwenModel(api_key=api_key)
                prompt = (
                    f"任务：针对一条用户关于产品'{category}'的负面评论，生成专业的应对措施。\n"
                    f"要求：\n1. 语气真诚、专业、具有同理心。\n2. 给出具体的解决方案（如退换货、补偿、技术指导等）。\n3. 给出内部改进建议。\n4. 字数控制在150字以内。\n\n"
                    f"评论内容：{review_text}"
                )
                
                response = model.predict(prompt)
                
                if response.get("status") == "success":
                    return f"🤖 【AI 智能建议】\n{response.get('text')}"
                else:
                    return f"⚠️ AI 生成失败: {response.get('text')}\n建议人工接入处理。"
        except Exception as e:
            return f"⚠️ AI 生成异常: {str(e)}"
            
    # 如果没有 AI 模型或 API Key，或者发生异常的后备方案
    return (
        "1. 【综合整改】建议人工深入分析评论内容，联系客户了解具体情况。\n"
        "2. 【客户关怀】主动致电不满意的客户，提供退换货服务或补偿，以挽回口碑。\n"
        "(提示：配置 API Key 后可启用 AI 智能生成具体的应对措施)"
    )

def process_uploaded_data(df):
    """处理上传的 DataFrame"""
    # 1. 确保列名存在
    required_cols = ['product_name', 'rating', 'review_content']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        # 尝试模糊匹配或重命名
        # 比如 'content' -> 'review_content', 'stars' -> 'rating'
        rename_map = {
            'content': 'review_content',
            'review': 'review_content',
            'text': 'review_content',
            'stars': 'rating',
            'score': 'rating',
            'product': 'product_name',
            'name': 'product_name'
        }
        df = df.rename(columns=rename_map)
        
        # 再次检查
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"上传的文件缺少必要列: {', '.join(missing_cols)}。请确保包含 product_name, rating, review_content (或类似名称)。")

    # 2. 填充缺失值
    df['review_content'] = df['review_content'].fillna('')
    df['product_name'] = df['product_name'].fillna('Unknown')
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0)

    # 3. 情感分析
    df['sentiment_score'] = df['review_content'].apply(get_sentiment_score)
    
    # 4. 情感标签
    def get_label(score):
        if score > 0.1: return '正面'
        elif score < -0.1: return '负面'
        else: return '中性'
    
    df['sentiment_label'] = df['sentiment_score'].apply(get_label)
    
    # 5. 产品分类
    df['product_category'] = df['product_name'].apply(extract_product_category)
    
    # 6. 生成应对方案
    df['solution'] = df.apply(
        lambda row: generate_response(row['sentiment_label'], row['review_content'], row['product_category']), 
        axis=1
    )
    
    return df
