import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
    # Fallback
    def render_header(title, subtitle=None): st.title(title)

def show_home(backend_url=None):
    """
    显示首页内容
    """
    render_header("多模态反馈分析平台", "综合性用户反馈智能分析系统")
    
    # 平台介绍
    with st.container():
        st.markdown("""
        <div class="css-card">
            <h3 style="font-size: 30px;">👋 欢迎使用</h3>
            <p style="font-size: 18px; line-height: 1.6;">多模态反馈分析平台是一个综合性的用户反馈分析系统，能够处理和分析文本、图像和音频等多种类型的用户反馈。
            通过先进的AI技术，平台可以自动识别反馈中的情感倾向、提取关键信息，并提供直观的数据可视化结果。</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 功能特点
    st.markdown("<h3 style='font-size: 30px; margin-top: 30px; margin-bottom: 20px;'>核心功能</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="css-card" style="height: 100%;">
            <h4 style="font-size: 22px;">文本分析</h4>
            <ul style="font-size: 18px; line-height: 1.6;">
                <li>情感倾向分析</li>
                <li>关键词智能提取</li>
                <li>主题自动分类</li>
                <li>语义深度理解</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="css-card" style="height: 100%;">
            <h4 style="font-size: 22px;">图像分析</h4>
            <ul style="font-size: 18px; line-height: 1.6;">
                <li>对象智能识别</li>
                <li>场景自动理解</li>
                <li>OCR文字提取</li>
                <li>图像分类标签</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="css-card" style="height: 100%;">
            <h4 style="font-size: 22px;">🤖 AI 智能助手</h4>
            <ul style="font-size: 18px; line-height: 1.6;">
                <li>智能对话交互</li>
                <li>深度数据洞察</li>
                <li>分析建议生成</li>
                <li>多模态辅助分析</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    
    # 使用指南
    st.markdown("<h2 style='font-size: 30px; margin-top: 40px; margin-bottom: 20px;'>使用指南</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="font-size: 20px; line-height: 1.8;">
    </div>
    <div class="css-card" style="height: 100%;">
        <ul style="font-size: 18px; line-height: 1.6;">
            <li>上传或输入文本数据，进行情感倾向分析、关键词提取和主题分类。</li>
            <li>上传图像文件，识别图像内容、提取文字信息 (OCR) 及场景分析。</li>
            <li>与基于通义千问大模型的智能助手对话，获取深度数据洞察和分析建议。</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    

    

    
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #6c757d; font-size: 1.2rem;'>
        邮箱: feedback@example.com ｜ 电话: 400-123-4567<br>
        网站: www.example.com
    </div>
    """, unsafe_allow_html=True)