"""
Web 应用启动脚本
同时启动 FastAPI 后端和 Vue 前端开发服务器
"""
import subprocess
import sys
import os
import time
import signal
from pathlib import Path

# 进程列表
processes = []

def signal_handler(sig, frame):
    """处理退出信号"""
    print("\n\n正在关闭服务...")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=5)
        except:
            p.kill()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_backend():
    """启动后端服务"""
    print("="*60)
    print("启动 FastAPI 后端服务...")
    print("="*60)
    
    backend_path = Path(__file__).parent / "backend" / "main.py"
    
    proc = subprocess.Popen(
        [sys.executable, str(backend_path)],
        cwd=str(Path(__file__).parent / "backend"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    processes.append(proc)
    
    # 等待后端启动
    print("等待后端启动...")
    time.sleep(3)
    print("后端服务已启动: http://localhost:8000")
    print()
    
    return proc

def start_frontend():
    """启动前端开发服务器"""
    print("="*60)
    print("启动 Vue 前端开发服务器...")
    print("="*60)
    
    frontend_path = Path(__file__).parent / "frontend"
    
    # 检查 node_modules 是否存在
    if not (frontend_path / "node_modules").exists():
        print("正在安装前端依赖...")
        subprocess.run(
            ["npm", "install"],
            cwd=str(frontend_path),
            check=True
        )
    
    proc = subprocess.Popen(
        ["npm", "run", "serve"],
        cwd=str(frontend_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    processes.append(proc)
    
    print("前端服务启动中...")
    time.sleep(5)
    print("前端服务已启动: http://localhost:8080")
    print()
    
    return proc

def print_output(proc, name):
    """打印进程输出"""
    try:
        for line in proc.stdout:
            print(f"[{name}] {line}", end='')
    except:
        pass

def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║              Offline Agent Web 启动器                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  技术栈:                                                     ║
║    • 后端: FastAPI (Python)                                  ║
║    • 前端: Vue 3 + TailwindCSS                               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # 启动后端
        backend_proc = start_backend()
        
        # 启动前端
        frontend_proc = start_frontend()
        
        print("="*60)
        print("所有服务已启动!")
        print("="*60)
        print()
        print("访问地址:")
        print("  • Web 界面: http://localhost:8080")
        print("  • API 文档: http://localhost:8000/docs")
        print("  • API 端点: http://localhost:8000")
        print()
        print("按 Ctrl+C 停止所有服务")
        print("="*60)
        print()
        
        # 等待进程结束
        while True:
            backend_status = backend_proc.poll()
            frontend_status = frontend_proc.poll()
            
            if backend_status is not None:
                print("后端服务已退出")
                break
            
            if frontend_status is not None:
                print("前端服务已退出")
                break
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f"启动失败: {e}")
        signal_handler(None, None)

if __name__ == "__main__":
    main()
