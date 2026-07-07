---
version: 0.1.0
name: 58pic-assets
description: |
  Search and download stock assets, design templates, photos, backgrounds,
  posters, PPT templates, UI assets, cut-out elements, and AI digital art
  from 千图AI / 58pic. Use when: "search images", "find stock photos",
  "search design templates", "download image", "download asset",
  "找素材", "搜索模板", "下载素材".
argument-hint: "[keyword] [--did <category>] [--ai] [--page <n>]"
allowed-tools: Bash
---

# 千图AI (58pic) — Asset Search & Download

Search and download stock assets with the `58pic` CLI.

## Bootstrap

```bash
58pic --version
58pic auth status -f json
```

If unauthenticated, use the `58pic-account` skill first.

## UX Rules

1. Show a short, ranked list of useful assets; do not dump raw JSON.
2. Always include `pid`, title, and preview/thumbnail URL when available.
3. Ask before downloading if the operation may cost credits.
4. Use `--ai` for semantic searches when the query is descriptive or visual.
5. For category filtering, load `references/search-categories.md`.

## Search

Keyword search:

```bash
58pic search "sunset beach" -f json \
  | jq '[.data.list[] | {pid: .id, title, thumb_url}]'
```

AI semantic search:

```bash
58pic search "warm cozy coffee shop morning light" --ai -f json \
  | jq '[.data.list[] | {pid: .id, title, thumb_url}]'
```

Category search:

```bash
58pic search "春节海报" --did 2 -f json \
  | jq '[.data.list[] | {pid: .id, title, thumb_url}]'
```

Pagination:

```bash
58pic search "abstract gradient" --page 2 -f json \
  | jq '[.data.list[] | {pid: .id, title}]'
```

## Download

Downloading may consume credits or require a plan. Confirm with the user first.

```bash
58pic download <pid> -f json \
  | jq '{preview_url: .data.preview_url, download_url: .data.url}'
```

## Use an Asset for Generation

Pass a searched `pid` to `58pic-generate` workflows:

```bash
58pic same-style -m <model_id> --picid <pid> \
  --prompt "same composition but in winter" \
  -f json
```

## References

- `references/search-categories.md` — valid `--did` category values
- `references/troubleshooting.md` — auth, download, and rate limit failures
