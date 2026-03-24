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
  - 用户首次使用本 skill 时，需要先完成 API Key 初始化

  **首次使用必须先初始化 API Key**，访问以下链接创建：
  https://ai.58pic.com/history?openHistory=1&historyType=5
---

# 千图网（58pic）AI 开放平台 Skill

本 skill 提供两个子指令，**首次使用前请完成初始化**。

## API 基础信息

- **Base URL**：`https://ai.58pic.com/api/`
- **路由方式**：通过 Query 参数 `r` 指定，例如 `?r=open-platform/search-images`
- **鉴权（二选一）**：
  - `Authorization: Bearer <api_key>`
  - `X-API-Key: <api_key>`
- **请求体格式**：`Content-Type: application/json`

---

## 0. 初始化：设置 API Key

**首次使用时，必须先检查是否已配置 API Key。**

### 检查配置

```bash
python3 /sessions/jolly-nice-feynman/mnt/skills/58pic/scripts/init_config.py --show
```

### 引导用户创建 API Key

如果未配置，告知用户：

> 🔑 **需要先配置千图 API Key**
>
> 请访问以下链接，点击「新建令牌」创建您的 API Key：
> **https://ai.58pic.com/history?openHistory=1&historyType=5**
>
> API Key 格式：`sk_xxxxxxxxxxxxxxxx`（仅创建时展示一次，请立即复制保存）

### 保存配置

用户提供 API Key 后，运行：

```bash
python3 /sessions/jolly-nice-feynman/mnt/skills/58pic/scripts/init_config.py --api-key "sk_用户的key"
```

---

## 1. 指令：58pic-search（素材搜索）

### 功能说明

搜索千图网素材库，展示搜索结果（含缩略图预览），用户可选择下载某个素材。

**重要限制**：
- 每页固定返回最多 **36 条**（不可自定义）
- 页码范围：1～100
- 分类 `kid` 仅支持以下值（传 0 表示全部）：

| kid | 分类名称 |
|-----|---------|
| 0 | 全部（不限类别） |
| 8 | 办公 |
| 130 | 免抠元素 |
| 275 | 广告设计 |
| 276 | 字体 |
| 668 | 摄影图 |
| 735 | 插画 |
| 743 | GIF动图 |

### 使用方式

用户说类似以下内容时触发：
- "搜索千图 春节海报"
- "在千图找 插画风格的圣诞素材"
- "千图 AI 搜索 扁平风格商务人物"（AI向量搜索）
- "千图搜索广告设计类的素材"

### 执行步骤

**Step 1：运行搜索脚本**

```bash
python3 /sessions/jolly-nice-feynman/mnt/skills/58pic/scripts/search.py \
  --keyword "关键词" \
  --page 1 \
  [--kid 275] \
  [--ai-search]
```

- `--ai-search`：使用 AI 向量搜索（适合描述性搜索，如"红色喜庆插画 灯笼 祥云"）
- `--kid`：按分类筛选，不传或传 0 为全部

**Step 2：生成图片预览页面**

```bash
python3 /sessions/jolly-nice-feynman/mnt/skills/58pic/scripts/preview.py \
  --results-file /tmp/58pic_search_results.json \
  --output /sessions/jolly-nice-feynman/mnt/skills/58pic_preview.html
```

在对话中提供链接：
[查看搜索结果预览](computer:///sessions/jolly-nice-feynman/mnt/skills/58pic_preview.html)

同时用文字列出前几条结果（pid、标题），方便用户直接复制 pid。

**Step 3：下载素材（用户指定时）**

```bash
python3 /sessions/jolly-nice-feynman/mnt/skills/58pic/scripts/download.py \
  --pid "素材PID" \
  --output-dir /sessions/jolly-nice-feynman/mnt/skills/
```

下载完成后提供文件链接。

---

## 2. 指令：58pic-ai（AI 做同款）

### 功能说明

调用千图 AI "做同款"接口，以参考图片（URL、base64 或千图素材 pid）为基础，生成风格相近的新图片。

**⚠️ 重要**：此接口本质是"做同款"，**必须提供至少一张参考图**（url、base64 或 pid）。若用户想纯文生图，建议告知这是基于参考图的生成。

### 使用方式

用户说类似以下内容时触发：
- "用 PID 12345 做同款"
- "参考这张图 https://... 生成一张类似的"
- "基于这张素材做同款，换成蓝色调"
- "千图 AI 生成，参考图是..."

### 执行步骤

**Step 1：获取可用模型列表（首次使用或用户想选模型时）**

```bash
python3 /sessions/jolly-nice-feynman/mnt/skills/58pic/scripts/list_models.py
```

询问用户选择模型，并记住用户偏好：

```bash
python3 /sessions/jolly-nice-feynman/mnt/skills/58pic/scripts/init_config.py \
  --default-model "模型ID"
```

**Step 2：提交做同款任务**

根据用户提供的参考来源，选择对应参数：

**参考来源 A：千图素材 PID（最常用，优先推荐）**
```bash
python3 /sessions/jolly-nice-feynman/mnt/skills/58pic/scripts/ai_generate.py \
  --prompt "用户的描述" \
  --model "模型ID" \
  --ref-pid "素材PID" \
  [--generate-nums 1]
```

**参考来源 B：图片 URL**
```bash
python3 /sessions/jolly-nice-feynman/mnt/skills/58pic/scripts/ai_generate.py \
  --prompt "用户的描述" \
  --model "模型ID" \
  --ref-url "https://参考图片URL" \
  [--generate-nums 1]
```

**参考来源 C：本地图片（Base64 上传）**
```bash
python3 /sessions/jolly-nice-feynman/mnt/skills/58pic/scripts/ai_generate.py \
  --prompt "用户的描述" \
  --model "模型ID" \
  --ref-image-path "/path/to/local/image.jpg"
```

**Step 3：轮询任务状态（脚本自动完成）**

脚本自动轮询 `same-style-status`（`status=3` 表示成功），打印进度。

**Step 4：展示结果**

生成完成后：

```bash
python3 /sessions/jolly-nice-feynman/mnt/skills/58pic/scripts/preview.py \
  --image-files /path/to/result1.png /path/to/result2.png \
  --prompt "用户描述" \
  --model "模型名" \
  --output /sessions/jolly-nice-feynman/mnt/skills/58pic_ai_result.html
```

提供链接：
[查看 AI 生成结果](computer:///sessions/jolly-nice-feynman/mnt/skills/58pic_ai_result.html)

---

## 参考文档

详见：
- `references/api_reference.md` — 完整 API 端点和参数说明（已根据官方文档更新）

---

## 注意事项

- API Key 以 `sk_` 开头，保存在 `~/.58pic_config.json`，请勿泄露
- 搜索：每页固定 36 条，kid 只能用文档中列出的值
- AI 做同款：需先通过 `available-models` 获取合法模型 ID
- 任务状态：`status=3` 为成功，图片 URL 为临时签名，过期需重新查询
- 点数不足时返回 429，`data.remaining` 显示剩余量
