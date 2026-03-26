---
name: 58pic
description: >
  千图网（58pic）AI 开放平台技能集，提供素材搜索和 AI 做同款图片生成两大核心功能。
  包含两个子指令：
  - **58pic-search**：搜索千图网素材库，支持关键词/AI向量搜索、分类筛选、图片预览及下载素材
  - **58pic-ai**：调用千图 AI 做同款接口，以参考图或已有素材生成风格相近的新图片

  **触发时机（MUST USE this skill whenever）：**
  - 用户说"搜索千图"、"在58pic找素材"、"千图搜索"、"找张图"并提到千图/58pic
  - 用户说"千图做同款"、"58pic AI生成"、"基于这张图做同款"
  - 用户说"下载千图素材"、"58pic下载"、"下载这个PID的图"
  - 用户提到"PID"并操作千图素材
  - 用户首次使用本 skill 时，需要先完成配置初始化

  **首次使用必须先完成初始化**
---

# 千图网（58pic）AI 开放平台 Skill

## 脚本路径

```bash
SKILL_DIR=~/.claude/skill/58pic/scripts
```

---

## 0. 初始化配置（首次使用 / 关键词触发）

### 触发时机

以下任一情况触发配置引导：
- 用户首次提到千图/58pic
- 用户说"配置千图"、"设置58pic"、"初始化千图"
- 执行任何操作前检查配置，发现缺失项

### Step 1：检查当前配置

```bash
python3 "$SKILL_DIR/init_config.py" --check
```

返回示例：`{"missing": ["api_key", "output_dir"], "config_file": "~/.58pic_config.json"}`

根据 `missing` 数组决定需要引导的项目。**所有项目均可跳过**（按回车或用户明确说"跳过"）。

### Step 2：引导设置各项（缺什么问什么）

#### A. api_key（必须，不可跳过）

如果 `missing` 包含 `api_key`，告知用户：

> 🔑 **需要配置千图 API Key**
>
> 请访问以下链接，点击「新建令牌」创建：
> **https://ai.58pic.com/history?openHistory=1&historyType=5**
>
> API Key 格式：`sk_xxxxxxxxxxxxxxxx`（仅创建时展示一次，请立即复制）

用户提供后：
```bash
python3 "$SKILL_DIR/init_config.py" --api-key "sk_用户的key"
```

#### B. output_dir（可选，可跳过）

如果 `missing` 包含 `output_dir`，询问：

> 📁 **文件存放目录**（下载素材、AI 生成图片、预览页面将保存在此）
>
> 请输入目录路径，或按回车使用当前对话目录（推荐）：

- 用户提供路径 → `python3 "$SKILL_DIR/init_config.py" --output-dir "用户路径"`
- 用户跳过 → 不设置，每次操作使用当前对话工作目录下的 `58pic_output/`

#### C. default_model（可选，可跳过）

如果 `missing` 包含 `default_model`，且用户正在做 AI 生成，询问是否现在设置。
也可以在首次做同款时再选择。

### Step 3：确认存放目录（每次操作前）

**重要**：存放目录由以下优先级决定（从高到低）：
1. 用户在当前对话中明确说的目录
2. `~/.58pic_config.json` 中的 `output_dir`
3. 当前对话工作目录下的 `58pic_output/`

**在开始操作前，向用户确认**：
> 📁 文件将保存到：`{OUTPUT_DIR}`，确认吗？（可以说"改成 /其他/路径" 来更改）

用 `OUTPUT_DIR` 变量存储本次对话使用的目录，后续所有操作复用。

---

## API 基础信息

- **Base URL**：`https://ai.58pic.com/api/`
- **鉴权**：`Authorization: Bearer <api_key>`
- **请求体格式**：`Content-Type: application/json`

---

## 1. 指令：58pic-search（素材搜索）

### 分类 did 值（一级分类）

| did | 分类名称 |
|-----|---------|
| 0 | 全部（不传参数）|
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

每页固定 36 条，页码 1-100。

### 执行步骤

**Step 1：运行搜索**

```bash
python3 "$SKILL_DIR/search.py" \
  --keyword "关键词" \
  --page 1 \
  --output-dir "$OUTPUT_DIR" \
  [--did 16] \
  [--ai-search]
```

脚本末行输出 `__SEARCH_RESULT__:{...}`，从中解析 `session_file` 和 `output_dir`。

