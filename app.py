import os
import io
from flask import Flask, request, render_template, session, redirect, url_for, render_template_string
import google.generativeai as genai
from PIL import Image

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 1. 获取配置
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ACCESS_PASSWORD = os.environ.get("PASSWORD", "123456")

# 配置 Gemini
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"Gemini Warning: {e}")
        model = None
else:
    model = None

@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    analysis_result = None
    
    if not model:
        return render_template('index.html', result="错误：未配置 API Key 或库版本过旧。")

    if request.method == 'POST':
        if 'file' not in request.files: return '无文件'
        file = request.files['file']
        if file.filename == '' or not file: return '未选择文件'
        
        try:
            img_bytes = file.read()
            img = Image.open(io.BytesIO(img_bytes))
            response = model.generate_content(["请详细分析这张图片的内容。", img])
            analysis_result = response.text
        except Exception as e:
            analysis_result = f"发生错误: {str(e)}"

    return render_template('index.html', result=analysis_result)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error_msg = ""
    if request.method == 'POST':
        if request.form.get('password') == ACCESS_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error_msg = '密码错误，请重试'
            
    # 使用 f-string 避免百分号冲突，这是最安全的写法
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ display:flex; justify-content:center; align-items:center; height:100vh; margin:0; font-family:sans-serif; background:#f4f4f9; }}
            form {{ background:white; padding:30px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.1); text-align:center; width: 300px; }}
            input {{ padding:10px; margin:10px 0; width:100%; box-sizing:border-box; border: 1px solid #ccc; border-radius: 4px; }}
            button {{ width:100%; padding:10px; background:#007BFF; color:white; border:none; border-radius:5px; cursor:pointer; font-size: 16px; }}
            button:hover {{ background:#0056b3; }}
        </style>
    </head>
    <body>
        <form method="post">
            <h3>🔒 请输入访问密码</h3>
            <input type="password" name="password" placeholder="在此输入密码" required>
            <button type="submit">进入</button>
            <p style="color:red; font-size:14px; margin-top: 10px;">{error_msg}</p>
        </form>
    </body>
    </html>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
