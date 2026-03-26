# @58pic/skill

千图网 AI Skill — 在任意 AI 工具中直接搜索千图素材、AI 做同款图片生成。

## 安装

```bash
# 推荐：从 GitHub 一键安装
npx skills add github:58pic-open/skills/58pic

# 指定工具
npx skills add github:58pic-open/skills/58pic --tool cursor
npx skills add github:58pic-open/skills/58pic --tool windsurf
npx skills add github:58pic-open/skills/58pic --tool continue
npx skills add github:58pic-open/skills/58pic --tool vscode

# 本地安装（克隆仓库后）
git clone https://github.com/58pic-open/skills.git
npx skills add ./skills/58pic
```

## 配置

```bash
# 1. 获取 API Key（仅显示一次，请立即保存）
# https://ai.58pic.com/history?openHistory=1&historyType=5

# 2. 绑定 API Key
python3 ~/.claude/skill/58pic/scripts/init_config.py --api-key sk_your_key

# 3. 设置文件存放目录（可选，不设置则使用当前目录）
python3 ~/.claude/skill/58pic/scripts/init_config.py --output-dir ~/58pic_files

# 4. 验证配置
python3 ~/.claude/skill/58pic/scripts/init_config.py --show
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
| Claude Code / Cowork | `npx skills add github:58pic-open/skills/58pic` |
| Cursor | `npx skills add github:58pic-open/skills/58pic --tool cursor` |
| Windsurf | `npx skills add github:58pic-open/skills/58pic --tool windsurf` |
| Continue | `npx skills add github:58pic-open/skills/58pic --tool continue` |
| VS Code + Copilot | `npx skills add github:58pic-open/skills/58pic --tool vscode` |

## 文件结构

```
58pic/
├── package.json       # 包配置
├── SKILL.md           # Skill 定义（AI 工具读取入口）
├── README.md          # 本文档
├── scripts/           # 执行脚本
│   ├── init_config.py   # 配置初始化（API Key、存放目录、默认模型）
│   ├── search.py        # 素材搜索
│   ├── download.py      # 素材下载
│   ├── ai_generate.py   # AI 做同款生成
│   ├── list_models.py   # 模型列表
│   └── preview.py       # 预览页生成（JSON + JS 动态渲染）
└── references/
    └── api_reference.md # API 完整文档
```

## License

MIT © 58pic Open Platform
