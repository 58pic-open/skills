#!/usr/bin/env python3
"""
千图网结果预览脚本
将搜索结果或 AI 生成图片渲染为 HTML 预览页面，方便用户查看和选择
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #f5f5f7;
      color: #1d1d1f;
      min-height: 100vh;
    }}
    .header {{
      background: linear-gradient(135deg, #e84118 0%, #ff6b35 100%);
      color: white;
      padding: 20px 30px;
      display: flex;
      align-items: center;
      gap: 15px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }}
    .logo {{ font-size: 28px; font-weight: 800; }}
    .header-info {{ flex: 1; }}
    .header h1 {{ font-size: 18px; font-weight: 600; }}
    .header p {{ font-size: 13px; opacity: 0.85; margin-top: 3px; }}
    .stats-bar {{
      background: white;
      padding: 12px 30px;
      display: flex;
      gap: 25px;
      align-items: center;
      border-bottom: 1px solid #e8e8e8;
      font-size: 14px;
      color: #666;
    }}
    .stats-bar strong {{ color: #e84118; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 16px;
      padding: 20px 30px;
      max-width: 1400px;
      margin: 0 auto;
    }}
    .card {{
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
      transition: transform 0.2s, box-shadow 0.2s;
      cursor: pointer;
    }}
    .card:hover {{
      transform: translateY(-3px);
      box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }}
    .card-img {{
      width: 100%;
      aspect-ratio: 4/3;
      object-fit: cover;
      background: #f0f0f0;
      display: block;
    }}
    .card-img-placeholder {{
      width: 100%;
      aspect-ratio: 4/3;
      background: linear-gradient(135deg, #f0f0f0, #e0e0e0);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 40px;
    }}
    .card-info {{
      padding: 10px 12px;
    }}
    .card-title {{
      font-size: 13px;
      font-weight: 500;
      color: #1d1d1f;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      margin-bottom: 5px;
    }}
    .card-meta {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      color: #999;
    }}
    .card-pid {{
      font-family: monospace;
      background: #f5f5f5;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 11px;
      color: #666;
    }}
    .badge {{
      padding: 2px 8px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 500;
    }}
    .badge-image {{ background: #e8f4fd; color: #0070c9; }}
    .badge-template {{ background: #fef3e2; color: #e67e22; }}
    .badge-vector {{ background: #e8faf0; color: #27ae60; }}
    .badge-psd {{ background: #f8e8ff; color: #8e44ad; }}
    .copy-btn {{
      background: none;
      border: 1px solid #ddd;
      border-radius: 6px;
      padding: 4px 10px;
      font-size: 11px;
      cursor: pointer;
      color: #666;
      transition: all 0.2s;
    }}
    .copy-btn:hover {{ background: #e84118; color: white; border-color: #e84118; }}
    .ai-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 20px;
      padding: 20px 30px;
      max-width: 1200px;
      margin: 0 auto;
    }}
    .ai-card {{
      background: white;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }}
    .ai-card img {{
      width: 100%;
      display: block;
    }}
    .ai-card-info {{
      padding: 15px;
    }}
    .ai-card-info h3 {{ font-size: 14px; font-weight: 600; margin-bottom: 6px; }}
    .ai-card-info p {{ font-size: 12px; color: #666; }}
    .download-btn {{
      display: block;
      width: 100%;
      background: linear-gradient(135deg, #e84118, #ff6b35);
      color: white;
      border: none;
      border-radius: 8px;
      padding: 10px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      margin-top: 12px;
      text-decoration: none;
      text-align: center;
    }}
    .prompt-box {{
      background: #f5f5f7;
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 12px;
      color: #666;
      margin-top: 8px;
      line-height: 1.5;
    }}
    .empty {{ text-align: center; padding: 60px; color: #999; }}
    .empty-icon {{ font-size: 48px; margin-bottom: 15px; }}
    .tip {{
      background: #fffbe6;
      border: 1px solid #ffe58f;
      border-radius: 8px;
      padding: 12px 20px;
      margin: 15px 30px;
      font-size: 13px;
      color: #614700;
    }}
    .tip code {{
      background: rgba(0,0,0,0.06);
      padding: 2px 6px;
      border-radius: 4px;
      font-family: monospace;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div class="logo">千图</div>
    <div class="header-info">
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </div>
  </div>
  {content}
  <script>
    function copyPid(pid) {{
      navigator.clipboard.writeText(pid).then(() => {{
        const btns = document.querySelectorAll('.copy-btn');
        btns.forEach(btn => {{
          if (btn.getAttribute('data-pid') === pid) {{
            btn.textContent = '已复制！';
            btn.style.background = '#27ae60';
            btn.style.color = 'white';
            setTimeout(() => {{
              btn.textContent = '复制PID';
              btn.style.background = '';
              btn.style.color = '';
            }}, 2000);
          }}
        }});
      }});
    }}
  </script>
</body>
</html>"""


