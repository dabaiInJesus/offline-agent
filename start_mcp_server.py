"""
MCP 服务器启动脚本
"""
import argparse
import sys
from custom_mcp_server import create_full_featured_mcp_server, CustomMCPServer


def main():
    parser = argparse.ArgumentParser(description="启动自定义 MCP 服务器")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="服务器主机地址 (默认: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="服务器端口 (默认: 8000)"
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="启动简化版服务器（不包含数据库和知识库）"
    )
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              自定义 MCP 服务器                               ║
║                                                              ║
║  地址: http://{args.host}:{args.port:<5}                     ║
║  MCP 端点: http://{args.host}:{args.port}/mcp                ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    if args.simple:
        # 启动简化版服务器
        custom_server = CustomMCPServer()
        server = custom_server.get_server()
    else:
        # 启动完整功能服务器
        print("正在初始化完整功能服务器...")
        server = create_full_featured_mcp_server()
    
    # 显示工具列表
    tools = server.list_tools()
    print(f"\n已加载 {len(tools)} 个工具:")
    for i, tool in enumerate(tools, 1):
        print(f"  {i}. {tool['name']}")
    
    resources = server.list_resources()
    print(f"\n已加载 {len(resources)} 个资源:")
    for i, resource in enumerate(resources, 1):
        print(f"  {i}. {resource['uri']}")
    
    print(f"\n{'='*60}")
    print("服务器启动中... 按 Ctrl+C 停止")
    print(f"{'='*60}\n")
    
    try:
        # 启动 HTTP 服务
        if args.simple:
            custom_server.run_http(host=args.host, port=args.port)
        else:
            from mcp.server import FastAPIMCPServer
            fastapi_server = FastAPIMCPServer(server)
            fastapi_server.run(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
        sys.exit(0)


if __name__ == "__main__":
    main()
