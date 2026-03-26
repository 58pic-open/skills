# 58pic Skills

千图网（58pic）官方 AI Skill 集合，适用于 Claude Code、Cowork、Cursor、Windsurf、Continue 等 AI 工具。

## 可用 Skills

| Skill | 功能 |
|-------|------|
| [58pic](./58pic) | 素材搜索 & AI 做同款图片生成 |

## 快速安装

### 方式一：从 GitHub 安装（推荐）

```bash
# 安装到 Claude Code / Cowork
npx skills add github:58pic-open/skills/58pic

# 安装到 Cursor
npx skills add github:58pic-open/skills/58pic --tool cursor

# 安装到 Windsurf
npx skills add github:58pic-open/skills/58pic --tool windsurf

# 安装到 Continue
npx skills add github:58pic-open/skills/58pic --tool continue

# 安装到 VS Code + Copilot
npx skills add github:58pic-open/skills/58pic --tool vscode
```

### 方式二：本地安装（已下载/解压）

```bash
# 克隆仓库
git clone https://github.com/58pic-open/skills.git
cd skills

# 安装到 Claude Code / Cowork
npx skills add ./58pic

# 安装到指定工具
npx skills add ./58pic --tool cursor
npx skills add ./58pic --tool windsurf
```

## 配置 API Key

安装完成后，配置千图 API Key：

```bash
# 获取 API Key：https://ai.58pic.com/history?openHistory=1&historyType=5
python3 ~/.claude/skill/58pic/scripts/init_config.py --api-key sk_your_key

# 查看当前配置
python3 ~/.claude/skill/58pic/scripts/init_config.py --show
```

## 使用文档

详见 [安装与使用教程](./58pic_tutorial.html) 或访问 [千图 AI 开放平台](https://ai.58pic.com)。

## License

MIT © 58pic Open Platform
