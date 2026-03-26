#!/usr/bin/env python3
"""
千图网素材搜索脚本
API: POST https://ai.58pic.com/api/?r=open-platform/search-images
每页固定 36 条，页码范围 1-100
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

CONFIG_FILE = os.path.expanduser("~/.58pic_config.json")
SESSION_FILENAME = "session.json"
DEFAULT_OUTPUT_DIR = "./58pic_output"


def get_config_output_dir():
    """从全局配置文件读取 output_dir，未设置则返回空字符串"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("output_dir", "")
        except Exception:
            pass
    return ""


# 允许的 did 一级分类值（0 = 全部，不传参数）
VALID_DIDS = {
    0:  "全部",
    2:  "海报展板",
    3:  "电商淘宝",
    4:  "装饰装修",
    5:  "网页UI",
    6:  "音乐音效",
    7:  "3D素材",
    8:  "PPT模板",
    10: "背景",
    11: "免抠元素",
    12: "Excel模板",
    14: "简历模板",
    15: "Word模板",
    16: "社交媒体",
    17: "插画",
    40: "字库",
    41: "艺术字",
    53: "高清图片",
    56: "视频模板",
    57: "元素世界",
    60: "AI数字艺术",
    66: "品牌广告",
}


# ── Session helpers ──────────────────────────────────────────────────────────

def load_session(output_dir):
    session_file = os.path.join(output_dir, SESSION_FILENAME)
    if os.path.exists(session_file):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"output_dir": os.path.abspath(output_dir),
            "searches": [], "downloads": [], "ai_results": []}


def save_session(session, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    session_file = os.path.join(output_dir, SESSION_FILENAME)
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)
    return session_file


# ── API ──────────────────────────────────────────────────────────────────────

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
        except Exception:
            if error_body:
                print(f"   错误详情: {error_body[:200]}")
        if e.code == 401:
            print("   → API Key 无效，请重新配置")
        elif e.code == 429:
            print("   → 请求过于频繁或点数不足")
        elif e.code == 400:
            print("   → 参数错误（检查 did 是否合法、page 是否在 1-100 范围内）")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ 网络连接失败: {e.reason}")
        sys.exit(1)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="千图网素材搜索")
    parser.add_argument("--keyword", "-k", required=True, help="搜索关键词")
    parser.add_argument("--page", "-p", type=int, default=1, help="页码（1-100，默认 1）")
    parser.add_argument("--did", type=int, default=0,
                        help=f"一级分类 ID（0=全部，不传）。可选: {list(VALID_DIDS.keys())}")
    parser.add_argument("--ai-search", action="store_true",
                        help="使用 AI 向量搜索（适合描述性关键词）")
    _cfg_dir = get_config_output_dir() or DEFAULT_OUTPUT_DIR
    parser.add_argument("--output-dir", default=_cfg_dir,
                        help=f"输出目录（默认：配置文件或当前目录下的 58pic_output/，当前: {_cfg_dir}）")
    args = parser.parse_args()

    # 校验 page
    if not 1 <= args.page <= 100:
        print(f"❌ 页码必须在 1-100 范围内，当前: {args.page}")
        sys.exit(1)

    # 校验 did
    if args.did not in VALID_DIDS:
        print(f"❌ 无效的 did: {args.did}，允许值: {list(VALID_DIDS.keys())}")
        print(f"   对应分类: {VALID_DIDS}")
        sys.exit(1)

    config = load_config()

    search_type = "AI 向量" if args.ai_search else "关键词"
    did_name = VALID_DIDS.get(args.did, str(args.did))
    print(f"🔍 {search_type}搜索「{args.keyword}」，分类：{did_name}，第 {args.page} 页...")

    payload = {
        "keyword": args.keyword,
        "page": args.page,
        "ai_search": args.ai_search,
    }
    if args.did != 0:
        payload["did"] = args.did

    result = api_post(config, "open-platform/search-images", payload)

    if result.get("code") != 200:
        print(f"❌ 搜索失败: {result.get('msg', '未知错误')}")
        sys.exit(1)

    data = result.get("data", {})
    items = data.get("list", [])
    total_page = data.get("total_page", 1)
    suggestions = data.get("suggestions", [])

    # 准备输出目录
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # 保存搜索结果到项目目录（每次生成唯一文件名，避免覆盖历史）
    ts = time.strftime("%Y%m%d_%H%M%S")
    safe_kw = re.sub(r"[^\w\u4e00-\u9fff]", "_", args.keyword)[:20]
    results_file = os.path.join(output_dir, f"search_{safe_kw}_p{args.page}_{ts}.json")
    save_data = {
        "keyword": args.keyword,
        "page": args.page,
        "total_page": total_page,
        "did": args.did,
        "did_name": did_name,
        "ai_search": args.ai_search,
        "items": items,
        "search_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)

    # 更新 session.json
    session = load_session(output_dir)
    session_entry = {
        "keyword": args.keyword,
        "page": args.page,
        "total_page": total_page,
        "did_name": did_name,
        "ai_search": args.ai_search,
        "item_count": len(items),
        "results_file": results_file,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    session["searches"].insert(0, session_entry)
    session["searches"] = session["searches"][:20]  # 保留最近 20 次
    session_file = save_session(session, output_dir)

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

    print(f"\n📁 搜索结果已保存: {results_file}")
    print(f"📋 Session 文件: {session_file}")
    print("💡 告诉我您想下载哪个素材的 PID，或者用某个 PID 做同款")

    # 输出结构化结果供 SKILL.md 解析
    print(f"\n__SEARCH_RESULT__:{json.dumps({'results_file': results_file, 'session_file': session_file, 'output_dir': output_dir}, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
