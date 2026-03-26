# 千图 AI 开放平台 API 参考（已核实）

基于官方 API 文档整理。

## Base URL & 路由

```
Base URL: https://ai.58pic.com/api/
路由参数: ?r=open-platform/<action>
```

完整 URL 示例：
```
https://ai.58pic.com/api/?r=open-platform/search-images
```

## 鉴权（二选一）

```http
Authorization: Bearer sk_your_api_key
```
或
```http
X-API-Key: sk_your_api_key
```

---

## 接口总览

| 功能 | 路由 `r` | 方法 |
|------|-----------|------|
| 搜索图片 | `open-platform/search-images` | POST |
| 下载图片 | `open-platform/image-download` | GET 或 POST |
| 做同款（AI生成） | `open-platform/same-style` | POST |
| 查询任务状态 | `open-platform/same-style-status` | GET 或 POST |
| 可用模型列表 | `open-platform/available-models` | GET 或 POST |

---

## 搜索图片

**POST** `?r=open-platform/search-images`（别名：`search-image`）

### 请求参数

```json
{
  "keyword": "春节海报",
  "page": 1,
  "did": 2,
  "ai_search": false
}
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `keyword` | string | 关键词（非 AI 搜索时必填）|
| `page` | int | 页码 1-100，默认 1；超出范围返回 400 |
| `did` | int | 一级分类 ID（见下表），0或不传=不限，超出白名单返回 400 |
| `ai_search` | bool | true=AI向量搜索，false=关键词搜索 |

**每页固定 36 条，不可自定义。**

### 允许的 did 值（一级分类）

| did | 分类 |
|-----|------|
| 0 | 全部（不传此参数）|
| 2 | 海报展板 |
| 3 | 电商淘宝 |
| 4 | 装饰装修 |
| 5 | 网页UI |
| 6 | 音乐音效 |
| 7 | 3D素材 |
| 8 | PPT模板 |
| 10 | 背景 |
| 11 | 免抠元素 |
| 12 | Excel模板 |
| 14 | 简历模板 |
| 15 | Word模板 |
| 16 | 社交媒体 |
| 17 | 插画 |
| 40 | 字库 |
| 41 | 艺术字 |
| 53 | 高清图片 |
| 56 | 视频模板 |
| 57 | 元素世界 |
| 60 | AI数字艺术 |
| 66 | 品牌广告 |

### 响应

```json
{
  "code": 200,
  "msg": "ok",
  "data": {
    "list": [
      {
        "pid": "74860190",
        "kid": 275,
        "title": "春节海报模板",
        "keyword": "春节 海报",
        "description": "...",
        "preview_url": "https://preview.qiantucdn.com/58pic/74/.../xxx.jpg!qt_kuan320",
        "download_url": "https://..."
      }
    ],
    "total_page": 28,
    "suggestions": []
  }
}
```

### 计费

- 每日前 N 次（`searchFreePerDay`）免费
- 超出后每次扣 0.1 点（`searchPaidPoints`）
- 点数不足返回 **429**

---

## 下载图片

**GET/POST** `?r=open-platform/image-download`

参数：`pid`（千图素材 ID）

GET 方式：`?r=open-platform/image-download&pid=74860190`

POST JSON：`{"pid": "74860190"}`

### 响应

```json
{
  "code": 200,
  "msg": "ok",
  "data": {
    "pid": "74860190",
    "preview_url": "https://...320px预览图（无水印）...",
    "download_url": "https://...七牛临时签名（长边最大2048px）...",
    "width": 1920,
    "height": 1080
  }
}
```

- `download_url`：七牛私有临时签名，默认有效期 3600s（可配置至 7 天）
- 扣 **1 点**；点数不足返回 **429**

---

## 可用模型列表

**GET/POST** `?r=open-platform/available-models`（别名：`available-model`）

无请求参数。

### 响应

```json
{
  "code": 200,
  "msg": "ok",
  "data": {
    "is_member": true,
    "models": {
      "image": [
        {
          "id": 4740,
          "name": "千图万画 2.0",
          "capabilities": {
            "single_reference_supported": true,
            "multi_reference_supported": false,
            "max_generate_num": 4,
            "custom_pixel_supported": false,
            "select_options": [
              {
                "submit_key": "ratio",
                "name": "比例",
                "choices": [
                  {"id": 100, "label": "1:1", "value_english": "1:1"},
                  {"id": 101, "label": "16:9", "value_english": "16:9"},
                  {"id": 102, "label": "9:16", "value_english": "9:16"}
                ]
              }
            ]
          }
        }
      ],
      "video": [],
      "music": [],
      "three_d": []
    }
  }
}
```

- 每类型最多返回 **10 条**模型（按排序降序）
- 非会员过滤掉 `vip_use=1` 的模型

---

## AI 做同款

**POST** `?r=open-platform/same-style`

### 请求参数

```json
{
  "media_type": "image",
  "model": "4740",
  "reference_image_url": "",
  "reference_image_urls": [
    "//preview.qiantucdn.com/58pic/74/86/01/90758PIC8aF0M3mMWP497_PIC2018.jpg!w1024"
  ],
  "ai_title": "参考当前作品的风格，重新生成一张",
  "picid": "74860190",
  "generate_nums": 1
}
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `media_type` | ✅ | 固定 `"image"`（传 `video` 返回 400）|
| `model` | ✅ | 模型 ID（整数或字符串），从 `available-models` 获取 |
| `reference_image_url` | 三选一 | 单张参考图 URL（可传空字符串仅用多图）|
| `reference_image_urls` | 三选一 | 多张参考图 URL 列表 |
| `image_base64` | 三选一 | 图片 Base64（≤8MB，可含或不含前缀）|
| `prompt` / `ai_title` | 否 | 描述词（省略时默认「开放平台同款」）|
| `picid` | 否 | 千图素材 PID（用于同款文案等逻辑）|
| `generate_nums` | 否 | 生成张数，1-16，默认 1 |

### 响应

```json
{
  "code": 200,
  "msg": "ok",
  "data": {
    "ai_id": "123456",
    "task_id": "xxx"
  }
}
```

---

## 查询任务状态

**GET/POST** `?r=open-platform/same-style-status`

参数：`ai_id`（提交后返回的任务主键）

GET：`?r=open-platform/same-style-status&ai_id=123456`

POST JSON：`{"ai_id": 123456}`

### 响应

```json
{
  "code": 200,
  "msg": "ok",
  "data": {
    "ai_id": "123456",
    "message_id": "789",
    "status": 3,
    "details": [
      {
        "id": 999,
        "width": 1024,
        "height": 1024,
        "oss_url": "58pic/xx/xx/xxx.jpg",
        "status": 3,
        "preview_url": "https://...临时签名预览（720px长边）...",
        "download_url": "https://...临时签名无水印原文件...",
        "image_url": "https://...兼容字段（1024px）..."
      }
    ]
  }
}
```

- **`status=3`**：任务成功，`details` 中有成品 URL
- `preview_url`：临时签名，长边最大 720px（可配置）
- `download_url`：无水印原文件临时签名
- 临时 URL 过期后需重新调用接口获取

---

## 错误码

| HTTP | code | 说明 |
|------|------|------|
| 200 | 200 | 成功 |
| 400 | 400 | 参数/业务校验失败 |
| 401 | 401 | Key 缺失/无效/IP 不在白名单 |
| 429 | 429 | QPS 超限、日上限或点数不足；`data.remaining` 显示剩余点数 |
