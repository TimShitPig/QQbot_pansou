# Ziliao API 接口对接说明

## 当前配置

插件已修改为对接 `www.ziliao.xyz` 的文件夹 API。

## 需要确认的 API 信息

请提供以下信息，以便完善对接：

### 1. API 接口地址

- **完整路径**：`https://www.ziliao.xyz/api/???`
- 当前默认使用：`/api/open/transfer`（与 xinyue 相同格式）

### 2. 请求方式

- [ ] POST
- [ ] GET
- [ ] 其他：_______

### 3. 请求参数

请提供你的 API 需要的参数格式，例如：

**当前代码使用的参数格式**：
```json
{
  "url": "网盘链接",
  "code": "提取码",
  "expired_type": 1,
  "isType": 0,
  "api_key": "API密钥（如果需要）"
}
```

**你的 API 实际需要的参数**：
```
参数1: _______
参数2: _______
...
```

### 4. 返回格式

请提供你的 API 返回的 JSON 格式，例如：

**当前代码期望的返回格式**：
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "share_url": "转存后的分享链接",
    "title": "资源标题",
    "code": "提取码"
  }
}
```

**或者**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "share_url": "...",
    "title": "..."
  }
}
```

**你的 API 实际返回格式**：
```json
{
  ...
}
```

### 5. 认证方式

- [ ] 需要 API Key（通过参数传递）
- [ ] 需要 Token（通过 Header 传递）
- [ ] 需要其他认证方式：_______
- [ ] 不需要认证

### 6. 请求头

如果需要特殊的请求头，请提供：
```
Content-Type: application/x-www-form-urlencoded
Authorization: Bearer xxx
...
```

## 测试接口

你可以使用以下方式测试你的 API：

```bash
# 使用 curl 测试
curl -X POST https://www.ziliao.xyz/api/open/transfer \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "url=https://pan.baidu.com/s/1test123&code=1234&api_key=your_key"
```

## 当前代码位置

转存功能的代码在 `pansearch.py` 的 `transfer_link` 方法中（第 122-166 行），你可以根据实际 API 格式进行调整。

## 下一步

1. 提供你的 API 接口信息
2. 我会根据你的 API 格式调整代码
3. 测试对接是否成功

