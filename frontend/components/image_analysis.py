import streamlit as st
import requests
from utils.api import API_BASE_URL
from PIL import Image
import io
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

def show_image_analysis():
    """
    显示图像分析页面
    """
    render_header("图像分析", "智能识别图像内容、场景与文字")

    with st.container():
        st.info("👋 欢迎使用图像分析！\n\n请上传您的图像文件以开始分析。")

        #st.markdown('<div class="css-card">', unsafe_allow_html=True)

        uploaded_file = st.file_uploader("上传图像文件", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            # 显示上传的图像
            image = Image.open(uploaded_file)
            st.image(image, caption="上传的图像", use_container_width=True)
            
            # 操作按钮区域
            st.markdown("### 选择分析模式")
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                analyze_click = st.button("🖼️ 图像分析 (对象/场景/分类)", type="primary", use_container_width=True)
            with col_btn2:
                ocr_click = st.button("📝 OCR文字提取", type="primary", use_container_width=True)
            
            target_task = None
            if analyze_click:
                target_task = "analysis"
            elif ocr_click:
                target_task = "ocr"

            if target_task:
                with st.spinner("正在进行智能分析..." if target_task == "analysis" else "正在提取文字..."):
                    try:
                        # 准备文件上传
                        files = {"image": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        
                        # 调用API (注意：分析API不在/api/v1下，而是在根路径下的/analyze)
                        base_url = API_BASE_URL.replace("/api/v1", "")
                        response = requests.post(f"{backend_url}/analyze/image", files=files)
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            st.success("处理完成！")
                            
                            if target_task == "analysis":
                                # 第一部分：视觉智能分析 (对象、场景、分类)
                                st.markdown("### 👁️ 视觉智能分析")
                                vis_col1, vis_col2 = st.columns(2)
                                
                                with vis_col1:
                                    # 对象识别
                                    st.markdown("#### 🎯 对象智能识别")
                                    objects = result.get("objects", [])
                                    if objects:
                                        for obj in objects:
                                            st.markdown(f"- **{obj['name']}** : `置信度 {obj['confidence']:.2f}`")
                                    else:
                                        st.info("未检测到显著对象")
                                    
                                    st.markdown("---")
                                    
                                    # 图像分类
                                    st.markdown("#### 🏷️ 图像分类标签")
                                    classification = result.get("classification", {})
                                    if classification:
                                        for cls, score in classification.items():
                                            st.write(f"**{cls}**")
                                            st.progress(score)
                                    else:
                                        st.info("无法分类")
                                        
                                with vis_col2:
                                    # 场景理解
                                    st.markdown("#### 🏞️ 场景自动理解")
                                    scene_text = result.get("scene", "无法识别场景")
                                    st.success(scene_text)
                                    
                            elif target_task == "ocr":
                                # 第二部分：OCR 文字提取 (独立区域)
                                st.markdown("### 📝 OCR文字提取结果")
                                
                                ocr_text = result.get("ocr_text", "")
                                if ocr_text and ocr_text != "无文字":
                                    st.text_area("提取内容", value=ocr_text, height=300)
                                    st.download_button(
                                        label="下载文本",
                                        data=ocr_text,
                                        file_name="ocr_result.txt",
                                        mime="text/plain"
                                    )
                                else:
                                    st.warning("当前图像未检测到包含文字，或文字无法识别。")
                                
                        else:
                            st.error(f"分析失败: {response.status_code} - {response.text}")
                            
                    except Exception as e:
                        st.error(f"请求错误: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
