# Search Categories (did values)

Pass `--did <value>` to `58pic search` to filter by category.
Omit `--did` (or pass `0`) to search all categories.

Each page returns **36 items fixed**. Page range: 1–100.

## Category table

| `did` | Category (中文) | Category (English) |
|---|---|---|
| `0` | 全部 | All (default, no filter) |
| `2` | 海报展板 | Posters & Banners |
| `3` | 电商淘宝 | E-commerce / Taobao |
| `4` | 装饰装修 | Home Decoration |
| `5` | 网页UI | Web & UI |
| `6` | 音乐音效 | Music & Sound Effects |
| `7` | 3D素材 | 3D Assets |
| `8` | PPT模板 | PPT Templates |
| `10` | 背景 | Backgrounds |
| `11` | 免抠元素 | Cut-out Elements |
| `12` | Excel模板 | Excel Templates |
| `14` | 简历模板 | Resume Templates |
| `15` | Word模板 | Word Templates |
| `16` | 社交媒体 | Social Media |
| `17` | 插画 | Illustrations |
| `40` | 字库 | Font Library |
| `41` | 艺术字 | Artistic Text |
| `53` | 高清图片 | HD Photos |
| `56` | 视频模板 | Video Templates |
| `57` | 元素世界 | Elements |
| `60` | AI数字艺术 | AI Digital Art |
| `66` | 品牌广告 | Brand Advertising |

> Only the values listed above are valid. Passing an unlisted `did` returns HTTP 400.

## Usage examples

```bash
# Search posters & banners
58pic search "春节" --did 2 -f json

# Search social media templates
58pic search "Instagram story" --did 16 -f json

# AI semantic search in illustrations
58pic search "abstract watercolor" --did 17 --ai -f json

# Search all categories (default)
58pic search "mountain landscape" -f json
```
