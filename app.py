import streamlit as st
import requests
import json
import base64

# --- 配置区 (请替换你的 Key) ---
API_KEY = "sk-zyuuqfzvqxcuddztkmirtgkwunabvuqlpcepchpbcxglcocu"  # 这里填你的硅基流动 Key
BASE_URL = "https://api.siliconflow.cn/v1"

# 设置网页标题和布局
st.set_page_config(page_title="My AI Studio", layout="wide", page_icon="🎨")

# 侧边栏
with st.sidebar:
    st.title("🎨 个人绘图工作台")
    st.markdown("集成 **DeepSeek + Qwen-VL + Flux**")
    st.info("无需 Dify，直接调用硅基流动 API")

# --- 核心函数 ---

def encode_image(uploaded_file):
    """将上传的图片转为 Base64"""
    if uploaded_file is None:
        return None
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

def analyze_image(image_base64, user_prompt):
    """1. 用 Qwen-VL 看懂图片并结合用户需求"""
    url = f"{BASE_URL}/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    # 构造视觉模型的输入
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": f"你是一个视觉分析专家。用户上传了一张图片，并说：'{user_prompt}'。请详细描述这张图片的内容、构图、光影，然后结合用户的要求，写一段用于 AI 绘图的英文 Prompt。只输出英文 Prompt，不要废话。"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
        ]
    }]
    
    data = {
        "model": "Qwen/Qwen2-VL-72B-Instruct", # 使用强大的视觉模型
        "messages": messages,
        "max_tokens": 500
    }
    
    with st.spinner("👀 AI 正在观察你的图片..."):
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            st.error(f"识图失败: {response.text}")
            return None

def optimize_prompt(user_text):
    """2. (纯文字模式) 用 DeepSeek 优化提示词"""
    url = f"{BASE_URL}/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    data = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [{"role": "user", "content": f"你是一个绘图提示词大师。将用户这段话改写为 Flux 能够理解的高质量英文 Prompt，包含 detailed, 8k, photorealistic 等关键词：'{user_text}'。只输出英文。"}],
    }
    
    with st.spinner("🧠 DeepSeek 正在思考构图..."):
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return None

def generate_image(prompt):
    """3. 用 Flux 生成图片"""
    url = f"{BASE_URL}/images/generations"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    data = {
        "model": "black-forest-labs/FLUX.1-schnell",
        "prompt": prompt,
        "image_size": "1024x1024"
    }
    
    with st.spinner("🎨 Flux 正在挥毫泼墨..."):
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            try:
                return response.json()['images'][0]['url']
            except:
                st.error("解析图片地址失败")
                return None
        else:
            st.error(f"生图失败: {response.text}")
            return None

# --- 网页主界面 ---

st.header("✨ AI 视觉绘图助手")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 输入与上传")
    uploaded_file = st.file_uploader("上传参考图（可选）", type=['jpg', 'png', 'jpeg'])
    user_input = st.text_area("你想画什么？或者对上面的图怎么改？", height=100, placeholder="例如：帮我画一个写实的玻璃杯，或者：把上面这张图的背景换成雪山")
    
    generate_btn = st.button("开始生成 ✨", type="primary")

with col2:
    st.subheader("2. 结果展示")
    if generate_btn and user_input:
        final_prompt = ""
        
        # 分支逻辑：有图 vs 没图
        if uploaded_file:
            # 模式 A: 图生图/改图 (Qwen-VL -> Flux)
            img_b64 = encode_image(uploaded_file)
            final_prompt = analyze_image(img_b64, user_input)
        else:
            # 模式 B: 文生图 (DeepSeek -> Flux)
            final_prompt = optimize_prompt(user_input)
            
        if final_prompt:
            st.success("优化后的指令: " + final_prompt[:100] + "...")
            image_url = generate_image(final_prompt)
            
            if image_url:
                st.image(image_url, caption="AI 生成结果", use_container_width=True)
                st.markdown(f"[下载图片]({image_url})")
    elif generate_btn:
        st.warning("请输入描述文字！")