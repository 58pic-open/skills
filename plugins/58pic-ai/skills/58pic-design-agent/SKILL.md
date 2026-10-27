---
version: 0.1.0
name: 58pic-design-agent
description: |
  Run 千图AI 智能设计 industry agents (电商设计 / 海报设计 / 品牌设计 / 社媒营销 /
  办公设计 / 视频设计) that plan and produce whole design deliverables.
  Use when: "电商套图", "主图", "详情页", "海报设计", "品牌 VI", "小红书图文",
  "PPT", "智能设计", "design agent", "make a product image set", "design a poster".
  For single images use 58pic-generate. For ready-made 风格玩法 use 58pic-miniapp.
argument-hint: "[design request] [--agent <key>] [--image <url>]"
allowed-tools: Bash
---

# 千图AI — 智能设计行业 Agent

The agent plans the job (copy, layout, multiple images) itself, may ask the user
follow-up questions, and keeps context in a `session_id` for revisions.
Requires `@58pic/cli` ≥ 0.1.5 (`58pic --version`; upgrade with `npm install -g @58pic/cli@latest`).
If `58pic auth status -f json` shows `loggedIn: false`, use `58pic-account` first.

## 1. Pick an agent and sub-mode

```bash
58pic agent list -f json | jq '[.agents[] | {key, name, subtitle,
  modes: [.second_modes[] | {name, params: [.params[] | {key, type, required, options}]}]}]'
```

- Choose `key` by the user's industry; choose a `second_modes[].name`.
- Collect each param; `select` / `multi_select` values must come from `options`;
  ask the user (one question at a time) for missing `required` params.
- Unsure which agent → omit `-a` (全能 Agent chooses the mode itself).

## 2. Start the design (consumes credits)

Put the request text before the options; multi-select values are comma-separated.

```bash
58pic agent run "保温杯主图套图，卖点24小时保温" \
  -a <agent_key> --mode "<second_mode>" \
  -p 平台=亚马逊 -p 模块=主图,场景图 \
  -i https://preview.qiantucdn.com/xxx.png \
  --wait 60 -f json
```

Local images: upload first (the platform only accepts 千图 CDN URLs for references).

## 3. Handle `status`

| status | what to do |
|---|---|
| `succeeded` | show `images[]` and `agent_message` |
| `awaiting_user` | relay `ask_user` (question / options / steps) to the user verbatim — **never answer for them** — then `58pic agent reply` |
| `running` | the agent keeps working in the background; wait 20–30 s, then `58pic agent status <session_id> -f json`; repeat until it changes |
| `failed` | report `error`; do not auto-retry (credits) |

Answering multi-step questions:

```bash
58pic agent reply <session_id> "[多步骤选择]\n销售平台: 亚马逊\n生成模块: 主图、卖点图" -f json
```

## 4. Revisions

```bash
58pic agent reply <session_id> "背景换成户外露营场景，主色改为墨绿" -f json
```

Same session keeps the brief, brand info and earlier images.

## Rules

- Never call `agent run` again while a session is `running` — it double-charges; poll `agent status`.
- `agent reply` refuses while the previous turn is still running; wait first.
- Show credit usage when the CLI reports it; confirm before large sets (≥ 4 images).
