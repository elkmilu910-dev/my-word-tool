import streamlit as st
import pandas as pd
import requests
import re
import pdfplumber
import time

# 1. 页面基本配置
st.set_page_config(page_title="批量英语释义工具", layout="wide")
st.title("📚 快速英语单词释义转换器")
st.markdown("---")

# 2. 定义查词函数（这是最核心的“大脑”）
def get_definition(word):
    word = word.lower().strip()
    
    # 过滤非单词字符（比如数字、标点符号）
    if not word.isalpha() or len(word) < 2:
        return "N/A (Not a word)"

    # 两个免费词典 API 来源
    url_a = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    url_b = f"https://api.datamuse.com/words?sp={word}&d=definitions&max=1"

    try:
        # 【关键】每查一个词歇 0.5 秒，避免被服务器当作机器人封锁
        time.sleep(0.5) 
        
        # 尝试第一个 API
        resp = requests.get(url_a, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data[0]['meanings'][0]['definitions'][0]['definition']
        
        # 如果第一个不行，尝试第二个 API
        resp_b = requests.get(url_b, timeout=5)
        if resp_b.status_code == 200:
            data_b = resp_b.json()
            if data_b and 'defs' in data_b[0]:
                # 提取释义并简单处理格式
                return data_b[0]['defs'][0].split('\t')[-1]

        return "Definition not found. (Check spelling)"
    except:
        return "Service busy. (Connection error)"

# 3. 侧边栏设置
st.sidebar.header("导入设置")
mode = st.sidebar.radio("选择导入方式", ["批量粘贴文字", "上传 PDF 文件"])

words_list = []

# 4. 处理数据输入
if mode == "批量粘贴文字":
    raw_text = st.text_area("请直接粘贴英文内容:", height=250, placeholder="程序会自动识别文中的单词...")
    words_list = re.findall(r'\b[a-zA-Z]+\b', raw_text)

else:
    uploaded_file = st.file_uploader("上传 PDF", type="pdf")
    if uploaded_file:
        with pdfplumber.open(uploaded_file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            words_list = re.findall(r'\b[a-zA-Z]+\b', text)

# 5. 处理识别出的单词
# 去重并统一转为小写
words_list = sorted(list(set([w.lower() for w in words_list if len(w) > 2])))

if words_list:
    st.info(f" 系统已自动识别出 {len(words_list)} 个独特单词。")
    
    if st.button(" 点击开始：批量生成英文释义"):
        results = []
        # 创建进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, word in enumerate(words_list):
            status_text.text(f"正在查询第 {i+1}/{len(words_list)} 个单词: {word}")
            definition = get_definition(word)
            results.append({"单词 (Word)": word, "英文释义 (Definition)": definition})
            # 更新进度条
            progress_bar.progress((i + 1) / len(words_list))
        
        status_text.text("✅ 查询完成！")
        
        # 6. 显示结果表格
        df = pd.DataFrame(results)
        st.table(df)
        
        # 7. 导出功能
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 下载结果表格 (CSV)", csv, "word_definitions.csv", "text/csv")