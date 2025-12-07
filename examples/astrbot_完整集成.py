# encoding:utf-8
"""
astrbot 完整集成示例
使用增强版插件，支持分页浏览和选择转存
"""

from pansearch_enhanced import PanSearchPluginEnhanced
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ 全局插件实例 ============

plugin = None

def init_plugin(config_path: str = "config.json"):
    """
    初始化插件（在机器人启动时调用）
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        bool: 初始化是否成功
    """
    global plugin
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        plugin = PanSearchPluginEnhanced(config)
        logger.info("✅ 增强版网盘搜索插件初始化成功")
        return True
    except Exception as e:
        logger.error(f"❌ 插件初始化失败: {e}")
        return False


def handle_qq_message(message: str, user_id: str, group_id: str = None) -> str:
    """
    处理 QQ 消息（主入口函数）
    
    Args:
        message: 用户消息内容
        user_id: 用户ID（必填，用于会话管理）
        group_id: 群ID（可选，群聊时使用）
        
    Returns:
        str: 回复内容，如果不需要处理返回 None
    """
    if not plugin:
        return "❌ 插件未初始化，请检查配置"
    
    # 构建会话ID
    # 如果是群聊，使用 group_id + user_id 组合，确保每个用户在群里有独立会话
    # 如果是私聊，直接使用 user_id
    session_id = f"{group_id}_{user_id}" if group_id else user_id
    
    try:
        # 调用插件处理消息
        reply = plugin.handle_message(message, session_id)
        return reply
    except Exception as e:
        logger.error(f"消息处理异常: {e}")
        return f"❌ 处理失败: {str(e)}"


# ============ astrbot 集成示例 ============

def astrbot_integration():
    """
    astrbot 集成示例
    根据你的实际框架调整
    """
    
    # 1. 初始化插件（在机器人启动时）
    if not init_plugin():
        logger.error("插件初始化失败")
        return
    
    # 2. 注册消息处理器（根据你的 astrbot 框架调整）
    # 以下是几种常见的集成方式：
    
    # 方式 1: 基于装饰器
    # @bot.on_message()
    # async def on_message(event):
    #     message = event.message
    #     user_id = str(event.user_id)
    #     group_id = str(event.group_id) if hasattr(event, 'group_id') else None
    #     
    #     reply = handle_qq_message(message, user_id, group_id)
    #     if reply:
    #         await event.reply(reply)
    
    # 方式 2: 基于回调函数
    # def message_handler(message, user_id, group_id=None):
    #     reply = handle_qq_message(message, user_id, group_id)
    #     return reply
    # 
    # bot.register_message_handler(message_handler)
    
    # 方式 3: 基于事件循环
    # while True:
    #     message, user_id, group_id = bot.get_message()
    #     reply = handle_qq_message(message, user_id, group_id)
    #     if reply:
    #         bot.send_message(reply, user_id, group_id)
    
    print("astrbot 集成代码已准备")
    print("请根据你的 astrbot 框架调整消息处理部分")


# ============ 测试代码 ============

if __name__ == "__main__":
    # 初始化插件
    if not init_plugin():
        print("插件初始化失败")
        exit(1)
    
    print("=" * 60)
    print("astrbot 完整集成测试")
    print("=" * 60)
    
    # 模拟用户交互流程
    user_id = "test_user_123"
    
    test_cases = [
        ("搜仙逆", "搜索资源"),
        ("下一页", "翻页"),
        ("第1个", "选择并转存"),
    ]
    
    for message, description in test_cases:
        print(f"\n{'='*60}")
        print(f"【{description}】用户发送: {message}")
        print(f"{'='*60}")
        
        reply = handle_qq_message(message, user_id)
        if reply:
            print(f"\n机器人回复:\n{reply}")
        else:
            print("\n不处理此消息")
        
        print()

