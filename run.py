"""
Offline Agent 项目启动器
一键启动所有服务
"""
import subprocess
import sys
import os
import time
import signal
import argparse
from pathlib import Path
from colorama import init, Fore, Style

# 初始化 colorama
init(autoreset=True)

# 进程列表
processes = []

def signal_handler(sig, frame):
    """处理退出信号"""
    print(f"\n{Fore.YELLOW}正在关闭所有服务...{Style.RESET_ALL}")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=5)
        except:
            p.kill()
    print(f"{Fore.GREEN}所有服务已停止{Style.RESET_ALL}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def print_banner():
    """打印启动横幅"""
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                    Offline Agent                             ║
║          本地 AI 智能体 - LangChain + LangGraph              ║
╠══════════════════════════════════════════════════════════════╣
║  功能：                                                      ║
║    • Ollama 本地大模型连接                                   ║
║    • 多数据库支持 (Oracle/MySQL/PostgreSQL/Hive)             ║
║    • 向量数据库 (FAISS/Chroma)                               ║
║    • 知识库 RAG 系统                                         ║
║    • 智能体 Agent (ReAct/Tool/Graph)                         ║
║    • 技能系统 AgentSkill                                     ║
║    • MCP 协议支持                                            ║
║    • Web 界面 (FastAPI + Vue + TailwindCSS)                  ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """)

def check_dependencies():
    """检查依赖"""
    print(f"{Fore.BLUE}检查依赖...{Style.RESET_ALL}")
    
    # 检查 Python 依赖
    try:
        import fastapi
        import uvicorn
        import langchain
        print(f"{Fore.GREEN}✓ Python 依赖已安装{Style.RESET_ALL}")
    except ImportError as e:
        print(f"{Fore.RED}✗ 缺少 Python 依赖: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}请运行: pip install -r requirements.txt{Style.RESET_ALL}")
        return False
    
    # 检查 Node.js
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True, shell=True)
        print(f"{Fore.GREEN}✓ Node.js 已安装{Style.RESET_ALL}")
    except:
        print(f"{Fore.RED}✗ 未安装 Node.js{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}请访问 https://nodejs.org/ 安装 Node.js 16+{Style.RESET_ALL}")
        return False
    
    return True

def start_backend():
    """启动后端服务"""
    print(f"\n{Fore.BLUE}启动 FastAPI 后端服务...{Style.RESET_ALL}")
    
    backend_path = Path(__file__).parent / "webapp" / "backend" / "main.py"
    
    proc = subprocess.Popen(
        [sys.executable, str(backend_path)],
        cwd=str(Path(__file__).parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
        encoding='utf-8',
        errors='replace'
    )
    processes.append(proc)

    # 实时输出
    def output_reader():
        try:
            for line in proc.stdout:
                print(f"{Fore.CYAN}[后端]{Style.RESET_ALL} {line}", end='')
        except Exception:
            pass
    
    import threading
    threading.Thread(target=output_reader, daemon=True).start()
    
    print(f"{Fore.GREEN}✓ 后端服务启动中...{Style.RESET_ALL}")
    time.sleep(3)
    return proc

def start_frontend():
    """启动前端服务"""
    print(f"\n{Fore.BLUE}启动 Vue 前端服务...{Style.RESET_ALL}")
    
    frontend_path = Path(__file__).parent / "webapp" / "frontend"
    
    # 检查是否需要安装依赖
    if not (frontend_path / "node_modules").exists():
        print(f"{Fore.YELLOW}首次运行，正在安装前端依赖...{Style.RESET_ALL}")
        result = subprocess.run(
            "npm install",
            cwd=str(frontend_path),
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode != 0:
            print(f"{Fore.RED}安装依赖失败: {result.stderr}{Style.RESET_ALL}")
            return None
        print(f"{Fore.GREEN}✓ 依赖安装完成{Style.RESET_ALL}")

    proc = subprocess.Popen(
        "npm run serve",
        cwd=str(frontend_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
        shell=True,
        encoding='utf-8',
        errors='replace'
    )
    processes.append(proc)

    # 实时输出
    def output_reader():
        try:
            for line in proc.stdout:
                print(f"{Fore.MAGENTA}[前端]{Style.RESET_ALL} {line}", end='')
        except Exception:
            pass
    
    import threading
    threading.Thread(target=output_reader, daemon=True).start()
    
    print(f"{Fore.GREEN}✓ 前端服务启动中...{Style.RESET_ALL}")
    time.sleep(5)
    return proc

def start_mcp_server():
    """启动 MCP 服务器"""
    print(f"\n{Fore.BLUE}启动 MCP 服务器...{Style.RESET_ALL}")
    
    mcp_path = Path(__file__).parent / "start_mcp_server.py"
    
    proc = subprocess.Popen(
        [sys.executable, str(mcp_path), "--port", "8001"],
        cwd=str(Path(__file__).parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
        encoding='utf-8',
        errors='replace'
    )
    processes.append(proc)

    # 实时输出
    def output_reader():
        try:
            for line in proc.stdout:
                print(f"{Fore.YELLOW}[MCP]{Style.RESET_ALL} {line}", end='')
        except Exception:
            pass
    
    import threading
    threading.Thread(target=output_reader, daemon=True).start()
    
    print(f"{Fore.GREEN}✓ MCP 服务器启动中...{Style.RESET_ALL}")
    time.sleep(2)
    return proc

def print_access_info():
    """打印访问信息"""
    print(f"""
{Fore.GREEN}{'='*60}{Style.RESET_ALL}
{Fore.GREEN}所有服务已启动！{Style.RESET_ALL}
{Fore.GREEN}{'='*60}{Style.RESET_ALL}

{Fore.CYAN}访问地址：{Style.RESET_ALL}
  • Web 界面:     {Fore.YELLOW}http://localhost:8080{Style.RESET_ALL}
  • API 文档:     {Fore.YELLOW}http://localhost:8000/docs{Style.RESET_ALL}
  • API 端点:     {Fore.YELLOW}http://localhost:8000{Style.RESET_ALL}
  • MCP 服务:     {Fore.YELLOW}http://localhost:8001/mcp{Style.RESET_ALL}

{Fore.CYAN}功能模块：{Style.RESET_ALL}
  • 控制台       - 系统概览和快速操作
  • 对话         - 与 AI 智能体对话
  • 数据库       - SQL 查询和数据管理
  • 知识库       - RAG 文档检索
  • 智能体       - Agent 管理
  • 技能         - 执行各种技能
  • 设置         - 系统配置

{Fore.CYAN}快捷键：{Style.RESET_ALL}
  • Ctrl+C       - 停止所有服务

{Fore.GREEN}{'='*60}{Style.RESET_ALL}
    """)

def main():
    parser = argparse.ArgumentParser(description="Offline Agent 启动器")
    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="仅启动后端"
    )
    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="仅启动前端"
    )
    parser.add_argument(
        "--with-mcp",
        action="store_true",
        help="同时启动 MCP 服务器"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="仅检查环境"
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # 仅检查环境
    if args.check:
        check_dependencies()
        return
    
    # 检查依赖
    if not check_dependencies():
        return
    
    try:
        # 启动服务
        if args.frontend_only:
            start_frontend()
        elif args.backend_only:
            start_backend()
        else:
            # 启动后端
            start_backend()
            
            # 启动前端
            start_frontend()
            
            # 可选：启动 MCP 服务器
            if args.with_mcp:
                start_mcp_server()
        
        # 打印访问信息
        print_access_info()
        
        # 保持运行
        while True:
            time.sleep(1)
            # 检查进程状态
            for proc in processes[:]:
                if proc.poll() is not None:
                    processes.remove(proc)
            if not processes:
                print(f"{Fore.RED}所有服务已退出{Style.RESET_ALL}")
                break
    
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f"{Fore.RED}启动失败: {e}{Style.RESET_ALL}")
        signal_handler(None, None)

if __name__ == "__main__":
    main()
