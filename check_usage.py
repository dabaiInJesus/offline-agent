#!/usr/bin/env python3
"""
查看模型用量统计
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.usage_tracker import usage_tracker, UsageTracker
import argparse

def main():
    parser = argparse.ArgumentParser(description='查看模型用量统计')
    parser.add_argument('--days', '-d', type=int, default=1, help='查看最近 N 天 (默认 1)')
    parser.add_argument('--total', '-t', action='store_true', help='显示累计统计')
    parser.add_argument('--json', '-j', action='store_true', help='JSON 格式输出')
    
    args = parser.parse_args()
    
    if args.total:
        # 累计统计
        total = usage_tracker.get_total_usage()
        if args.json:
            import json
            print(json.dumps(total, indent=2, ensure_ascii=False))
        else:
            print(f"""
📊 累计用量统计
───────────────────────────────────────
总调用次数:   {total['total_calls']} 次
总 Prompt:   {total['total_prompt_tokens']} tokens
总 Completion: {total['total_completion_tokens']} tokens
总费用:      ${total['total_cost']:.6f}
成功率:      {(total['success_calls']/total['total_calls']*100) if total['total_calls'] > 0 else 0:.1f}%
""")
    else:
        # 每日统计
        recent = usage_tracker.get_recent_usage(args.days)
        
        if args.json:
            import json
            print(json.dumps([{
                'date': d.date,
                'total_calls': d.total_calls,
                'total_tokens': d.total_tokens,
                'total_cost': d.total_cost,
                'success_rate': f"{(d.success_calls/d.total_calls*100) if d.total_calls > 0 else 0:.1f}%"
            } for d in recent], indent=2, ensure_ascii=False))
        else:
            print("╔══════════════════════════════════════════════════════════════╗")
            print("║                    🤖 模型用量报告                              ║")
            print("╠══════════════════════════════════════════════════════════════╣")
            
            for d in recent:
                print(f"║  📅 {d.date}                                            ║")
                print(f"║  ──────────────────────────────────────────────────────────  ║")
                print(f"║  调用次数:     {d.total_calls:>6} 次                               ║")
                print(f"║  Prompt:      {d.total_prompt_tokens:>6} tokens                          ║")
                print(f"║  Completion:  {d.total_completion_tokens:>6} tokens                          ║")
                print(f"║  总计:        {d.total_tokens:>6} tokens                          ║")
                print(f"║  费用:        ${d.total_cost:>6.4f}                              ║")
                print(f"║  成功率:      {(d.success_calls/d.total_calls*100 if d.total_calls > 0 else 0):>6.1f}%                                ║")
                print(f"╠══════════════════════════════════════════════════════════════╣")
            
            print("╚══════════════════════════════════════════════════════════════╝")

if __name__ == '__main__':
    main()
