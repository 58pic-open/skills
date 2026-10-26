---
version: 0.1.0
name: 58pic-miniapp
description: |
  Run 千图AI MiniApps (站点「风格玩法」/ AI 应用): pre-tuned one-click effects such as
  商品套图, 批量换背景, AI 详情页, 商品打光, 产品分解特效, 万物可种, 萌宠打工记.
  Use when: "风格玩法", "MiniApp", "一键做同款效果", "用千图的XX玩法",
  "批量换背景", "商品套图", "做个同款特效视频".
  For free-form generation use 58pic-generate; for multi-step design briefs use 58pic-design-agent.
argument-hint: "[miniapp name or id] [--image <url>] [prompt]"
allowed-tools: Bash
---

# 千图AI — MiniApp 风格玩法

Each MiniApp bundles a fixed model / template / workflow; the user only supplies
an image and/or a short prompt. Requires `@58pic/cli` ≥ 0.1.5.

## 1. Find the MiniApp

```bash
58pic miniapp list -k 套图 -f json | jq '[.body.data.list[] | {miniapp_id, name, description, kind, page_url}]'
```

`kind`: `same_style` (AI 作品同款) · `template` · `model` · `workflow`.
Several matches → show 3–5 to the user and let them pick.

## 2. Check what it needs

```bash
58pic miniapp get <miniapp_id> -f json | jq '.body.data | {name, needs_reference_image,
  prompt_template, prompt_slots, guide, sample_media}'
```

- `needs_reference_image: true` → you must pass a reference image; ask the user for one.
- `prompt_template` / `prompt_slots` → replace each `{slot}` with the user's content and send as the prompt.
  No prompt → the default template prompt is used.
- `kind: model` → a prompt is required.

## 3. Run and poll (consumes credits)

```bash
RESULT=$(58pic miniapp run <miniapp_id> "保温杯，户外露营风" \
  --reference-url https://preview.qiantucdn.com/xxx.png -f json)
AI_ID=$(echo "$RESULT" | jq -r '.body.data.ai_id // .body.data[0].ai_id // empty')

while true; do
  S=$(58pic same-style-status "$AI_ID" -f json)
  STATUS=$(echo "$S" | jq -r '.body.data.status')
  [ "$STATUS" = "3" ] || [ "$STATUS" = "success" ] && break
  case "$STATUS" in 2|4|5|failed) echo "$S"; break;; esac
  sleep 5
done
echo "$S" | jq '[.body.data.details[] | .image_url // .preview_url]'
```

Workflow MiniApps often take 1–3 minutes; tell the user before polling.

## Rules

- Don't re-run while a task is still generating — keep polling the same `ai_id`.
- Show the MiniApp's `page_url` if the user wants to try it on the website.
