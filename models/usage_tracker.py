"""
用量统计模块 - 追踪模型调用次数和 Token 消耗
"""
from datetime import datetime, date
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import json
import os
import threading

@dataclass
class ModelUsage:
    """单次模型调用记录"""
    timestamp: datetime
    model: str
    provider: str  # 'ollama' or 'deepseek'
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0  # 费用（仅 DeepSeek）
    success: bool = True
    error: Optional[str] = None

@dataclass
class DailyUsage:
    """每日用量汇总"""
    date: str
    total_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    calls_by_model: Dict[str, int] = field(default_factory=dict)
    success_calls: int = 0
    failed_calls: int = 0

class UsageTracker:
    """
    模型用量追踪器
    支持 DeepSeek Token 统计和费用计算
    """
    
    # DeepSeek 价格（每千 Token）
    DEEPSEEK_PRICING = {
        "deepseek-chat": {"prompt": 0.001, "completion": 0.002},  # $0.001/1K prompt, $0.002/1K completion
        "deepseek-coder": {"prompt": 0.001, "completion": 0.002},
    }
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance
    
    def _init(self):
        """初始化"""
        self._records: List[ModelUsage] = []
        self._file_lock = threading.Lock()
        self._storage_file = "./logs/usage.json"
        
        # 确保日志目录存在
        os.makedirs("./logs", exist_ok=True)
        
        # 加载历史记录
        self._load()
    
    def _load(self):
        """加载历史记录"""
        if os.path.exists(self._storage_file):
            try:
                with open(self._storage_file, 'r') as f:
                    data = json.load(f)
                    self._records = [
                        ModelUsage(
                            timestamp=datetime.fromisoformat(r['timestamp']),
                            model=r['model'],
                            provider=r['provider'],
                            prompt_tokens=r.get('prompt_tokens', 0),
                            completion_tokens=r.get('completion_tokens', 0),
                            total_tokens=r.get('total_tokens', 0),
                            cost=r.get('cost', 0.0),
                            success=r.get('success', True),
                            error=r.get('error')
                        )
                        for r in data
                    ]
            except Exception as e:
                print(f"加载用量记录失败: {e}")
    
    def _save(self):
        """保存记录到文件"""
        with self._file_lock:
            try:
                data = [
                    {
                        'timestamp': r.timestamp.isoformat(),
                        'model': r.model,
                        'provider': r.provider,
                        'prompt_tokens': r.prompt_tokens,
                        'completion_tokens': r.completion_tokens,
                        'total_tokens': r.total_tokens,
                        'cost': r.cost,
                        'success': r.success,
                        'error': r.error
                    }
                    for r in self._records[-1000:]  # 只保留最近 1000 条
                ]
                with open(self._storage_file, 'w') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"保存用量记录失败: {e}")
    
    def record(
        self,
        model: str,
        provider: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        usage_data: dict = None,
        success: bool = True,
        error: Optional[str] = None
    ):
        """
        记录一次模型调用
        
        Args:
            model: 模型名称
            provider: 提供者 ('ollama' 或 'deepseek')
            prompt_tokens: 提示词 Token 数
            completion_tokens: 补全 Token 数
            total_tokens: 总 Token 数
            usage_data: 原始 usage 数据（用于解析 Token）
            success: 是否成功
            error: 错误信息
        """
        # 从 usage_data 解析 Token（DeepSeek API 返回格式）
        if usage_data and provider == 'deepseek':
            prompt_tokens = usage_data.get('prompt_tokens', prompt_tokens)
            completion_tokens = usage_data.get('completion_tokens', completion_tokens)
            total_tokens = usage_data.get('total_tokens', total_tokens)
        
        # 计算费用
        cost = 0.0
        if provider == 'deepseek' and total_tokens > 0:
            pricing = self.DEEPSEEK_PRICING.get(model, {"prompt": 0.001, "completion": 0.002})
            cost = (prompt_tokens / 1000) * pricing['prompt'] + \
                   (completion_tokens / 1000) * pricing['completion']
        
        record = ModelUsage(
            timestamp=datetime.now(),
            model=model,
            provider=provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            success=success,
            error=error
        )
        
        self._records.append(record)
        self._save()
    
    def get_today_usage(self) -> DailyUsage:
        """获取今日用量"""
        today = date.today().isoformat()
        return self._get_daily_usage(today)
    
    def get_usage_by_date(self, target_date: str) -> DailyUsage:
        """获取指定日期用量"""
        return self._get_daily_usage(target_date)
    
    def _get_daily_usage(self, target_date: str) -> DailyUsage:
        """获取指定日期的用量汇总"""
        daily = DailyUsage(date=target_date)
        
        for record in self._records:
            if record.timestamp.date().isoformat() != target_date:
                continue
            
            daily.total_calls += 1
            daily.total_prompt_tokens += record.prompt_tokens
            daily.total_completion_tokens += record.completion_tokens
            daily.total_tokens += record.total_tokens
            daily.total_cost += record.cost
            
            if record.model not in daily.calls_by_model:
                daily.calls_by_model[record.model] = 0
            daily.calls_by_model[record.model] += 1
            
            if record.success:
                daily.success_calls += 1
            else:
                daily.failed_calls += 1
        
        return daily
    
    def get_recent_usage(self, days: int = 7) -> List[DailyUsage]:
        """获取最近 N 天的用量"""
        from datetime import timedelta
        
        result = []
        today = date.today()
        
        for i in range(days):
            target_date = (today - timedelta(days=i)).isoformat()
            result.append(self._get_daily_usage(target_date))
        
        return result
    
    def get_total_usage(self) -> Dict:
        """获取总用量统计"""
        total = {
            'total_calls': len(self._records),
            'total_prompt_tokens': sum(r.prompt_tokens for r in self._records),
            'total_completion_tokens': sum(r.completion_tokens for r in self._records),
            'total_tokens': sum(r.total_tokens for r in self._records),
            'total_cost': sum(r.cost for r in self._records),
            'success_calls': sum(1 for r in self._records if r.success),
            'failed_calls': sum(1 for r in self._records if not r.success),
        }
        return total
    
    def format_usage_report(self) -> str:
        """格式化用量报告"""
        today = self.get_today_usage()
        total = self.get_total_usage()
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║                    🤖 模型用量报告                              ║
╠══════════════════════════════════════════════════════════════╣
║  📅 今日 ({today.date})                                        ║
║  ──────────────────────────────────────────────────────────  ║
║  调用次数:     {today.total_calls:>6} 次                               ║
║  Prompt:      {today.total_prompt_tokens:>6} tokens                          ║
║  Completion:  {today.total_completion_tokens:>6} tokens                          ║
║  总计:        {today.total_tokens:>6} tokens                          ║
║  费用:        ${today.total_cost:>6.4f}                              ║
║  成功率:      {(today.success_calls/today.total_calls*100 if today.total_calls > 0 else 0):>6.1f}%                                ║
╠══════════════════════════════════════════════════════════════╣
║  📊 累计统计                                               ║
║  ──────────────────────────────────────────────────────────  ║
║  总调用次数:   {total['total_calls']:>6} 次                               ║
║  总 Token:    {total['total_tokens']:>6} tokens                          ║
║  总费用:      ${total['total_cost']:>6.4f}                              ║
║  成功率:      {(total['success_calls']/total['total_calls']*100 if total['total_calls'] > 0 else 0):>6.1f}%                                ║
╚══════════════════════════════════════════════════════════════╝
"""
        return report


# 全局单例
usage_tracker = UsageTracker()


def record_usage(
    model: str,
    provider: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    usage_data: dict = None,
    success: bool = True,
    error: Optional[str] = None
):
    """便捷函数：记录用量"""
    usage_tracker.record(
        model=model,
        provider=provider,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        usage_data=usage_data,
        success=success,
        error=error
    )
