#!/usr/bin/env python3
"""
千图 AI 做同款脚本
API: POST https://ai.58pic.com/api/?r=open-platform/same-style
轮询: GET/POST https://ai.58pic.com/api/?r=open-platform/same-style-status

必须提供至少一种参考图来源（--ref-pid / --ref-url / --ref-image-path）
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

CONFIG_FILE = os.path.expanduser("~/.58pic_config.json")
MODELS_CACHE_FILE = "/tmp/58pic_models.json"
SESSION_FILENAME = "session.json"
DEFAULT_OUTPUT_DIR = "./58pic_output"


def get_config_output_dir():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("output_dir", "")
        except Exception:
            pass
    return ""


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


def load_config():
    if not os.path.exists(CONFIG_FILE):
        print("❌ 未找到配置文件！请先运行：")
        print("   python3 init_config.py --api-key sk_your_key")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def api_call(config, method, route, payload=None, use_get_params=False):
    base_url = config.get("base_url", "https://ai.58pic.com/api/")
    api_key = config["api_key"]

    if use_get_params and payload:
        params = {"r": route}
        params.update(payload)
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url)
    else:
        url = f"{base_url}?r={route}"
        data = json.dumps(payload).encode("utf-8") if payload else None
        req = urllib.request.Request(url, data=data, method=method)

    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "58pic-skill/1.0")

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"❌ API 请求失败 (HTTP {e.code}): {e.reason}")
        if e.code == 401:
            print("   → API Key 无效，请重新配置")
        elif e.code == 403:
            print("   → 权限不足（账户余额不足）")
        elif e.code == 400:
            print("   → 参数错误")
        elif e.code == 429:
            print("   → 点数不足或触发日上限")
        try:
            err_data = json.loads(error_body)
            msg = err_data.get("msg", error_body)
            remaining = err_data.get("data", {}).get("remaining", "") if isinstance(err_data.get("data"), dict) else ""
            print(f"   错误详情: {msg}")
            if remaining:
                print(f"   剩余点数: {remaining}")
        except Exception:
            if error_body:
                print(f"   错误详情: {error_body[:300]}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ 网络连接失败: {e.reason}")
        sys.exit(1)


def get_ref_url_from_session(pid, output_dir):
    """从 session.json 或搜索结果缓存中找到素材的预览 URL"""
    # 优先从 session.json 的搜索记录里找
    session = load_session(output_dir)
    for search_entry in session.get("searches", []):
        results_file = search_entry.get("results_file", "")
        if results_file and os.path.exists(results_file):
            try:
                with open(results_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                for item in cache.get("items", []):
                    if str(item.get("pid")) == str(pid):
                        url = item.get("preview_url") or item.get("download_url")
                        if url:
                            return url
            except Exception:
                pass
    return None


def image_to_base64(image_path):
    """将本地图片转为 base64"""
    with open(image_path, "rb") as f:
        data = f.read()
    ext = os.path.splitext(image_path)[1].lower().strip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{base64.b64encode(data).decode('utf-8')}"


def is_api_ok(result):
    """开放平台部分接口成功为 code=200，部分为 code=1 + msg=success。"""
    c = result.get("code")
    if c in (200, 1):
        return True
    msg = (result.get("msg") or "").lower()
    return msg == "success"


def poll_task_status(config, ai_id, max_wait=180, interval=5):
    """轮询任务状态，status=3 为成功"""
    elapsed = 0
    print(f"⏳ 任务已提交（ai_id: {ai_id}），等待生成中", end="", flush=True)

    while elapsed <= max_wait:
        result = api_call(config, "GET", "open-platform/same-style-status",
                          payload={"ai_id": str(ai_id)}, use_get_params=True)

        if not is_api_ok(result):
            print(f"\n❌ 查询任务失败: {result.get('msg', '未知错误')}")
            sys.exit(1)

        data = result.get("data", {})
        status = data.get("status")

        if status == 3:  # 成功
            print(f"\n✅ 生成完成！（用时 {elapsed}s）")
            return data.get("details", [])
        elif status in (2, 4, 5):  # 失败状态（2=失败, 4=失败, 5=失败）
            print(f"\n❌ 生成失败（status={status}）")
            sys.exit(1)

        dots = "." * ((elapsed // interval % 4) + 1)
        print(f"\r⏳ 任务已提交（ai_id: {ai_id}），等待生成中{dots:<4} ({elapsed}s)", end="", flush=True)
        time.sleep(interval)
        elapsed += interval

    print(f"\n⏰ 等待超时（{max_wait}s），任务 ID: {ai_id}")
    print("💡 稍后可手动查询状态：")
    print(f"   curl 'https://ai.58pic.com/api/?r=open-platform/same-style-status&ai_id={ai_id}' -H 'Authorization: Bearer YOUR_KEY'")
    sys.exit(1)


def download_result_image(url, output_path):
    """下载生成的图片（临时签名 URL）"""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "58pic-skill/1.0")
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            with open(output_path, "wb") as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"❌ 图片下载失败: {e}")
        return False


def get_image_ext_from_url(url):
    """从 URL 推断图片格式"""
    path = url.split("?")[0].lower()
    for ext in ["png", "jpg", "jpeg", "webp", "gif", "mp4"]:
        if f".{ext}" in path:
            return ext
    return "jpg"


def main():
    parser = argparse.ArgumentParser(description="千图 AI 做同款图片生成")
    parser.add_argument("--prompt", "-p", help="创意描述 / 提示词（可选，默认「开放平台同款」）")
    parser.add_argument("--model", "-m", help="模型 ID（先用 list_models.py 查询）")
    parser.add_argument("--ref-pid", help="参考千图素材 PID（做同款主要方式）")
    parser.add_argument("--ref-url", help="参考图片 URL（公网可访问）")
    parser.add_argument("--ref-urls", nargs="+", help="多张参考图片 URL 列表（多图做同款）")
    parser.add_argument("--ref-image-path", help="本地参考图片路径（将转为 base64 上传，≤8MB）")
    parser.add_argument("--generate-nums", type=int, default=1, help="生成张数（1-16，默认 1）")
    _cfg_dir = get_config_output_dir() or DEFAULT_OUTPUT_DIR
    parser.add_argument("--output-dir", default=_cfg_dir,
                        help=f"输出目录（默认：{_cfg_dir}）")
    parser.add_argument("--max-wait", type=int, default=180, help="最长等待秒数（默认 180）")
    parser.add_argument(
        "--aspect-id",
        type=int,
        default=None,
        help="比例选项 ID（见 list_models 缓存中 select_options，如全能香蕉2.0 的 16:9 为 2）",
    )
    args = parser.parse_args()

    output_dir = os.path.abspath(args.output_dir)
    config = load_config()
    defaults = config.get("defaults", {})

    # 校验至少有一种参考来源
    if not any([args.ref_pid, args.ref_url, args.ref_urls, args.ref_image_path]):
        print("❌ 必须提供至少一种参考来源：")
        print("   --ref-pid PID        千图素材 PID")
        print("   --ref-url URL        参考图片 URL")
        print("   --ref-urls URL1 URL2 多张参考图片")
        print("   --ref-image-path     本地图片路径")
        sys.exit(1)

    # 获取模型 ID
    model = args.model or defaults.get("model")
    model_name = ""
    if not model:
        # 自动从 API 获取排序第一的模型
        print("ℹ️  未配置默认模型，自动获取排序最高的可用模型...")
        models_result = api_call(config, "GET", "open-platform/available-models")
        if is_api_ok(models_result):
            image_models = models_result.get("data", {}).get("models", {}).get("image", [])
            if image_models:
                first = image_models[0]
                model = str(first["id"])
                model_name = first.get("name", "")
                print(f"   自动选择: {model_name}（ID: {model}）")
        if not model:
            print("❌ 无法获取可用模型，请手动指定：")
            print("   python3 init_config.py --default-model 模型ID")
            print("   或在命令行加 --model 模型ID")
            sys.exit(1)
    else:
        # 尝试从缓存中获取模型名称
        if os.path.exists(MODELS_CACHE_FILE):
            try:
                with open(MODELS_CACHE_FILE, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                for m in cache.get("image_models", cache.get("models", {}).get("image", [])):
                    if str(m.get("id")) == str(model):
                        model_name = m.get("name", "")
                        break
            except Exception:
                pass

    prompt = args.prompt or "参考当前作品的风格，重新生成一张"
    generate_nums = max(1, min(16, args.generate_nums))

    print(f"🎨 千图 AI 做同款")
    print(f"   模型: {model_name or model}（ID: {model}）" if model_name else f"   模型 ID: {model}")
    print(f"   描述: {prompt[:80]}")
    print(f"   生成张数: {generate_nums}")

    # 构造请求体
    payload = {
        "media_type": "image",
        "model": str(model),
        "generate_nums": generate_nums,
    }

    # 处理参考来源
    if args.ref_pid:
        print(f"   参考来源: 千图素材 PID {args.ref_pid}")
        payload["picid"] = str(args.ref_pid)

        # 从 session.json 的搜索记录获取预览 URL
        cached_url = get_ref_url_from_session(args.ref_pid, output_dir)
        if cached_url:
            print(f"   参考图预览 URL: {cached_url[:60]}...")
            payload["reference_image_urls"] = [cached_url]
            payload["reference_image_url"] = ""
        else:
            print("   ⚠️  未在 session 记录中找到该 PID 的预览 URL")
            print("   建议先搜索该素材获取预览图")
            payload["reference_image_url"] = ""
            payload["reference_image_urls"] = []

    elif args.ref_urls:
        print(f"   参考来源: {len(args.ref_urls)} 张图片 URL")
        payload["reference_image_url"] = ""
        payload["reference_image_urls"] = args.ref_urls

    elif args.ref_url:
        print(f"   参考来源: 单图 URL")
        payload["reference_image_url"] = args.ref_url

    elif args.ref_image_path:
        print(f"   参考来源: 本地图片 {args.ref_image_path}")
        if not os.path.exists(args.ref_image_path):
            print(f"❌ 文件不存在: {args.ref_image_path}")
            sys.exit(1)
        file_size = os.path.getsize(args.ref_image_path)
        if file_size > 8 * 1024 * 1024:
            print(f"❌ 图片文件过大（{file_size//1024//1024}MB），上限 8MB")
            sys.exit(1)
        payload["image_base64"] = image_to_base64(args.ref_image_path)

    payload["prompt"] = prompt
    payload["ai_title"] = prompt
    if args.aspect_id is not None:
        payload["Aspect"] = args.aspect_id
        print(f"   比例选项 Aspect ID: {args.aspect_id}")

    print("\n📤 正在提交做同款任务...")
    result = api_call(config, "POST", "open-platform/same-style", payload)

    if not is_api_ok(result):
        print(f"❌ 提交失败: {result.get('msg', '未知错误')}")
        sys.exit(1)

    raw_data = result.get("data")
    if isinstance(raw_data, list) and raw_data:
        data = raw_data[0] if isinstance(raw_data[0], dict) else {}
    elif isinstance(raw_data, dict):
        data = raw_data
    else:
        data = {}
    ai_id = data.get("ai_id")
    task_id = data.get("task_id")

    if not ai_id:
        print(f"❌ 未获取到任务 ID，响应: {json.dumps(data, ensure_ascii=False)}")
        sys.exit(1)

    print(f"✅ 任务已提交！ai_id={ai_id}, task_id={task_id}")

    # 轮询等待完成
    details = poll_task_status(config, ai_id, max_wait=args.max_wait)

    if not details:
        print("⚠️  任务已完成但无结果详情")
        sys.exit(1)

    # 下载生成的图片
    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    downloaded_files = []

    for i, detail in enumerate(details):
        # 接口可能返回整数 3 或字符串 "3"
        if str(detail.get("status")) != "3":
            continue

        img_url = detail.get("download_url") or detail.get("preview_url") or detail.get("image_url")
        if not img_url:
            continue

        ext = get_image_ext_from_url(img_url)
        filename = f"58pic_ai_{timestamp}_{i+1}.{ext}"
        output_path = os.path.join(output_dir, filename)

        print(f"⬇️  下载生成图片 {i+1}/{len(details)}: {filename}")
        print(f"   宽高: {detail.get('width', '?')}×{detail.get('height', '?')}")

        if download_result_image(img_url, output_path):
            file_size = os.path.getsize(output_path)
            print(f"   已保存: {output_path} ({file_size//1024}KB)")
            downloaded_files.append(output_path)
        else:
            print(f"   ⚠️  下载失败，图片 URL（临时有效）: {img_url}")

    if downloaded_files:
        print(f"\n🎉 成功下载 {len(downloaded_files)} 张图片！")

        # 更新 session.json
        session = load_session(output_dir)
        session["ai_results"].append({
            "ai_id": str(ai_id),
            "model": model,
            "prompt": prompt,
            "ref_pid": args.ref_pid or "",
            "files": downloaded_files,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        session_file = save_session(session, output_dir)

        print(f"📋 Session 已更新: {session_file}")

        result_info = {
            "success": True,
            "ai_id": str(ai_id),
            "model": model,
            "prompt": prompt,
            "files": downloaded_files,
            "session_file": session_file,
            "output_dir": output_dir,
        }
        print(f"\n__GENERATE_RESULT__:{json.dumps(result_info, ensure_ascii=False)}")
    else:
        print("\n⚠️  没有成功下载的图片")
        sys.exit(1)


if __name__ == "__main__":
    main()
