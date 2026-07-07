---
version: 0.1.0
name: 58pic-generate
description: |
  Generate images and videos, search and download stock assets
  via 千图AI (58pic) open platform. Use when: "generate an image",
  "make a video", "text to image", "image to image", "同款图片",
  "animate this photo", "image to video", "search for images",
  "find stock photos", "search design templates", "check my credits",
  "list AI models", "what models are available", "download image".
  Supports: text-to-image, image-to-image, same-style, text-to-video,
  image-to-video, multi-aspect ratios, custom resolution/duration.
argument-hint: "[prompt-or-request] [--model <id>] [--image <url>]"
allowed-tools: Bash
---

# 千图AI (58pic) — Image & Video Generation

Submit AI generation jobs and search assets on 千图AI open platform.
Wraps the `58pic` CLI (`@58pic/cli`).

## Step 0 — Bootstrap

Before any other command:

**1. Check CLI**

```bash
58pic --version
```

If command not found, install:

```bash
npm install -g @58pic/cli
```

**2. Check auth status**

```bash
58pic auth status -f json
```

If `loggedIn` is `false`, authenticate using one of these methods:

| Method | Command | When to use |
|---|---|---|
| **API Key** | `58pic config init --api-key sk_YOUR_KEY` | Fastest — one command, no browser |
| **OAuth login** | `58pic auth login` | No API key yet; opens browser for authorization |

After `58pic auth login`, wait for the user to confirm they completed the browser authorization step before continuing.

Once `loggedIn: true`, proceed.

---

## UX Rules

1. **Show results, not dumps.** Print image/video URLs and a one-line summary. Never dump raw JSON in chat.
2. **Always use `-f json`** for machine-readable output, then extract with `jq`.
3. **Always poll to completion.** After submitting a generation job, keep polling `same-style-status` until status `3` (succeeded) or a failure code. Don't leave the user with just an `ai_id`.
4. **Discover models at runtime.** Never hardcode model IDs. Run `58pic models` first.
5. **Set expectations for video.** Video generation takes 1–5 minutes. Show a brief "Generating your video…" message while polling.
6. **One question at a time.** If something is missing (model, prompt), ask for the most critical piece and proceed with smart defaults for the rest.

---

## Workflow — Image Generation

### Step 1 — Pick a model

```bash
58pic models -f json | jq '[.data.models[] | select(.category=="image") | {id, name}]'
```

Choose the model that best fits the task. See `references/model-selection.md` for guidance.

### Step 2 — (Optional) Check aspect ratios

```bash
58pic model-capabilities <model_id> -f json \
  | jq '[.data.aspect_options[] | {id, label, is_vip}]'
```

Pass `--aspect <id>` to `same-style` to override the default ratio. You can also pass a ratio string like `"16:9"` — the CLI will match the closest option.

### Step 3 — Submit & poll

**Text-to-image:**

```bash
RESULT=$(58pic same-style -m <model_id> --prompt "a serene mountain lake at golden hour" -f json)
AI_ID=$(echo "$RESULT" | jq -r '.data.ai_id // .data[0].ai_id // empty')
```

**Image-to-image** (provide a reference image URL):

```bash
RESULT=$(58pic same-style -m <model_id> \
  --reference-url "https://example.com/ref.jpg" \
  --prompt "make it oil painting style" -f json)
AI_ID=$(echo "$RESULT" | jq -r '.data.ai_id // .data[0].ai_id // empty')
```

**Same-style from platform asset** (use a pid from `58pic search`):

```bash
RESULT=$(58pic same-style -m <model_id> --picid <pid> \
  --prompt "same composition but in winter" -f json)
AI_ID=$(echo "$RESULT" | jq -r '.data.ai_id // .data[0].ai_id // empty')
```

**Poll until done:**

```bash
while true; do
  POLL=$(58pic same-style-status "$AI_ID" -f json)
  STATUS=$(echo "$POLL" | jq -r '.data.status')
  [ "$STATUS" = "3" ] && break                               # 3 = succeeded
  [[ "$STATUS" != "1" && "$STATUS" != "2" ]] && break        # 1/2 = running
  sleep 3
done
```

**Extract and present results:**

```bash
# Check if succeeded
if [ "$(echo "$POLL" | jq -r '.data.status')" = "3" ]; then
  echo "$POLL" | jq -r '.data.details[]? | .image_url // .url // empty'
else
  echo "Generation failed: $(echo "$POLL" | jq -r '.data.error_msg // "unknown error"')"
fi
```

