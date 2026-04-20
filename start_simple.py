"""
简化版启动脚本 - 快速启动 Web 服务
"""
import subprocess
import sys
import os
import time
import signal
from pathlib import Path

def signal_handler(sig, frame):
    print("\n正在关闭服务...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def check_command(cmd):
    """检查命令是否可用"""
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except:
        return False

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║              Offline Agent - 简化启动器                      ║
╠══════════════════════════════════════════════════════════════╣
║  检查环境...                                                 ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 检查 Python
    print(f"Python: {sys.executable}")
    print(f"Python 版本: {sys.version}")
    
    # 检查必要模块
    try:
        import fastapi
        print("✓ FastAPI 已安装")
    except ImportError:
        print("✗ FastAPI 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "colorama"])
        print("✓ FastAPI 安装完成")
    
    try:
        import uvicorn
        print("✓ Uvicorn 已安装")
    except ImportError:
        print("✗ Uvicorn 未安装")
        return
    
    # 检查 Node.js
    if check_command(["node", "--version"]):
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        print(f"✓ Node.js: {result.stdout.strip()}")
        has_node = True
    else:
        print("✗ Node.js 未安装，前端服务无法启动")
        print("  请访问 https://nodejs.org/ 安装 Node.js 16+")
        has_node = False
    
    print("\n" + "="*60)
    print("启动服务...")
    print("="*60 + "\n")
    
    # 启动后端
    backend_path = Path(__file__).parent / "webapp" / "backend" / "main.py"
    if backend_path.exists():
        print(f"启动后端: {backend_path}")
        backend_proc = subprocess.Popen(
            [sys.executable, str(backend_path)],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print("✓ 后端服务已启动 (新窗口)")
        time.sleep(3)
    else:
        print(f"✗ 后端文件不存在: {backend_path}")
        return
    
    # 启动前端
    if has_node:
        frontend_path = Path(__file__).parent / "webapp" / "frontend"
        if frontend_path.exists():
            # 检查 node_modules
            if not (frontend_path / "node_modules").exists():
                print("\n首次运行，正在安装前端依赖...")
                print("这可能需要几分钟时间...")
                result = subprocess.run(
                    ["npm", "install"],
                    cwd=str(frontend_path),
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print("✓ 依赖安装完成")
                else:
                    print(f"✗ 依赖安装失败: {result.stderr}")
                    return
            
            print(f"\n启动前端: {frontend_path}")
            frontend_proc = subprocess.Popen(
                ["npm", "run", "serve"],
                cwd=str(frontend_path),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            print("✓ 前端服务已启动 (新窗口)")
            time.sleep(5)
        else:
            print(f"✗ 前端目录不存在: {frontend_path}")
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    服务启动成功！                            ║
╠══════════════════════════════════════════════════════════════╣
║  访问地址：                                                  ║
║    • Web 界面:  http://localhost:8080                        ║
║    • API 文档:  http://localhost:8000/docs                   ║
║                                                              ║
║  按 Ctrl+C 停止此监控程序                                    ║
║  （后端和前端在独立窗口运行，可单独关闭）                    ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n监控程序已停止")
        print("注意：后端和前端服务仍在运行，请手动关闭它们的窗口")

if __name__ == "__main__":
    main()
