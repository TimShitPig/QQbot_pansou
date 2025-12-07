# Ziliao API 对接说明（基于源代码）

根据 `www.ziliao.xyz` 源代码分析，API 接口信息如下：

## 📍 API 接口路径

```
POST https://www.ziliao.xyz/api/open/transfer
```

**文件位置**：`app/api/controller/Open.php` 第 15 行

## 📤 请求参数

### 请求方式
**POST**，使用 `application/x-www-form-urlencoded` 格式

### 参数列表

| 参数名 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| `api_key` | string | ✅ 是 | API 密钥，与数据库配置 `qfshop.api_key` 比较 | - |
| `url` | string | ✅ 是 | 要转存的网盘链接 | - |
| `code` | string | ❌ 否 | 提取码/密码 | 空字符串 |
| `expired_type` | int | ❌ 否 | 有效期类型：1=正式资源（永久），2=临时资源 | 1 |
| `isType` | int | ❌ 否 | 类型：0=转存并分享后的资源信息，1=直接获取资源信息 | 0 |
| `isSave` | int | ❌ 否 | 是否保存到数据库：0=不保存，1=保存 | 0 |

### 源代码参考

```php
// app/api/controller/Open.php 第 15-28 行
public function transfer()
{
    if(Config('qfshop.api_key') != input('api_key')){
        return jerr('api_key错误');
    }
    $urlData = [
        'expired_type' => input('expired_type')??1,  // 1正式资源 2临时资源
        'url' => input("url")?? '',
        'code' => input('code')??'',
        'isType' => input('isType')??0,
    ];
    if(empty($urlData['url'])){
        return jerr('资源地址不能为空');
    }
    // ... 转存逻辑
}
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

**常见错误信息**：
- `"api_key错误"` - API 密钥不匹配
- `"资源地址不能为空"` - 未提供 url 参数
- 其他转存失败的错误信息

### 源代码参考

```php
// app/common.php 第 10-19 行
function jok($message = 'success', $data = null)
{
    header("content-type:application/json;chartset=uft-8");
    if ($data) {
        echo json_encode(["code" => 200, "message" => $message, 'data' => $data]);
    } else {
        echo json_encode(["code" => 200, "message" => $message, 'data' => $data??'']);
    }
    die;
}

// app/common.php 第 35-40 行
function jerr($message = 'error', $code = 500)
{
    header("content-type:application/json;chartset=uft-8");
    echo json_encode(["code" => $code, "message" => $message]);
    die;
}
```

## 🔐 认证方式

**通过 POST 参数认证**：`api_key` 参数必须与数据库配置表中的 `qfshop.api_key` 值匹配

```php
// app/api/controller/Open.php 第 17-19 行
if(Config('qfshop.api_key') != input('api_key')){
    return jerr('api_key错误');
}
```

**注意**：
- 如果数据库中的 `api_key` 为空字符串，那么请求中的 `api_key` 也应该是空字符串
- 如果数据库中的 `api_key` 有值，请求中必须传递相同的值

## ✅ 插件代码已匹配

插件代码 (`pansearch.py`) 已经按照这个格式实现：

1. ✅ 使用 POST 请求
2. ✅ 使用 `application/x-www-form-urlencoded` 格式
3. ✅ 传递所有必需和可选参数
4. ✅ 处理 `code: 200` 的成功响应
5. ✅ 处理错误响应

## 🧪 测试 API

### 使用 curl 测试

```bash
curl -X POST https://www.ziliao.xyz/api/open/transfer \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "api_key=&url=https://pan.baidu.com/s/1test123&code=1234&expired_type=1&isType=0"
```

### 使用 Python 测试

```python
import requests

url = "https://www.ziliao.xyz/api/open/transfer"
payload = {
    "api_key": "",  # 如果数据库中的 api_key 为空，这里也传空字符串
    "url": "https://pan.baidu.com/s/1test123",
    "code": "1234",
    "expired_type": 1,
    "isType": 0
}

response = requests.post(url, data=payload)
result = response.json()
print(result)
```

## 📝 配置说明

在 `config.json` 中配置：

```json
{
  "pansou_api_url": "http://154.12.83.97:8085",
  "ziliao_api_url": "https://www.ziliao.xyz",
  "ziliao_api_path": "/api/open/transfer",
  "ziliao_api_key": "",  // 如果数据库中的 api_key 为空，这里也留空
  "max_results": 5,
  "timeout": 30
}
```

## 🔍 如何查看数据库中的 api_key

1. 登录网站后台
2. 进入"系统设置"或"配置管理"
3. 查找 `api_key` 配置项
4. 查看其值（可能为空）

或者直接查询数据库：
```sql
SELECT conf_value FROM qf_conf WHERE conf_key = 'api_key';
```

## ✅ 当前状态

插件代码已经完全匹配你的网站 API 格式，只需要：
1. 确认数据库中的 `api_key` 值
2. 在 `config.json` 中填入相同的值（如果为空则留空）
3. 测试转存功能

