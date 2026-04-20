"""
使用 Conda 环境启动 Offline Agent
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

def run_in_conda(cmd, cwd=None, wait=True):
    """在 conda 环境中运行命令"""
    # 激活 conda 环境并执行命令
    conda_cmd = f"conda activate offline-agent && {cmd}"
    
    if wait:
        result = subprocess.run(
            conda_cmd,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True
        )
        return result
    else:
        # 在新窗口中运行
        return subprocess.Popen(
            f"start cmd /k \"{conda_cmd}\"",
            cwd=cwd,
            shell=True
        )

def check_conda_env():
    """检查 conda 环境"""
    result = subprocess.run(
        "conda env list",
        shell=True,
        capture_output=True,
        text=True
    )
    if "offline-agent" in result.stdout:
        print("✓ Conda 环境 'offline-agent' 已存在")
        return True
    else:
        print("✗ Conda 环境 'offline-agent' 不存在")
        print("  请先创建环境: conda create -n offline-agent python=3.10")
        return False

def check_dependencies():
    """检查依赖是否已安装"""
    result = run_in_conda("python -c \"import fastapi; print('OK')\"")
    if result.returncode == 0 and "OK" in result.stdout:
        print("✓ 依赖已安装")
        return True
    else:
        print("✗ 依赖未安装")
        return False

def install_dependencies():
    """安装依赖"""
    print("\n正在安装依赖...")
    print("这可能需要几分钟时间...")
    
    req_file = Path(__file__).parent / "requirements.txt"
    result = run_in_conda(f"pip install -r {req_file} -i https://pypi.tuna.tsinghua.edu.cn/simple")
    
    if result.returncode == 0:
        print("✓ 依赖安装完成")
        return True
    else:
        print(f"✗ 依赖安装失败")
        print(result.stderr)
        return False

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║         Offline Agent - Conda 环境启动器                     ║
╠══════════════════════════════════════════════════════════════╣
║  使用环境: offline-agent                                     ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 检查 conda 环境
    if not check_conda_env():
        return
    
    # 检查依赖
    if not check_dependencies():
        print("\n是否安装依赖? (y/n)")
        choice = input().strip().lower()
        if choice == 'y':
            if not install_dependencies():
                return
        else:
            print("取消启动")
            return
    
    # 检查 Node.js
    result = subprocess.run("node --version", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ Node.js: {result.stdout.strip()}")
        has_node = True
    else:
        print("✗ Node.js 未安装，前端服务无法启动")
        print("  请访问 https://nodejs.org/ 安装 Node.js 16+")
        has_node = False
    
    print("\n" + "="*60)
    print("启动服务...")
    print("="*60 + "\n")
    
    # 项目路径
    project_path = Path(__file__).parent
    backend_path = project_path / "webapp" / "backend" / "main.py"
    frontend_path = project_path / "webapp" / "frontend"
    
    # 启动后端
    if backend_path.exists():
        print(f"启动后端服务...")
        print(f"  路径: {backend_path}")
        backend_cmd = f"python {backend_path}"
        run_in_conda(backend_cmd, wait=False)
        print("✓ 后端服务已启动 (新窗口)")
        time.sleep(3)
    else:
        print(f"✗ 后端文件不存在: {backend_path}")
        return
    
    # 启动前端
    if has_node and frontend_path.exists():
        # 检查 node_modules
        if not (frontend_path / "node_modules").exists():
            print("\n首次运行，正在安装前端依赖...")
            print("这可能需要几分钟时间...")
            result = subprocess.run(
                f"cd {frontend_path} && npm install",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✓ 依赖安装完成")
            else:
                print(f"✗ 依赖安装失败")
                print(result.stderr)
                return
        
        print(f"\n启动前端服务...")
        print(f"  路径: {frontend_path}")
        subprocess.Popen(
            f"start cmd /k \"cd {frontend_path} && npm run serve\"",
            shell=True
        )
        print("✓ 前端服务已启动 (新窗口)")
        time.sleep(5)
    
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
