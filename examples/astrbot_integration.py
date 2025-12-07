# encoding:utf-8
"""
astrbot 集成示例
网盘搜索转存插件
"""

import json
import logging
from pansearch import PanSearchPlugin

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局插件实例
plugin = None


def init_plugin(config_path: str = "config.json"):
    """
    初始化插件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        bool: 初始化是否成功
    """
    global plugin
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        plugin = PanSearchPlugin(config)
        logger.info("网盘搜索转存插件初始化成功")
        return True
    except Exception as e:
        logger.error(f"插件初始化失败: {str(e)}")
        return False


def handle_message(message: str, user_id: str = None) -> str:
    """
    处理消息（主入口函数）
    
    Args:
        message: 用户消息内容
        user_id: 用户ID（可选）
        
    Returns:
        str: 回复内容，如果不需要处理返回 None
    """
    if not plugin:
        return "❌ 插件未初始化，请检查配置"
    
    # 检测搜索命令（可以根据需要修改触发词）
    search_triggers = ["/搜索", "/search", "搜索", "找资源", "/找"]
    
    keyword = None
    for trigger in search_triggers:
        if message.startswith(trigger):
            keyword = message.replace(trigger, "").strip()
            break
    
    # 如果没有触发词，检查是否是纯文本（可能是直接搜索）
    # 可以根据需要启用这个功能
    # if not keyword and len(message.strip()) > 2:
    #     keyword = message.strip()
    
    if keyword:
        try:
            result = plugin.search_and_transfer(keyword)
            return result
        except Exception as e:
            logger.error(f"处理搜索请求失败: {str(e)}")
            return f"❌ 处理失败: {str(e)}"
    
    return None  # 不处理此消息


# ============ astrbot 集成示例 ============

def astrbot_integration_example():
    """
    astrbot 集成示例
    根据你的 astrbot 框架调整此代码
    """
    
    # 1. 在机器人启动时初始化插件
    if not init_plugin():
        logger.error("插件初始化失败，请检查配置")
        return
    
    # 2. 注册消息处理器（根据你的 astrbot 框架调整）
    # 示例代码（需要根据实际框架调整）：
    
    # from astrbot import Bot, Message
    
    # bot = Bot()
    
    # @bot.on_message()
    # async def on_message(msg: Message):
    #     # 处理消息
    #     reply = handle_message(msg.content, msg.user_id)
    #     if reply:
    #         await msg.reply(reply)
    
    # bot.run()
    
    print("astrbot 集成示例代码已准备")
    print("请根据你的 astrbot 框架调整消息处理部分")


# ============ 通用消息处理函数 ============

def process_qq_message(message: str, user_id: str = None, group_id: str = None) -> str:
    """
    通用的 QQ 消息处理函数
    可以在任何框架中使用
    
    Args:
        message: 消息内容
        user_id: 用户ID
        group_id: 群ID（可选）
        
    Returns:
        str: 回复内容，如果不需要处理返回 None
    """
    return handle_message(message, user_id)


# ============ 测试代码 ============

if __name__ == "__main__":
    # 初始化插件
    if not init_plugin():
        print("插件初始化失败")
        exit(1)
    
    # 测试消息处理
    test_messages = [
        "/搜索 仙逆",
        "搜索 速度与激情",
        "找资源 复仇者联盟",
        "普通消息"  # 这个不会被处理
    ]
    
    print("=" * 60)
    print("测试消息处理")
    print("=" * 60)
    
    for msg in test_messages:
        print(f"\n用户消息: {msg}")
        result = handle_message(msg)
        if result:
            print(f"机器人回复:\n{result}")
        else:
            print("不处理此消息")
        print("-" * 60)