**Generate multiple images** (up to model's `max_generate_num`):

```bash
58pic same-style -m <model_id> --prompt "..." --nums 4 --aspect "1:1" -f json
```

---

## Workflow — Video Generation

### Step 1 — Pick a video model

```bash
58pic models -f json | jq '[.data.models[] | select(.category=="video") | {id, name}]'
```

### Step 2 — Check video capabilities

```bash
58pic model-capabilities <model_id> -f json | jq '{
  aspect:     [.data.aspect_options[]     | {id, label}],
  resolution: [.data.resolution_options[] | {id, label}],
  duration:   [.data.duration_options[]   | {id, label}]
}'
```

### Step 3 — Submit & poll

**Text-to-video:**

```bash
RESULT=$(58pic generate-video -m <model_id> \
  --prompt "cinematic drone shot over a misty forest" \
  --aspect "16:9" \
  --resolution "1080p" \
  --duration "5s" \
  -f json)
AI_ID=$(echo "$RESULT" | jq -r '.data.ai_id // .data[0].ai_id // empty')
```

**Image-to-video:**

```bash
RESULT=$(58pic generate-video -m <model_id> \
  --reference-url "https://example.com/photo.jpg" \
  --prompt "gentle camera pan to the right" \
  -f json)
AI_ID=$(echo "$RESULT" | jq -r '.data.ai_id // .data[0].ai_id // empty')
```

**With start + end frame** (for models that support `supports_end_frame: true`):

```bash
RESULT=$(58pic generate-video -m <model_id> \
  --reference-url "https://example.com/start.jpg" \
  --end-frame-url "https://example.com/end.jpg" \
  --prompt "smooth transition" \
  -f json)
AI_ID=$(echo "$RESULT" | jq -r '.data.ai_id // .data[0].ai_id // empty')
```

**Poll** (same as image, but use longer sleep — video takes more time):

```bash
while true; do
  POLL=$(58pic same-style-status "$AI_ID" -f json)
  STATUS=$(echo "$POLL" | jq -r '.data.status')
  [ "$STATUS" = "3" ] && break
  [[ "$STATUS" != "1" && "$STATUS" != "2" ]] && break
  sleep 5
done
```

**Extract result:**

```bash
if [ "$(echo "$POLL" | jq -r '.data.status')" = "3" ]; then
  echo "$POLL" | jq -r '.data.details[]? | .video_url // .url // empty'
  # Cover image (if available)
  echo "$POLL" | jq -r '.data.details[]? | .cover_url // empty'
else
  echo "Video generation failed: $(echo "$POLL" | jq -r '.data.error_msg // "unknown error"')"
fi
```

---

## Workflow — Search & Download

### Search images

```bash
# Keyword search
58pic search "sunset beach" -f json \
  | jq '[.data.list[] | {pid: .id, title, thumb_url}]'

# AI semantic / vector search
58pic search "warm cozy coffee shop morning light" --ai -f json \
  | jq '[.data.list[] | {pid: .id, title, thumb_url}]'

# Paginate
58pic search "abstract gradient" --page 2 -f json | jq '[.data.list[] | {pid: .id, title}]'
```

### Download an asset (costs credits)

```bash
58pic download <pid> -f json \
  | jq '{preview_url: .data.preview_url, download_url: .data.url}'
```

---

## Credits

```bash
# Check balance and recent usage
58pic credits -f json | jq '{balance: .data.balance, recent: .data.list[:5]}'
```

---

## Generation status codes

| `data.status` | Meaning | Action |
|---|---|---|
| `1` | Running / generating | Keep polling |
| `3` | **Succeeded** ✓ | Extract result |
| `2` / `4` / `5` | **Failed** ✗ | Report `data.error_msg` |
| other | **Failed** ✗ | Report `data.error_msg` |

---

## Auth commands reference

```bash
58pic auth status          # Show current auth state (OAuth / API Key / none)
58pic auth login           # OAuth browser login
58pic auth logout          # Revoke and clear OAuth token
58pic config init          # Interactive API Key setup
58pic config init --api-key sk_xxx   # Non-interactive API Key setup
58pic config show          # Show current config (masked)
```

---

## Errors

See `references/troubleshooting.md` for error codes and fixes.

## Reference docs

Load on demand:

- `references/model-selection.md` — which model to use for which task, and how to read capabilities
- `references/search-categories.md` — valid `--did` category values for search filtering
- `references/troubleshooting.md` — common errors and fixes
