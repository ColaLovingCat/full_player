# 项目根目录/run_dev.py
import subprocess
import os
import sys
import time

def start_backend():
    print("🚀 启动后端 (FastAPI) ...")
    # 进入 backend 目录，使用 uvicorn 启动，并开启 --reload 热更新
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
        cwd=os.path.join(os.getcwd(), "backend")
    )
    return backend_process

def start_frontend():
    print("🎨 启动前端 (Vite) ...")
    # 根据操作系统选择不同的 npm 命令
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    
    # 进入 frontend 目录运行 npm run dev
    frontend_process = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=os.path.join(os.getcwd(), "frontend")
    )
    return frontend_process

if __name__ == "__main__":
    try:
        # 1. 启动后端
        backend_p = start_backend()
        
        # 稍微等一秒，让后端服务先起来
        time.sleep(1)
        
        # 2. 启动前端
        frontend_p = start_frontend()
        
        print("\n=======================================================")
        print("✨ 开发环境启动成功！")
        print("👉 请在浏览器中访问 Vite 的地址 (通常是 http://localhost:5173)")
        print("💡 后端 API 运行在 http://localhost:8000")
        print("🛑 按 Ctrl+C 停止所有服务")
        print("=======================================================\n")
        
        # 保持主进程运行，直到用户按下 Ctrl+C
        backend_p.wait()
        frontend_p.wait()

    except KeyboardInterrupt:
        print("\n正在停止服务...")
        backend_p.terminate()
        frontend_p.terminate()
        print("已完全退出。")
        sys.exit(0)