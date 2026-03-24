# 58pic Skills

千图网（58pic）官方 AI Skill 集合，适用于 Claude Code、Cowork、Cursor、Windsurf、Continue 等 AI 工具。

## 可用 Skills

| Skill | 功能 | npm 包 |
|-------|------|--------|
| [58pic](./58pic) | 素材搜索 & AI 做同款图片生成 | `@58pic/skill` |

## 快速安装

### 方式一：npx 在线安装（推荐）

```bash
# 安装到 Claude Code / Cowork
npx skills add @58pic/skill

# 安装到 Cursor
npx skills add @58pic/skill --tool cursor

# 安装到 Windsurf
npx skills add @58pic/skill --tool windsurf

# 安装到 Continue
npx skills add @58pic/skill --tool continue

# 安装到 VS Code + Copilot
npx skills add @58pic/skill --tool vscode
```

### 方式二：从 GitHub 安装

```bash
npx skills add github:58pic-open/skills#path=58pic
```

### 方式三：本地安装（已下载/解压）

```bash
# 下载 zip
curl -L https://preview.58pic.com/AI/SKILLS/58pic.zip -o 58pic.zip
unzip 58pic.zip -d ./58pic

# 本地路径安装，指定工具
npx skills add ./58pic
npx skills add ./58pic --tool cursor
```

### 方式四：直接 npm 安装

```bash
npm install @58pic/skill
```

## 配置 API Key

安装完成后，配置千图 API Key：

```bash
# 获取 API Key：https://ai.58pic.com/history?openHistory=1&historyType=5
python3 ~/.claude/skills/58pic/scripts/init_config.py --api-key sk_your_key
```

## 使用文档

详见 [安装与使用教程](./58pic_tutorial.html) 或访问 [千图 AI 开放平台](https://ai.58pic.com)。

## License

MIT © 58pic Open Platform