def type_badge(material_type):
    badges = {
        "image": ("image", "图片"),
        "vector": ("vector", "矢量"),
        "psd": ("psd", "PSD"),
        "template": ("template", "模板"),
    }
    cls, label = badges.get(str(material_type).lower(), ("image", material_type or "素材"))
    return f'<span class="badge badge-{cls}">{label}</span>'


def build_search_content(data):
    items = data.get("items", [])
    total = data.get("total", 0)
    keyword = data.get("keyword", "")
    page = data.get("page", 1)

    stats = f"""
    <div class="stats-bar">
      搜索关键词：<strong>「{keyword}」</strong>
      &nbsp;|&nbsp; 共 <strong>{total}</strong> 条结果
      &nbsp;|&nbsp; 第 <strong>{page}</strong> 页，共 <strong>{len(items)}</strong> 条
      &nbsp;|&nbsp; 搜索时间：{data.get('search_time', '')}
    </div>
    <div class="tip">
      💡 找到心仪素材？<strong>复制 PID</strong> 后告诉我「下载 PID xxxxx」，或使用 <code>--ref-pid PID</code> 做同款 AI 生成
    </div>
    """

    if not items:
        return stats + '<div class="empty"><div class="empty-icon">🔍</div><p>未找到相关素材</p></div>'

    cards = []
    for item in items:
        pid = item.get("pid", "")
        title = item.get("title", "无标题")
        item_type = item.get("type", "image")
        thumbnail = item.get("thumbnail", "")
        width = item.get("width", "")
        height = item.get("height", "")
        fmt = item.get("format", "")

        img_html = ""
        if thumbnail:
            img_html = f'<img class="card-img" src="{thumbnail}" alt="{title}" loading="lazy" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">'
            img_html += f'<div class="card-img-placeholder" style="display:none">🖼️</div>'
        else:
            img_html = '<div class="card-img-placeholder">🖼️</div>'

        size_info = f"{width}×{height}" if width and height else fmt

        card = f"""
        <div class="card" onclick="copyPid('{pid}')">
          {img_html}
          <div class="card-info">
            <div class="card-title" title="{title}">{title}</div>
            <div class="card-meta">
              {type_badge(item_type)}
              <span style="color:#bbb">{size_info}</span>
            </div>
            <div style="display:flex;align-items:center;gap:6px;margin-top:8px">
              <span class="card-pid">PID: {pid}</span>
              <button class="copy-btn" data-pid="{pid}" onclick="event.stopPropagation();copyPid('{pid}')">复制PID</button>
            </div>
          </div>
        </div>"""
        cards.append(card)

    return stats + f'<div class="grid">{"".join(cards)}</div>'


