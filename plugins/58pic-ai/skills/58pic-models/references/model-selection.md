# Model Selection Guide

## Discovering models

Always run this first — never hardcode model IDs:

```bash
58pic models -f json | jq '.data.models[] | {id, name, category, capabilities}'
```

Key response fields per model:

| Field | Description |
|---|---|
| `id` | Pass to `-m` / `--model` |
| `name` | Human-readable display name |
| `category` | `image` \| `video` \| `music` \| `three_d` |
| `capabilities.accepts` | Input types: `"text"`, `"single_image"`, `"multi_image"` |
| `capabilities.max_generate_num` | Max images per job |
| `capabilities.supports_end_frame` | Video: accepts an end-frame image |
| `capabilities.supports_audio` | Video: supports audio generation |
| `options.aspect[]` | Available aspect ratios `{id, value, label}` |
| `options.resolution[]` | Video: available resolutions |
| `options.duration[]` | Video: available durations |

---

## Image model selection

| Use case | Filter |
|---|---|
| Text-to-image | `category == "image"` and `accepts` includes `"text"` |
| Image-to-image | `accepts` includes `"single_image"` |
| Multi-reference image | `accepts` includes `"multi_image"` |
| Same-style from platform pid | Any image model (use `--picid`) |
| Generate multiple at once | `max_generate_num > 1` |

```bash
# Find image models that accept a reference image
58pic models -f json | jq '[
  .data.models[]
  | select(.category=="image")
  | select(.capabilities.accepts | contains(["single_image"]))
  | {id, name}
]'
```

---

## Video model selection

| Use case | Filter |
|---|---|
| Text-to-video | `category == "video"`, `accepts` includes `"text"` |
| Image-to-video | `category == "video"`, `accepts` includes `"single_image"` |
| With custom end frame | `supports_end_frame == true` |
| With audio | `supports_audio == true` |

```bash
# Find video models that support image-to-video
58pic models -f json | jq '[
  .data.models[]
  | select(.category=="video")
  | select(.capabilities.accepts | contains(["single_image"]))
  | {id, name}
]'
```

---

## Checking model capabilities (aspect / resolution / duration)

```bash
58pic model-capabilities <model_id> -f json
```

Returns three option lists:

- `aspect_options[]` — `{id, label, name, is_vip}` — pass `id` to `--aspect`
- `resolution_options[]` — video only — pass `id` to `--resolution`
- `duration_options[]` — video only — pass `id` to `--duration`

**Shortcut:** You can also pass human-readable strings like `"16:9"`, `"1080p"`, `"5s"` to `--aspect`, `--resolution`, `--duration`. The CLI will find the closest matching option automatically.

**VIP options:** Options with `is_vip: true` require a paid membership. Prefer non-VIP options unless the user explicitly requests a VIP-only format.

---

## Quick commands

```bash
# All image models
58pic models -f json | jq '[.data.models[] | select(.category=="image") | {id,name}]'

# All video models
58pic models -f json | jq '[.data.models[] | select(.category=="video") | {id,name}]'

# Capabilities for a specific model
58pic model-capabilities <model_id> -f json | jq '{
  aspect:     [.data.aspect_options[]     | select(.is_vip==false) | {id,label}],
  resolution: [.data.resolution_options[] | select(.is_vip==false) | {id,label}],
  duration:   [.data.duration_options[]   | select(.is_vip==false) | {id,label}]
}'
```
