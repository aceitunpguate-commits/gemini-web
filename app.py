import os
import io
from flask import Flask, request, render_template, session, redirect, url_for, render_template_string
import google.generativeai as genai
from PIL import Image

app = Flask(__name__)
app.secret_key = os.urandom(24)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ACCESS_PASSWORD = os.environ.get("PASSWORD", "123456")

# --- 核心修改：自动寻找可用模型 ---
model = None
model_name_used = "未知"

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # 1. 获取所有支持生成内容的模型列表
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print(f"你的账号可用模型列表: {all_models}")
        
        # 2. 智能筛选策略
        # 优先找 2.0, 其次找 1.5 flash, 再次找 1.5 pro, 最后随便拿一个
        target_model = None
        
        # 策略A: 找最新 2.0
        for m in all_models:
            if 'gemini-2.0' in m:
                target_model = m
                break
        
        # 策略B: 没找到2.0，找 1.5 flash (不带版本的通用名)
        if not target_model:
            for m in all_models:
                if 'gemini-1.5-flash' in m and '001' not in m and '002' not in m:
                    target_model = m
                    break
                    
        # 策略C: 实在不行，列表里第一个能用的就行
        if not target_model and all_models:
            target_model = all_models[0]
            
        if target_model:
            model = genai.GenerativeModel(target_model)
            model_name_used = target_model
            print(f"--> 最终已自动选择模型: {target_model}")
        else:
            print("错误：未找到任何可用模型")
            
    except Exception as e:
        print(f"Gemini 初始化严重错误: {e}")
else:
    print("未检测到 GEMINI_API_KEY")

@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    analysis_result = None
    
    if not model:
        return render_template('index.html', result=f"系统错误：无法加载 AI 模型。请检查后台日志里的‘可用模型列表’。")

    if request.method == 'POST':
        if 'file' not in request.files: return '请上传文件'
        file = request.files['file']
        if file.filename == '' or not file: return '未选择文件'
        
        try:
            img_bytes = file.read()
            img = Image.open(io.BytesIO(img_bytes))
            
            # 提示词
            response = model.generate_content(["请详细分析这张图片的内容。", img])
            
            # 在结果里偷偷告诉你用的哪个模型，方便你确认
            analysis_result = f"【当前使用模型: {model_name_used}】\n\n" + response.text
        except Exception as e:
            analysis_result = f"模型 {model_name_used} 调用失败: {str(e)}"

    return render_template('index.html', result=analysis_result)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error_msg = ""
    if request.method == 'POST':
        if request.form.get('password') == ACCESS_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error_msg = '密码错误'
            
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { display:flex; justify-content:center; align-items:center; height:100vh; margin:0; font-family:sans-serif; background:#f4f4f9; }
            form { background:white; padding:30px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.1); text-align:center; width: 300px; }
            input { padding:10px; margin:10px 0; width:100%; box-sizing:border-box; border: 1px solid #ccc; border-radius: 4px; }
            button { width:100%; padding:10px; background:#007BFF; color:white; border:none; border-radius:5px; cursor:pointer; font-size: 16px; }
            button:hover { background:#0056b3; }
        </style>
    </head>
    <body>
        <form method="post">
            <h3>🔒 请输入访问密码</h3>
            <input type="password" name="password" placeholder="在此输入密码" required>
            <button type="submit">进入</button>
            <p style="color:red; font-size:14px; margin-top: 10px;">{{ error_msg }}</p>
        </form>
    </body>
    </html>
    """
    return render_template_string(html, error_msg=error_msg)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
