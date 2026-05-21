# 58pic Skills

Agent skills for [千图AI (58pic)](https://ai.58pic.com) open platform.
Install into Claude Code / compatible AI IDEs with one command.

## Available skills

| Skill | Description |
|---|---|
| [`58pic-generate`](./58pic-generate/SKILL.md) | Generate images & videos, search and download stock assets via 千图AI |

## Install

```bash
npx skills add 58pic-open/skills
```

Or install a specific skill:

```bash
npx skills add 58pic-open/skills/58pic-generate
```

## Prerequisites

- **Node.js** ≥ 18
- A [千图AI open platform](https://ai.58pic.com) account
- API Key **or** OAuth login (the skill will guide you through setup)

## Quick start

After installing, invoke the skill in your AI IDE:

```
/58pic-generate generate a serene mountain lake at sunset
```

The skill will:
1. Check / install the `58pic` CLI automatically
2. Guide you through authentication (API Key or OAuth)
3. Pick the right model and generate your image

## Authentication

| Method | Command | When to use |
|---|---|---|
| API Key | `58pic config init --api-key sk_…` | Fastest — one command |
| OAuth | `58pic auth login` | No API key; browser-based login |

Get your API Key at: https://ai.58pic.com/open-platform

## Docs

- [58pic-generate skill](./58pic-generate/SKILL.md)
- [Model selection](./58pic-generate/references/model-selection.md)
- [Troubleshooting](./58pic-generate/references/troubleshooting.md)

## License

MIT
