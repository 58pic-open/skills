---
version: 0.2.0
name: 58pic-generate
description: |
  Generate images and videos via 千图AI (58pic) open platform.
  Use when: "generate an image", "make a video", "text to image",
  "image to image", "同款图片", "animate this photo", "image to video".
  For asset search/download use 58pic-assets. For auth/credits use
  58pic-account. For model discovery use 58pic-models.
argument-hint: "[prompt-or-request] [--model <id>] [--image <url>]"
allowed-tools: Bash
---

# 千图AI (58pic) — Image & Video Generation

Generate images and videos through the `58pic` CLI (`@58pic/cli`).

## Bootstrap

Before generation:

```bash
58pic --version
58pic auth status -f json
```

If the CLI is missing:

```bash
npm install -g @58pic/cli
```

If `loggedIn` is `false`, use the `58pic-account` skill to authenticate.

## UX Rules

1. Always use `-f json` and extract only the useful result URLs.
2. Discover models at runtime; never hardcode model IDs. Use `58pic-models` or run `58pic models -f json`.
3. Poll to completion after submitting a job. Do not leave the user with only an `ai_id`.
4. For videos, set expectations: generation usually takes 1-5 minutes.
5. Ask one missing input at a time; use smart defaults for aspect ratio, resolution, duration, and count.

## Image Generation

### Pick an image model

```bash
58pic models -f json | jq '[.data.models[] | select(.category=="image") | {id, name}]'
```

For model selection details, load `references/model-selection.md`.

### Optional: check aspect ratios

```bash
58pic model-capabilities <model_id> -f json \
  | jq '[.data.aspect_options[] | {id, label, is_vip}]'
```

### Submit text-to-image

```bash
RESULT=$(58pic same-style -m <model_id> \
  --prompt "a serene mountain lake at golden hour" \
  --aspect "16:9" \
  -f json)
AI_ID=$(echo "$RESULT" | jq -r '.data.ai_id // .data[0].ai_id // empty')
```

### Submit image-to-image

```bash
RESULT=$(58pic same-style -m <model_id> \
  --reference-url "https://example.com/ref.jpg" \
  --prompt "make it oil painting style" \
  -f json)
AI_ID=$(echo "$RESULT" | jq -r '.data.ai_id // .data[0].ai_id // empty')
```

### Submit same-style from a 58pic asset

Use a `pid` returned by `58pic-assets` search:

```bash
RESULT=$(58pic same-style -m <model_id> \
  --picid <pid> \
  --prompt "same composition but in winter" \
  -f json)
AI_ID=$(echo "$RESULT" | jq -r '.data.ai_id // .data[0].ai_id // empty')
```

## Video Generation

### Pick a video model

```bash
58pic models -f json | jq '[.data.models[] | select(.category=="video") | {id, name}]'
```

### Check video options

```bash
58pic model-capabilities <model_id> -f json | jq '{
  aspect:     [.data.aspect_options[]     | {id, label}],
  resolution: [.data.resolution_options[] | {id, label}],
  duration:   [.data.duration_options[]   | {id, label}]
}'
```

### Submit text-to-video

```bash
RESULT=$(58pic generate-video -m <model_id> \
  --prompt "cinematic drone shot over a misty forest" \
  --aspect "16:9" \
  --resolution "1080p" \
  --duration "5s" \
  -f json)
AI_ID=$(echo "$RESULT" | jq -r '.data.ai_id // .data[0].ai_id // empty')
```

### Submit image-to-video

```bash
RESULT=$(58pic generate-video -m <model_id> \
  --reference-url "https://example.com/photo.jpg" \
  --prompt "gentle camera pan to the right" \
  -f json)
AI_ID=$(echo "$RESULT" | jq -r '.data.ai_id // .data[0].ai_id // empty')
```

### Submit with start and end frames

For models that support `supports_end_frame: true`:

```bash
RESULT=$(58pic generate-video -m <model_id> \
  --reference-url "https://example.com/start.jpg" \
  --end-frame-url "https://example.com/end.jpg" \
  --prompt "smooth transition" \
  -f json)
AI_ID=$(echo "$RESULT" | jq -r '.data.ai_id // .data[0].ai_id // empty')
```

## Polling

Poll image and video jobs with `same-style-status`:

```bash
while true; do
  POLL=$(58pic same-style-status "$AI_ID" -f json)
  STATUS=$(echo "$POLL" | jq -r '.data.status')
  [ "$STATUS" = "3" ] && break
  [[ "$STATUS" != "1" && "$STATUS" != "2" ]] && break
  sleep 5
done
```

Extract result URLs:

```bash
if [ "$(echo "$POLL" | jq -r '.data.status')" = "3" ]; then
  echo "$POLL" | jq -r '.data.details[]? | .image_url // .video_url // .url // empty'
  echo "$POLL" | jq -r '.data.details[]? | .cover_url // empty'
else
  echo "Generation failed: $(echo "$POLL" | jq -r '.data.error_msg // "unknown error"')"
fi
```

## Status Codes

| `data.status` | Meaning | Action |
|---|---|---|
| `1` | Running / generating | Keep polling |
| `2` | Running / queued | Keep polling |
| `3` | Succeeded | Extract result |
| other | Failed | Report `data.error_msg` |

## References

- `references/model-selection.md` — model picking and capability checks
- `references/troubleshooting.md` — common generation/auth/API failures
