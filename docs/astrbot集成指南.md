# astrbot 集成指南

## 📋 快速集成

### 步骤 1: 复制插件文件

将插件文件复制到你的 astrbot 项目目录中，或者将插件目录添加到 Python 路径。

### 步骤 2: 在机器人代码中导入

```python
from pansearch import PanSearchPlugin
import json
```

### 步骤 3: 初始化插件（在机器人启动时）

```python
# 加载配置
with open('astrbot-pansou-transfer/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 创建插件实例（全局变量）
pansearch_plugin = PanSearchPlugin(config)
print("网盘搜索插件加载成功")
```

### 步骤 4: 在消息处理函数中使用

```python
def on_message(message, user_id, group_id=None):
    """消息处理函数"""
    
    # 检测搜索命令
    if message.startswith("/搜索") or message.startswith("/search"):
        keyword = message.replace("/搜索", "").replace("/search", "").strip()
        if keyword:
            result = pansearch_plugin.search_and_transfer(keyword)
            return result
        else:
            return "请输入搜索关键词，例如：/搜索 仙逆"
    
    return None  # 不处理其他消息
```

## 🔧 不同框架的集成方式

### 方式 1: 基于事件驱动的框架

```python
from pansearch import PanSearchPlugin
import json

# 初始化插件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
plugin = PanSearchPlugin(config)

# 注册消息事件
@bot.on_message()
async def handle_message(event):
    message = event.message
    user_id = event.user_id
    
    # 检测搜索命令
    if message.startswith("/搜索"):
        keyword = message.replace("/搜索", "").strip()
        if keyword:
            result = plugin.search_and_transfer(keyword)
            await event.reply(result)
```

### 方式 2: 基于回调函数的框架

```python
from pansearch import PanSearchPlugin
import json

# 初始化插件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
plugin = PanSearchPlugin(config)

def message_callback(message, user_id):
    """消息回调函数"""
    if message.startswith("/搜索"):
        keyword = message.replace("/搜索", "").strip()
        if keyword:
            return plugin.search_and_transfer(keyword)
    return None

# 注册回调
bot.register_message_handler(message_callback)
```

### 方式 3: 基于装饰器的框架

```python
from pansearch import PanSearchPlugin
import json

# 初始化插件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
plugin = PanSearchPlugin(config)

@bot.command("/搜索")
def search_command(message, user_id):
    """搜索命令处理"""
    keyword = message.replace("/搜索", "").strip()
    if keyword:
        return plugin.search_and_transfer(keyword)
    return "请输入搜索关键词"

@bot.command("/search")
def search_command_en(message, user_id):
    """英文搜索命令"""
    keyword = message.replace("/search", "").strip()
    if keyword:
        return plugin.search_and_transfer(keyword)
    return "Please enter a search keyword"
```

## 📝 完整示例

### 示例 1: 简单集成

```python
# bot.py
from pansearch import PanSearchPlugin
import json

# 初始化插件
with open('astrbot-pansou-transfer/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
pansearch_plugin = PanSearchPlugin(config)

def on_message(message, user_id):
    """消息处理"""
    # 检测搜索命令
    if message.startswith("/搜索"):
        keyword = message.replace("/搜索", "").strip()
        if keyword:
            return pansearch_plugin.search_and_transfer(keyword)
        else:
            return "请输入搜索关键词，例如：/搜索 仙逆"
    return None

# 你的机器人主循环
while True:
    message = get_message()  # 获取消息（根据你的框架调整）
    reply = on_message(message, user_id)
    if reply:
        send_reply(reply)  # 发送回复（根据你的框架调整）
```

### 示例 2: 支持多种触发方式

```python
from pansearch import PanSearchPlugin
import json

# 初始化插件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
plugin = PanSearchPlugin(config)

def on_message(message, user_id):
    """消息处理"""
    # 支持的触发词
    triggers = ["/搜索", "/search", "搜索", "找资源", "/找"]
    
    keyword = None
    for trigger in triggers:
        if message.startswith(trigger):
            keyword = message.replace(trigger, "").strip()
            break
    
    if keyword:
        try:
            result = plugin.search_and_transfer(keyword)
            return result
        except Exception as e:
            return f"❌ 搜索失败: {str(e)}"
    
    return None
```

### 示例 3: 带错误处理和日志

```python
from pansearch import PanSearchPlugin
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化插件
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    plugin = PanSearchPlugin(config)
    logger.info("网盘搜索插件初始化成功")
except Exception as e:
    logger.error(f"插件初始化失败: {e}")
    plugin = None

def on_message(message, user_id):
    """消息处理"""
    if not plugin:
        return "❌ 插件未初始化"
    
    if message.startswith("/搜索"):
        keyword = message.replace("/搜索", "").strip()
        if not keyword:
            return "请输入搜索关键词，例如：/搜索 仙逆"
        
        try:
            logger.info(f"用户 {user_id} 搜索: {keyword}")
            result = plugin.search_and_transfer(keyword)
            logger.info(f"搜索成功，返回结果")
            return result
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return f"❌ 搜索失败，请稍后重试"
    
    return None
```

## 🎯 自定义功能

### 自定义触发词

```python
# 修改触发词列表
SEARCH_TRIGGERS = ["/搜索", "/找资源", "帮我找", "搜索"]
```

### 自定义返回格式

```python
def custom_search(keyword):
    """自定义搜索函数"""
    result = plugin.search_and_transfer(keyword)
    # 自定义格式化
    return f"🔍 搜索「{keyword}」\n\n{result}"
```

### 添加权限控制

```python
ALLOWED_USERS = ["123456789", "987654321"]  # 允许使用的用户ID

def on_message(message, user_id):
    """消息处理（带权限控制）"""
    if user_id not in ALLOWED_USERS:
        return "❌ 您没有权限使用此功能"
    
    if message.startswith("/搜索"):
        keyword = message.replace("/搜索", "").strip()
        if keyword:
            return plugin.search_and_transfer(keyword)
    return None
```

## 📌 注意事项

1. **配置文件路径**：确保 `config.json` 的路径正确
2. **错误处理**：建议添加 try-except 处理异常
3. **日志记录**：建议记录搜索日志，方便调试
4. **性能优化**：如果消息量大，可以考虑异步处理
5. **频率限制**：建议添加请求频率限制，避免 API 被限流

## 🧪 测试

运行测试脚本验证集成：

```bash
python astrbot_integration.py
```

## 📞 需要帮助？

如果遇到问题：
1. 检查配置文件是否正确
2. 查看日志输出
3. 运行测试脚本验证插件功能
4. 根据你的 astrbot 框架调整代码

