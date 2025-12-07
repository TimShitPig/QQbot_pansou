# astrbot 网盘搜索转存插件

一个功能强大的网盘搜索转存插件，支持夸克、百度、UC、迅雷等多种网盘类型。

## 功能特性

- 🔍 **智能搜索**：支持"搜XX"、"求XX"等触发方式
- 📦 **多网盘支持**：夸克网盘、百度网盘、UC网盘、迅雷网盘
- 📄 **分页浏览**：每页显示6条结果，支持翻页
- 🎯 **选择转存**：输入序号即可选择资源并自动转存
- 🔗 **自动转存**：选择后自动调用转存API，返回最终链接

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

复制 `config.json.example` 为 `config.json` 并填写配置：

```json
{
  "pansou_api_url": "http://154.12.83.97:8085",
  "ziliao_api_url": "https://www.ziliao.xyz",
  "ziliao_api_path": "/api/open/transfer",
  "ziliao_api_key": "",
  "max_results": 50,
  "timeout": 30
}
```

### 3. 集成到 astrbot

```python
from astrbot_plugin import AstrbotPanSearchPlugin

# 初始化插件
pansearch_plugin = AstrbotPanSearchPlugin("config.json")

# 在消息处理函数中调用
def on_message(message, user_id):
    # 检查是否是搜索命令
    if message.startswith("搜") or message.startswith("求"):
        return pansearch_plugin.handle_message(message, user_id)
    
    # 检查是否是翻页或选择命令
    if message in ["下一页", "上一页"] or message.isdigit() or ("第" in message and "个" in message):
        return pansearch_plugin.handle_message(message, user_id)
    
    return None
```

## 使用方法

### 搜索资源

用户发送：`搜仙逆` 或 `求速度与激情`

机器人回复：
```
🔍 搜索结果（共 349 个，第 1/59 页）

【1】仙逆 4K臻彩MAX [附合集篇+剧场版][更新至117集]
    📦 夸克网盘

【2】仙逆 年番 【更117集】【4K .臻彩】 【杜比音效】&【臻悦全景声】
    📦 夸克网盘

【3】仙逆(2023)【最新一集】【4K.臻彩】【内嵌简中】【动画/古装/奇幻】【奇幻】【附剧场版】
    📦 百度网盘

【4】【短剧】仙逆（115集全集）谢蕊伊&王镱深
    📦 百度网盘

【5】仙逆
    📦 UC网盘

【6】仙逆年番(臻彩)
    📦 UC网盘

💡 输入「下一页」或「上一页」翻页
💡 输入「第X个」或「X」选择资源（如：第1个、1）
```

### 翻页浏览

用户发送：`下一页` 或 `上一页`

### 选择转存

用户发送：`1` 或 `第1个`

机器人回复：
```
✅ 转存成功！

📝 标题: 仙逆 4K臻彩MAX [更新至117集]
🔗 链接: https://pan.quark.cn/s/xxx
📦 网盘: 夸克网盘
```

## 文件结构

```
astrbot-pansou-transfer/
├── pansearch_enhanced.py    # 核心插件文件
├── astrbot_plugin.py        # astrbot 集成文件
├── config.json              # 配置文件（需要自己创建）
├── config.json.example      # 配置示例
├── requirements.txt         # 依赖列表
├── README.md               # 本文件
├── docs/                   # 文档目录
│   ├── astrbot集成指南.md
│   ├── API对接说明.md
│   └── ...
└── examples/               # 示例代码
    ├── astrbot_integration.py
    └── ...
```

## 配置说明

- `pansou_api_url`: 资源搜索API地址
- `ziliao_api_url`: 转存API地址
- `ziliao_api_path`: 转存API路径
- `ziliao_api_key`: 转存API密钥（如果不需要可以留空）
- `max_results`: 最大搜索结果数
- `timeout`: 请求超时时间（秒）

## 注意事项

1. 确保 `pansou_api_url` 可以正常访问
2. 确保 `ziliao_api_url` 可以正常访问
3. 如果转存API需要密钥，请在 `ziliao_api_key` 中填写
4. 每页显示6条结果，按顺序：夸克2条 -> 百度2条 -> UC2条

## 更多文档

详细文档请查看 `docs/` 目录：
- `astrbot集成指南.md` - 详细的集成说明
- `API对接说明.md` - API接口说明
- `如何设置API_Key.md` - API密钥设置指南

## 许可证

MIT License