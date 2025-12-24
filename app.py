import os
import io
from flask import Flask, request, render_template
import google.generativeai as genai
from PIL import Image

app = Flask(__name__)

# 获取环境变量中的 API Key
# 在本地运行时，你可以临时把下面这行改成: api_key = "你的实际KEY"
# 但上传到 GitHub 前，请改回 os.environ.get...
api_key = os.environ.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

@app.route('/', methods=['GET', 'POST'])
def index():
    analysis_result = None
    
    # 如果没有配置 Key，提示错误
    if not model:
        return render_template('index.html', result="错误：未配置 GEMINI_API_KEY 环境变量。请在部署平台的设置中添加。")

    if request.method == 'POST':
        if 'file' not in request.files:
            return '没有文件'
        
        file = request.files['file']
        if file.filename == '':
            return '未选择文件'

        if file:
            try:
                # 读取图片流（不保存到硬盘）
                img_bytes = file.read()
                img = Image.open(io.BytesIO(img_bytes))
                
                # 调用 Gemini
                response = model.generate_content([
                    "请详细描述这张图片的内容，用中文回答。如果是外语截图，请帮忙翻译。", 
                    img
                ])
                analysis_result = response.text
                
            except Exception as e:
                analysis_result = f"发生错误: {str(e)}"

    return render_template('index.html', result=analysis_result)

if __name__ == '__main__':
    app.run(debug=True)