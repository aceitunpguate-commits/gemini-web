import os
import io
from flask import Flask, request, render_template, session, redirect, url_for
import google.generativeai as genai
from PIL import Image

app = Flask(__name__)
# 必须设置 secret_key 才能使用 session (用于记住登录状态)
app.secret_key = os.urandom(24)

# 1. 从环境变量获取配置
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# 如果环境变量里没有设置 PASSWORD，默认密码设为 123456
ACCESS_PASSWORD = os.environ.get("PASSWORD", "123456")

# 配置 Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None


@app.route('/', methods=['GET', 'POST'])
def index():
    # 2. 检查登录状态
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    analysis_result = None

    if not model:
        return render_template('index.html', result="错误：未配置 GEMINI_API_KEY，请在 Zeabur 环境变量中添加。")

    if request.method == 'POST':
        if 'file' not in request.files: return '无文件'
        file = request.files['file']
        if file.filename == '' or not file: return '未选择文件'

        try:
            img_bytes = file.read()
            img = Image.open(io.BytesIO(img_bytes))
            # 这里的提示词
            response = model.generate_content(["请详细分析这张图片的内容。", img])
            analysis_result = response.text
        except Exception as e:
            analysis_result = f"错误: {str(e)}"

    return render_template('index.html', result=analysis_result)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        # 3. 比对用户输入的密码 和 环境变量里的密码
        if request.form.get('password') == ACCESS_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = '密码错误'

    return '''
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { display:flex; justify-content:center; align-items:center; height:100vh; margin:0; font-family:sans-serif; background:#f4f4f9; }
            form { background:white; padding:30px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.1); text-align:center; }
            input { padding:10px; margin:10px 0; width:100%; box-sizing:border-box; }
            button { width:100%; padding:10px; background:#007BFF; color:white; border:none; border-radius:5px; cursor:pointer; }
        </style>
    </head>
    <body>
        <form method="post">
            <h3>🔒 请输入访问密码</h3>
            <input type="password" name="password" placeholder="请输入密码" required>
            <button type="submit">进入</button>
            <p style="color:red; font-size:14px;">%s</p>
        </form>
    </body>
    </html>
    ''' % (error if error else "")


if __name__ == '__main__':
    # 4. 让 Flask 监听环境变量提供的端口 (Zeabur 必备)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)