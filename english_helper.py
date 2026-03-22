import streamlit as st
import pandas as pd
import requests
import re
import pdfplumber

# 设置页面标题
st.set_page_config(page_title="快速英语释义转换器", layout="wide")
st.title("📚 批量英语单词释义工具")

# 定义获取释义的函数 (使用免费 API)
def get_definition(word):
    # 1. 预处理：变小写并去除空格
    word = word.lower().strip()
    
    # 2. 备用方案：尝试多个免费 API 来源
    urls = [
        f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}",
        f"https://api.datamuse.com/words?sp={word}&d=definitions&max=1"
    ]
    
    try:
        # 先试第一个主流 API
        response = requests.get(urls[0], timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data[0]['meanings'][0]['definitions'][0]['definition']
        
        # 如果第一个失败了，自动尝试第二个备份 API (Datamuse)
        response_backup = requests.get(urls[1], timeout=5)
        if response_backup.status_code == 200:
            data_backup = response_backup.json()
            if data_backup and 'defs' in data_backup[0]:
                # 提取备份 API 的释义并去掉前缀
                raw_def = data_backup[0]['defs'][0]
                return raw_def.split('\t')[-1] 
                
        return "Definition not found (Tried backup)."
    except:
        return "Connection Error."

# 侧边栏：导入选项
st.sidebar.header("导入方式")
mode = st.sidebar.radio("选择导入类型", ["手动粘贴/文本", "PDF 文件"])

words_list = []

if mode == "手动粘贴/文本":
    raw_text = st.text_area("请粘贴包含单词的内容（程序会自动识别单词）:", height=200)
    # 使用正则表达式提取所有英语单词
    words_list = re.findall(r'\b[a-zA-Z]+\b', raw_text)

else:
    uploaded_file = st.file_uploader("上传 PDF 文件", type="pdf")
    if uploaded_file:
        with pdfplumber.open(uploaded_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
            words_list = re.findall(r'\b[a-zA-Z]+\b', text)

# 去重并过滤短词
words_list = list(set([w.lower() for w in words_list if len(w) > 2]))

if words_list:
    st.write(f"检测到 {len(words_list)} 个独特单词。")
    if st.button("开始批量生成释义"):
        results = []
        progress_bar = st.progress(0)
        
        for i, word in enumerate(words_list):
            definition = get_definition(word)
            results.append({"Word": word, "Definition (English)": definition})
            progress_bar.progress((i + 1) / len(words_list))
        
        # 显示结果表格
        df = pd.DataFrame(results)
        st.table(df)
        
        # 下载按钮
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("下载结果为 CSV", csv, "definitions.csv", "text/csv")