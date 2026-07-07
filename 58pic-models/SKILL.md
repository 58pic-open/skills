---
version: 0.1.0
name: 58pic-models
description: |
  List 千图AI / 58pic models and inspect model capabilities, supported
  inputs, aspect ratios, video resolution, duration, VIP-only options,
  max generation count, end-frame support, and audio support. Use when:
  "list AI models", "what models are available", "check model capabilities",
  "which model should I use", "模型列表", "模型能力".
argument-hint: "[image|video|model-id]"
allowed-tools: Bash
---

# 千图AI (58pic) — Models & Capabilities

Discover available models at runtime. Never hardcode model IDs in other skills.

## Bootstrap

```bash
58pic --version
58pic auth status -f json
```

If unauthenticated, use the `58pic-account` skill first.

## List Models

All models:

```bash
58pic models -f json | jq '.data.models[] | {id, name, category, capabilities}'
```

Image models:

```bash
58pic models -f json | jq '[.data.models[] | select(.category=="image") | {id, name}]'
```

Video models:

```bash
58pic models -f json | jq '[.data.models[] | select(.category=="video") | {id, name}]'
```

## Filter by Input Type

Image-to-image capable models:

```bash
58pic models -f json | jq '[
  .data.models[]
  | select(.category=="image")
  | select(.capabilities.accepts | contains(["single_image"]))
  | {id, name}
]'
```

Image-to-video capable models:

```bash
58pic models -f json | jq '[
  .data.models[]
  | select(.category=="video")
  | select(.capabilities.accepts | contains(["single_image"]))
  | {id, name}
]'
```

End-frame video models:

```bash
58pic models -f json | jq '[
  .data.models[]
  | select(.category=="video")
  | select(.capabilities.supports_end_frame == true)
  | {id, name}
]'
```

## Inspect One Model

```bash
58pic model-capabilities <model_id> -f json | jq '{
  aspect:     [.data.aspect_options[]     | {id, label, is_vip}],
  resolution: [.data.resolution_options[] | {id, label, is_vip}],
  duration:   [.data.duration_options[]   | {id, label, is_vip}]
}'
```

Prefer non-VIP options unless the user explicitly requests a VIP-only format.

## References

- `references/model-selection.md` — model selection guide
- `references/troubleshooting.md` — auth and API failures
