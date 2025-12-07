# encoding:utf-8
"""
astrbot 网盘搜索转存插件
直接集成到 astrbot 中使用
"""

import json
from pansearch_enhanced import PanSearchPluginEnhanced


class AstrbotPanSearchPlugin:
    """astrbot 网盘搜索转存插件"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化插件
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 创建插件实例
        self.plugin = PanSearchPluginEnhanced(config)
    
    def handle_message(self, message: str, user_id: str) -> str:
        """
        处理用户消息
        
        Args:
            message: 用户消息
            user_id: 用户ID
            
        Returns:
            回复消息
        """
        return self.plugin.handle_message(message, user_id)


# 使用示例（集成到 astrbot）
"""
# 在 astrbot 的插件系统中使用：

from astrbot_plugin import AstrbotPanSearchPlugin

# 初始化插件
pansearch_plugin = AstrbotPanSearchPlugin("config.json")

# 在消息处理函数中调用
def on_message(message, user_id):
    # 检查是否是搜索命令
    if message.startswith("搜") or message.startswith("求"):
        return pansearch_plugin.handle_message(message, user_id)
    
    # 检查是否是翻页或选择命令
    if message in ["下一页", "上一页"] or message.isdigit() or "第" in message and "个" in message:
        return pansearch_plugin.handle_message(message, user_id)
    
    return None  # 不处理其他消息
"""
