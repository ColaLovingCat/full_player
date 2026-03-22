# backend/desktop.py
import webview
import threading
import uvicorn
import sys
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from main import app  # 导入你 main.py 里的 app 实例

# 1. 解决 PyInstaller 打包后的路径问题
def get_resource_path(relative_path):
    """ 获取静态资源的绝对路径，兼容开发环境和 PyInstaller 打包环境 """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

# 2. 挂载 Vue 编译后的前端静态文件
frontend_dist_path = get_resource_path("dist")

if os.path.exists(frontend_dist_path):
    # 挂载 assets 文件夹 (js/css/图片)
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist_path, "assets")), name="assets")
    
    # 将根目录指向 Vue 的 index.html
    @app.get("/")
    async def serve_vue_app():
        return FileResponse(os.path.join(frontend_dist_path, "index.html"))

# 3. 启动 FastAPI 服务的线程函数
def start_server():
    # 禁用 uvloop，防止在部分 Windows 系统上 PyInstaller 打包后报错
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if __name__ == '__main__':
    # 4. 在后台线程中启动 FastAPI
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 5. 创建并启动桌面窗口，指向本地服务
    webview.create_window(
        title='我的 3D 音乐空间', 
        url='http://127.0.0.1:8000', 
        width=1280, 
        height=800,
        resizable=True,
        frameless=False, # 如果你想要无边框沉浸式窗口，可以设为 True
        background_color='#000000'
    )
    
    webview.start()