def build_ai_content(image_file, prompt="", model=""):
    if not os.path.exists(image_file):
        return '<div class="empty"><div class="empty-icon">❌</div><p>图片文件不存在</p></div>'

    # 将图片转为 base64 嵌入 HTML（避免路径问题）
    with open(image_file, "rb") as f:
        img_data = base64.b64encode(f.read()).decode("utf-8")

    ext = os.path.splitext(image_file)[1].lower().strip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/png")

    filename = os.path.basename(image_file)
    file_size = os.path.getsize(image_file)

    content = f"""
    <div class="tip">
      ✅ AI 图片生成成功！点击「保存图片」下载到本地，或告诉我您是否满意，需要继续调整。
    </div>
    <div class="ai-grid">
      <div class="ai-card">
        <img src="data:{mime};base64,{img_data}" alt="AI生成图片">
        <div class="ai-card-info">
          <h3>🎨 生成完成</h3>
          <p>文件名：{filename}</p>
          <p>文件大小：{file_size/1024:.0f} KB</p>
          {f'<p>使用模型：{model}</p>' if model else ''}
          {f'<div class="prompt-box">📝 描述词：{prompt}</div>' if prompt else ''}
          <a href="data:{mime};base64,{img_data}" download="{filename}" class="download-btn">
            ⬇️ 保存图片
          </a>
        </div>
      </div>
    </div>"""

    return content


def build_ai_multi_content(image_files, prompt="", model=""):
    """多张图片结果展示"""
    cards = []
    for img_path in image_files:
        if not os.path.exists(img_path):
            continue
        with open(img_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode("utf-8")
        ext = os.path.splitext(img_path)[1].lower().strip(".")
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/png")
        filename = os.path.basename(img_path)
        file_size = os.path.getsize(img_path)

        card = f"""
        <div class="ai-card">
          <img src="data:{mime};base64,{img_data}" alt="AI生成图片">
          <div class="ai-card-info">
            <h3>{filename}</h3>
            <p>{file_size/1024:.0f} KB</p>
            <a href="data:{mime};base64,{img_data}" download="{filename}" class="download-btn">⬇️ 保存图片</a>
          </div>
        </div>"""
        cards.append(card)

    tip = '<div class="tip">✅ AI 图片生成成功！点击「保存图片」下载，或告诉我是否需要调整。</div>'
    if not cards:
        return tip + '<div class="empty"><div class="empty-icon">⚠️</div><p>没有可预览的图片</p></div>'

    prompt_html = f'<div style="padding:0 30px 10px;font-size:13px;color:#666">📝 描述词：{prompt}</div>' if prompt else ""
    return tip + prompt_html + f'<div class="ai-grid">{"".join(cards)}</div>'


def main():
    parser = argparse.ArgumentParser(description="千图网结果预览生成")
    parser.add_argument("--results-file", help="搜索结果 JSON 文件路径")
    parser.add_argument("--image-file", help="AI 生成单张图片路径")
    parser.add_argument("--image-files", nargs="+", help="AI 生成多张图片路径列表")
    parser.add_argument("--prompt", default="", help="生成描述词（用于 AI 结果页面）")
    parser.add_argument("--model", default="", help="使用的模型（用于 AI 结果页面）")
    parser.add_argument("--output", required=True, help="输出 HTML 文件路径")
    args = parser.parse_args()

    if args.results_file:
        # 搜索结果预览
        with open(args.results_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        keyword = data.get("keyword", "")
        title = f"搜索结果：{keyword}"
        subtitle = f"千图网素材库搜索 · {time.strftime('%Y-%m-%d %H:%M')}"
        content = build_search_content(data)

    elif args.image_files:
        # 多张 AI 生成结果
        title = "AI 图片生成结果"
        subtitle = f"千图 AI 开放平台 · {time.strftime('%Y-%m-%d %H:%M')}"
        content = build_ai_multi_content(args.image_files, args.prompt, args.model)

    elif args.image_file:
        # 单张 AI 生成结果
        title = "AI 图片生成结果"
        subtitle = f"千图 AI 开放平台 · {time.strftime('%Y-%m-%d %H:%M')}"
        content = build_ai_content(args.image_file, args.prompt, args.model)

    else:
        print("❌ 请指定 --results-file 或 --image-file 或 --image-files")
        sys.exit(1)

    html = HTML_TEMPLATE.format(title=title, subtitle=subtitle, content=content)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 预览页面已生成: {args.output}")
    return args.output


if __name__ == "__main__":
    main()