**Step 2：生成预览页面**

```bash
python3 "$SKILL_DIR/preview.py" \
  --session-file "$OUTPUT_DIR/session.json"
```

预览页面输出到 `$OUTPUT_DIR/preview.html`。

提供链接（使用绝对路径）：
`[查看搜索结果预览](computer://{OUTPUT_DIR的绝对路径}/preview.html)`

同时文字列出前几条结果（pid、标题）。

**Step 3：下载素材（用户指定时）**

```bash
python3 "$SKILL_DIR/download.py" \
  --pid "素材PID" \
  --output-dir "$OUTPUT_DIR"
```

下载成功后自动更新 `session.json`，然后重新生成预览：

```bash
python3 "$SKILL_DIR/preview.py" \
  --session-file "$OUTPUT_DIR/session.json"
```

---

## 2. 指令：58pic-ai（AI 做同款）

### 执行步骤

**Step 1：获取模型列表（首次或用户想换模型时）**

```bash
python3 "$SKILL_DIR/list_models.py"
```

保存用户选择：
```bash
python3 "$SKILL_DIR/init_config.py" --default-model "模型ID"
```

**Step 2：提交任务**

```bash
# 参考来源 A：千图素材 PID
python3 "$SKILL_DIR/ai_generate.py" \
  --prompt "描述" --model "模型ID" --ref-pid "PID" \
  --output-dir "$OUTPUT_DIR" [--generate-nums 1]

# 参考来源 B：图片 URL
python3 "$SKILL_DIR/ai_generate.py" \
  --prompt "描述" --model "模型ID" --ref-url "https://..." \
  --output-dir "$OUTPUT_DIR"

# 参考来源 C：本地图片
python3 "$SKILL_DIR/ai_generate.py" \
  --prompt "描述" --model "模型ID" --ref-image-path "/path/to/image.jpg" \
  --output-dir "$OUTPUT_DIR"
```

脚本自动轮询状态（`status=3` 成功，`status=2/4/5` 失败）。
完成后自动更新 `session.json`，输出 `__GENERATE_RESULT__:{...}`。

**Step 3：生成预览**

```bash
python3 "$SKILL_DIR/preview.py" \
  --session-file "$OUTPUT_DIR/session.json"
```

提供链接：
`[查看 AI 生成结果](computer://{OUTPUT_DIR的绝对路径}/preview.html)`

预览页「AI 生成」tab 显示本 session 全部历史批次。

---

## 预览页面数据结构（`window.PIC58_DATA`）

```json
{
  "version": 2,
  "generated_at": "2024-03-26 10:30:00",
  "search": {
    "keyword": "春节海报",
    "page": 1,
    "total_page": 28,
    "did_name": "海报展板",
    "ai_search": false,
    "search_time": "2024-03-26 10:30:00",
    "items": [
      {
        "pid": "74860190",
        "title": "春节海报模板",
        "preview_url": "https://preview.qiantucdn.com/...",
        "type": "image",
        "width": "1920",
        "height": "1080"
      }
    ]
  },
  "downloads": [
    {
      "pid": "74860190",
      "filename": "58pic_74860190.jpg",
      "path": "/abs/path/...",
      "size": "2.3 MB",
      "b64": "data:image/jpeg;base64,...",
      "timestamp": "2024-03-26 10:31:00"
    }
  ],
  "ai_results": [
    {
      "ai_id": "5182589",
      "model": "全能香蕉2.0",
      "prompt": "春节主题海报",
      "timestamp": "2024-03-26 10:35:00",
      "images": [
        {
          "filename": "58pic_ai_20240326_103500_1.jpg",
          "path": "/abs/path/...",
          "size": "1.2 MB",
          "b64": "data:image/jpeg;base64,..."
        }
      ]
    }
  ]
}
```

---

## 注意事项

- API Key 以 `sk_` 开头，保存在 `~/.58pic_config.json`，请勿泄露
- 搜索：每页固定 36 条，did 只能用文档中列出的值
- AI 做同款：需先通过 `available-models` 获取合法模型 ID
- 任务状态：`status=3` 成功，`status=2/4/5` 均为失败
- 点数不足返回 429，`data.remaining` 显示剩余量
- `preview_url`（搜索缩略图）直接用于 `<img src>`，浏览器可正常加载
- 本地下载/AI 生成文件通过 base64 内嵌到预览 HTML，无需服务器
