# 58pic Skills

Agent skills for [千图AI (58pic)](https://ai.58pic.com) open platform.
Install into Claude Code / compatible AI IDEs with one command.

## Available skills

| Skill | Description |
|---|---|
| [`58pic-generate`](./58pic-generate/SKILL.md) | Generate images and videos via 千图AI |
| [`58pic-assets`](./58pic-assets/SKILL.md) | Search and download stock assets, photos, templates, and design resources |
| [`58pic-models`](./58pic-models/SKILL.md) | List AI models and inspect model capabilities |
| [`58pic-account`](./58pic-account/SKILL.md) | Configure CLI auth, API keys, OAuth login, and credits |

## Install

### Codex Plugin Marketplace

Install this repository as a Codex plugin marketplace:

```bash
codex plugin marketplace add https://github.com/58pic-open/skills
codex plugin add 58pic-ai@58pic-open-skills
```

Restart Codex after installing so the bundled 58pic skills are loaded.

### Skills CLI

```bash
npx skills add 58pic-open/skills
```

Or install a specific skill:

```bash
npx skills add 58pic-open/skills/58pic-generate
npx skills add 58pic-open/skills/58pic-assets
npx skills add 58pic-open/skills/58pic-models
npx skills add 58pic-open/skills/58pic-account
```

## Prerequisites

- **Node.js** ≥ 18
- A [千图AI open platform](https://ai.58pic.com) account
- API Key **or** OAuth login (the skill will guide you through setup)

## Quick start

After installing, invoke the skill in your AI IDE:

```
/58pic-generate generate a serene mountain lake at sunset
/58pic-assets search Spring Festival poster templates
/58pic-models list image models
/58pic-account check my credits
```

The skills will:
1. Check / install the `58pic` CLI automatically
2. Guide you through authentication (API Key or OAuth)
3. Route generation, asset search, model discovery, and account tasks to focused workflows

## Authentication

| Method | Command | When to use |
|---|---|---|
| API Key | `58pic config init --api-key sk_…` | Fastest — one command |
| OAuth | `58pic auth login` | No API key; browser-based login |

Get your API Key at: https://ai.58pic.com/open-platform

## Docs

- [58pic-generate skill](./58pic-generate/SKILL.md)
- [58pic-assets skill](./58pic-assets/SKILL.md)
- [58pic-models skill](./58pic-models/SKILL.md)
- [58pic-account skill](./58pic-account/SKILL.md)
- [Model selection](./58pic-generate/references/model-selection.md)
- [Troubleshooting](./58pic-generate/references/troubleshooting.md)

## License

MIT
