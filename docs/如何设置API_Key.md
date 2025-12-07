# 如何设置 API Key

## 情况说明

根据 xinyue 源代码分析，API Key 存储在数据库的配置表中。有两种方式处理：

## 方案 1：不设置 API Key（推荐，如果数据库中的 api_key 为空）

如果你的网站数据库中 `api_key` 配置项为空，那么：

1. **在 `config.json` 中不填写或留空**：
```json
{
  "ziliao_api_key": ""
}
```

2. **代码会自动传递空字符串**，这样就能通过验证。

## 方案 2：在网站后台设置 API Key

### 步骤 1：登录网站后台

访问你的网站后台管理系统（通常是 `https://www.ziliao.xyz/admin`）

### 步骤 2：找到系统配置

在后台找到"系统设置"或"配置管理"页面

### 步骤 3：设置 API Key

找到 `api_key` 配置项，设置一个你想要的密钥（例如：`my_secret_key_123`）

### 步骤 4：在插件配置中使用

在 `config.json` 中填入相同的密钥：
```json
{
  "ziliao_api_key": "my_secret_key_123"
}
```

## 方案 3：修改代码跳过 API Key 验证（不推荐）

如果你想让 API 不需要验证，可以修改网站源代码：

**文件**：`app/api/controller/Open.php`

**修改前**（第17-19行）：
```php
if(Config('qfshop.api_key') != input('api_key')){
    return jerr('api_key错误');
}
```

**修改后**（注释掉验证）：
```php
// 暂时禁用 API Key 验证
// if(Config('qfshop.api_key') != input('api_key')){
//     return jerr('api_key错误');
// }
```

⚠️ **注意**：这样会降低安全性，不推荐在生产环境使用。

## 推荐做法

**最简单的方式**：在 `config.json` 中设置 `ziliao_api_key` 为空字符串 `""`，如果数据库中的 `api_key` 也是空的，就能正常工作。

```json
{
  "pansou_api_url": "http://154.12.83.97:8085",
  "ziliao_api_url": "https://www.ziliao.xyz",
  "ziliao_api_path": "/api/open/transfer",
  "ziliao_api_key": "",
  "max_results": 5,
  "timeout": 30
}
```

## 测试

配置好后，运行测试：
```bash
python test.py
```

如果返回 "api_key错误"，说明数据库中的 `api_key` 不为空，你需要：
1. 查看数据库中的实际值
2. 或者在后台设置一个值，然后在配置文件中使用相同的值

