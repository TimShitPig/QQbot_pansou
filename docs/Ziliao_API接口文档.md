# Ziliao (www.ziliao.xyz) API 接口文档

根据 xinyue 源代码分析，API 接口信息如下：

## 📍 API 接口路径

```
POST https://www.ziliao.xyz/api/open/transfer
```

**说明**：这是 ThinkPHP 框架的标准路由格式
- `api` = 应用名称（app/api）
- `open` = 控制器名称（Open.php）
- `transfer` = 方法名称

## 📤 请求参数格式

### 请求方式
**POST**（使用 `application/x-www-form-urlencoded` 格式）

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| `api_key` | string | ✅ 是 | API 密钥，用于认证 | - |
| `url` | string | ✅ 是 | 要转存的网盘链接 | - |
| `code` | string | ❌ 否 | 提取码/密码 | 空字符串 |
| `expired_type` | int | ❌ 否 | 有效期类型：1=正式资源（永久），2=临时资源 | 1 |
| `isType` | int | ❌ 否 | 类型：0=转存并分享后的资源信息，1=直接获取资源信息 | 0 |
| `isSave` | int | ❌ 否 | 是否保存到数据库：0=不保存，1=保存 | 0 |

### 请求示例

```bash
curl -X POST https://www.ziliao.xyz/api/open/transfer \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "api_key=your_api_key&url=https://pan.baidu.com/s/1test123&code=1234&expired_type=1&isType=0"
```

## 📥 返回数据格式

### 成功响应

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "share_url": "https://转存后的分享链接",
    "title": "资源标题",
    "code": "提取码",
    "fid": "文件ID或文件ID数组"
  }
}
```

### 失败响应

```json
{
  "code": 500,
  "message": "错误信息"
}
```

**常见错误**：
- `{"code": 500, "message": "api_key错误"}` - API 密钥错误
- `{"code": 500, "message": "资源地址不能为空"}` - 未提供 url 参数
- `{"code": 500, "message": "转存失败"}` - 转存过程出错

## 🔐 认证方式

**通过参数认证**：在 POST 请求的 body 中传递 `api_key` 参数

```php
// 源代码中的认证逻辑（Open.php 第17行）
if(Config('qfshop.api_key') != input('api_key')){
    return jerr('api_key错误');
}
```

## 📝 完整请求示例

### Python 示例

```python
import requests

url = "https://www.ziliao.xyz/api/open/transfer"
payload = {
    "api_key": "your_api_key_here",
    "url": "https://pan.baidu.com/s/1test123",
    "code": "1234",
    "expired_type": 1,
    "isType": 0
}

response = requests.post(url, data=payload)
result = response.json()

if result.get("code") == 200:
    share_url = result["data"]["share_url"]
    title = result["data"]["title"]
    print(f"转存成功: {title}")
    print(f"分享链接: {share_url}")
else:
    print(f"转存失败: {result.get('message')}")
```

### JavaScript 示例

```javascript
fetch('https://www.ziliao.xyz/api/open/transfer', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: new URLSearchParams({
    api_key: 'your_api_key_here',
    url: 'https://pan.baidu.com/s/1test123',
    code: '1234',
    expired_type: 1,
    isType: 0
  })
})
.then(response => response.json())
.then(data => {
  if (data.code === 200) {
    console.log('转存成功:', data.data.share_url);
  } else {
    console.error('转存失败:', data.message);
  }
});
```

## 🔍 源代码位置

所有信息来自 xinyue 源代码：

1. **控制器文件**：`xinyue-search-main/app/api/controller/Open.php`
2. **转存逻辑**：`xinyue-search-main/extend/netdisk/Transfer.php`
3. **返回格式**：`xinyue-search-main/app/common.php` 中的 `jok()` 和 `jerr()` 函数

## ✅ 当前插件配置

插件代码已经按照这个格式实现，你只需要：

1. 在 `config.json` 中配置：
```json
{
  "ziliao_api_url": "https://www.ziliao.xyz",
  "ziliao_api_path": "/api/open/transfer",
  "ziliao_api_key": "你的实际API密钥"
}
```

2. 确保你的网站 API 格式与 xinyue 一致

## 🧪 测试 API

你可以使用以下命令测试你的 API：

```bash
curl -X POST https://www.ziliao.xyz/api/open/transfer \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "api_key=你的密钥&url=https://pan.baidu.com/s/1test&code=1234"
```

如果返回 `{"code": 200, ...}` 说明 API 正常工作！

