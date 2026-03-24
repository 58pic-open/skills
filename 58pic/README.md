# @58pic/skill

千图网 AI Skill — 在任意 AI 工具中直接搜索千图素材、AI 做同款图片生成。

## 安装

```bash
# 推荐：npx 一键安装
npx skills add @58pic/skill

# 指定工具
npx skills add @58pic/skill --tool cursor
npx skills add @58pic/skill --tool windsurf
npx skills add @58pic/skill --tool continue
npx skills add @58pic/skill --tool vscode

# 本地安装（解压后）
npx skills add ./58pic
npx skills add ./58pic --tool cursor
```

## 配置

```bash
# 1. 获取 API Key（仅显示一次，请立即保存）
# https://ai.58pic.com/history?openHistory=1&historyType=5

# 2. 绑定 API Key
python3 scripts/init_config.py --api-key sk_your_key

# 3. 验证配置
python3 scripts/init_config.py --show
```

## 功能

### 素材搜索

```
搜索千图 春节海报
在千图找 插画风格圣诞素材
千图 AI 搜索 红色喜庆灯笼祥云
```

### AI 做同款

```
用 PID 12345678 做同款，换成蓝色调
参考这张图 https://... 生成一张类似风格的海报
（上传图片）基于这张图做同款，生成 4 张变体
```

### 下载素材

```
下载 PID 12345678 的素材
```

## 支持工具

| 工具 | 安装命令 |
|------|----------|
| Claude Code / Cowork | `npx skills add @58pic/skill` |
| Cursor | `npx skills add @58pic/skill --tool cursor` |
| Windsurf | `npx skills add @58pic/skill --tool windsurf` |
| Continue | `npx skills add @58pic/skill --tool continue` |
| VS Code + Copilot | `npx skills add @58pic/skill --tool vscode` |

## 文件结构

```
58pic/
├── package.json       # npm 包配置
├── SKILL.md           # Skill 定义（AI 工具读取入口）
├── README.md          # 本文档
├── scripts/           # 执行脚本
│   ├── init_config.py   # API Key 初始化
│   ├── search.py        # 素材搜索
│   ├── download.py      # 素材下载
│   ├── ai_generate.py   # AI 做同款生成
│   ├── list_models.py   # 模型列表
│   └── preview.py       # 预览页生成
└── references/
    └── api_reference.md # API 完整文档
```

## License

MIT © 58pic Open Platform
