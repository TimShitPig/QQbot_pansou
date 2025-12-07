# encoding:utf-8
"""
astrbot 集成示例
根据你的 astrbot 框架调整此代码
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
    """初始化插件"""
    global plugin
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        plugin = PanSearchPlugin(config)
        logger.info("插件初始化成功")
        return True
    except Exception as e:
        logger.error(f"插件初始化失败: {str(e)}")
        return False


def handle_qq_message(message: str, user_id: str = None) -> str:
    """
    处理 QQ 消息
    
    Args:
        message: 用户消息内容
        user_id: 用户ID（可选）
        
    Returns:
        回复内容，如果不需要回复返回 None
    """
    if not plugin:
        return "❌ 插件未初始化，请检查配置"
    
    # 检测搜索命令（根据你的需求修改触发词）
    search_triggers = ["/搜索", "/search", "搜索", "找资源"]
    
    keyword = None
    for trigger in search_triggers:
        if message.startswith(trigger):
            keyword = message.replace(trigger, "").strip()
            break
    
    # 如果没有触发词，检查是否是纯文本（可能是直接搜索）
    if not keyword and len(message.strip()) > 0:
        # 可以根据需要决定是否直接作为关键词
        # keyword = message.strip()
        pass
    
    if keyword:
        try:
            result = plugin.search_and_transfer(keyword)
            return result
        except Exception as e:
            logger.error(f"处理搜索请求失败: {str(e)}")
            return f"❌ 处理失败: {str(e)}"
    
    return None  # 不处理此消息


# ============ 不同框架的集成示例 ============

# 示例1: 基于 NoneBot2 的集成
def nonebot2_integration():
    """
    NoneBot2 集成示例
    需要安装: pip install nonebot2
    """
    try:
        from nonebot import on_command
        from nonebot.adapters.onebot.v11 import MessageEvent
        
        # 初始化插件
        init_plugin()
        
        # 注册命令处理器
        search_cmd = on_command("搜索", aliases={"search", "找资源"})
        
        @search_cmd.handle()
        async def handle_search(event: MessageEvent):
            keyword = str(event.message).strip()
            if keyword:
                result = plugin.search_and_transfer(keyword)
                await search_cmd.finish(result)
            else:
                await search_cmd.finish("请输入搜索关键词，例如：/搜索 速度与激情")
                
    except ImportError:
        logger.warning("NoneBot2 未安装，跳过集成示例")


# 示例2: 基于 go-cqhttp 的集成
def gocqhttp_integration():
    """
    go-cqhttp HTTP API 集成示例
    """
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    
    # 初始化插件
    if not init_plugin():
        logger.error("插件初始化失败")
        return
    
    @app.route('/message', methods=['POST'])
    def handle_message():
        """处理消息"""
        data = request.json
        message = data.get('message', '')
        user_id = data.get('user_id', '')
        
        result = handle_qq_message(message, user_id)
        if result:
            return jsonify({
                'reply': result,
                'at_sender': False
            })
        return jsonify({'reply': None})
    
    app.run(host='0.0.0.0', port=5000)


# 示例3: 简单的消息处理函数
def simple_integration():
    """
    简单的消息处理函数
    适用于自定义的机器人框架
    """
    # 初始化插件
    if not init_plugin():
        return
    
    # 模拟消息处理
    test_messages = [
        "/搜索 速度与激情",
        "搜索 复仇者联盟",
        "找资源 权力的游戏"
    ]
    
    for msg in test_messages:
        print(f"\n用户消息: {msg}")
        result = handle_qq_message(msg)
        if result:
            print(f"机器人回复:\n{result}")
        print("-" * 50)


if __name__ == "__main__":
    # 运行简单示例
    simple_integration()

