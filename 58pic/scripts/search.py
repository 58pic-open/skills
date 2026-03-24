#!/usr/bin/env python3
"""
千图网素材搜索脚本
API: POST https://ai.58pic.com/api/?r=open-platform/search-images
每页固定 36 条，页码范围 1-100
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

CONFIG_FILE = os.path.expanduser("~/.58pic_config.json")
RESULTS_FILE = "/tmp/58pic_search_results.json"

# 允许的 kid 分类值
VALID_KIDS = {
    0: "全部",
    8: "办公",
    130: "免抠元素",
    275: "广告设计",
    276: "字体",
    668: "摄影图",
    735: "插画",
    743: "GIF动图",
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        print("❌ 未找到配置文件！请先运行：")
        print("   python3 init_config.py --api-key sk_your_key")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def api_post(config, route, payload):
    base_url = config.get("base_url", "https://ai.58pic.com/api/")
    api_key = config["api_key"]
    url = f"{base_url}?r={route}"

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "58pic-skill/1.0")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"❌ API 请求失败 (HTTP {e.code}): {e.reason}")
        try:
            err_data = json.loads(error_body)
            print(f"   错误详情: {err_data.get('msg', error_body)}")
        except:
            if error_body:
                print(f"   错误详情: {error_body[:200]}")
        if e.code == 401:
            print("   → API Key 无效，请重新配置")
        elif e.code == 429:
            print("   → 请求过于频繁或点数不足")
        elif e.code == 400:
            print("   → 参数错误（检查 kid 是否合法、page 是否在 1-100 范围内）")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ 网络连接失败: {e.reason}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="千图网素材搜索")
    parser.add_argument("--keyword", "-k", required=True, help="搜索关键词")
    parser.add_argument("--page", "-p", type=int, default=1, help="页码（1-100，默认 1）")
    parser.add_argument("--kid", type=int, default=0, help=f"一级分类 ID（0=全部）。可选: {list(VALID_KIDS.keys())}")
    parser.add_argument("--ai-search", action="store_true", help="使用 AI 向量搜索（适合描述性关键词）")
    parser.add_argument("--output", default=RESULTS_FILE, help="结果输出文件路径")
    args = parser.parse_args()

    # 校验 page
    if not 1 <= args.page <= 100:
        print(f"❌ 页码必须在 1-100 范围内，当前: {args.page}")
        sys.exit(1)

    # 校验 kid
    if args.kid not in VALID_KIDS:
        print(f"❌ 无效的 kid: {args.kid}，允许值: {list(VALID_KIDS.keys())}")
        print(f"   对应分类: {VALID_KIDS}")
        sys.exit(1)

    config = load_config()

    search_type = "AI 向量" if args.ai_search else "关键词"
    kid_name = VALID_KIDS.get(args.kid, str(args.kid))
    print(f"🔍 {search_type}搜索「{args.keyword}」，分类：{kid_name}，第 {args.page} 页...")

    payload = {
        "keyword": args.keyword,
        "page": args.page,
        "kid": args.kid,
        "ai_search": args.ai_search,
    }

    result = api_post(config, "open-platform/search-images", payload)

    if result.get("code") != 200:
        print(f"❌ 搜索失败: {result.get('msg', '未知错误')}")
        sys.exit(1)

    data = result.get("data", {})
    items = data.get("list", [])
    total_page = data.get("total_page", 1)
    suggestions = data.get("suggestions", [])

    # 保存结果
    save_data = {
        "keyword": args.keyword,
        "page": args.page,
        "total_page": total_page,
        "kid": args.kid,
        "kid_name": kid_name,
        "ai_search": args.ai_search,
        "items": items,
        "search_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)

    # 打印摘要
    print(f"\n✅ 搜索完成！第 {args.page}/{total_page} 页，本页 {len(items)} 条")

    if suggestions:
        print(f"💡 搜索建议: {', '.join(suggestions[:5])}")

    print("─" * 60)

    for i, item in enumerate(items[:12], 1):
        pid = item.get("pid", "N/A")
        title = (item.get("title") or item.get("keyword") or "无标题")[:35]
        preview_url = item.get("preview_url", "")
        preview_hint = "🖼️" if preview_url else "  "
        print(f"  {i:2}. {preview_hint} [{pid}] {title}")

    if len(items) > 12:
        print(f"  ... 还有 {len(items) - 12} 条，查看预览页面获取完整列表")

    if total_page > args.page:
        print(f"\n  📄 还有更多结果（共 {total_page} 页），加 --page {args.page + 1} 查看下一页")

    print(f"\n📁 完整结果已保存: {args.output}")
    print("💡 告诉我您想下载哪个素材的 PID，或者用某个 PID 做同款")


if __name__ == "__main__":
    main()
