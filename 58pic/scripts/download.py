#!/usr/bin/env python3
"""
千图网素材下载脚本
API: GET/POST https://ai.58pic.com/api/?r=open-platform/image-download
参数: pid
返回: preview_url, download_url (临时签名，默认 3600s 有效)
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

CONFIG_FILE = os.path.expanduser("~/.58pic_config.json")
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


# ── API ──────────────────────────────────────────────────────────────────────

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print("❌ 未找到配置文件！请先运行：")
        print("   python3 init_config.py --api-key sk_your_key")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_download_info(config, pid):
    base_url = config.get("base_url", "https://ai.58pic.com/api/")
    api_key = config["api_key"]

    params = urllib.parse.urlencode({"r": "open-platform/image-download", "pid": str(pid)})
    url = f"{base_url}?{params}"

    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("User-Agent", "58pic-skill/1.0")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"❌ 获取下载信息失败 (HTTP {e.code}): {e.reason}")
        if e.code == 400:
            print("   → 素材不存在或缺少缓存（宽高信息未就绪）")
        elif e.code == 401:
            print("   → API Key 无效，请重新配置")
        elif e.code == 403:
            print("   → 权限不足（账户余额不足或无下载权限）")
        elif e.code == 429:
            print("   → 点数不足或触发日上限，请升级会员或明日再试")
        try:
            err_data = json.loads(error_body)
            print(f"   错误详情: {err_data.get('msg', error_body)}")
        except Exception:
            pass
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ 网络连接失败: {e.reason}")
        sys.exit(1)


def download_file(download_url, output_path):
    """下载文件并显示进度"""
    req = urllib.request.Request(download_url)
    req.add_header("User-Agent", "58pic-skill/1.0")

    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 32768

            with open(output_path, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = downloaded / total_size * 100
                        print(f"\r   ⬇️  {pct:.0f}% ({downloaded//1024}KB / {total_size//1024}KB)", end="", flush=True)

        elapsed = time.time() - start_time
        print(f"\n✅ 下载完成！({downloaded//1024}KB，{elapsed:.1f}s)")
        return True
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return False


def main():
    parser = argparse.ArgumentParser(description="千图网素材下载（扣 1 点）")
    parser.add_argument("--pid", required=True, help="千图素材 PID")
    _cfg_dir = get_config_output_dir() or DEFAULT_OUTPUT_DIR
    parser.add_argument("--output-dir", default=_cfg_dir,
                        help=f"下载目标目录（默认：{_cfg_dir}）")
    parser.add_argument("--preview-only", action="store_true", help="仅获取预览图 URL，不下载高清图")
    args = parser.parse_args()

    output_dir = os.path.abspath(args.output_dir)
    config = load_config()

    print(f"📦 获取素材 {args.pid} 的下载信息...（将扣 1 点）")
    result = get_download_info(config, args.pid)

    if result.get("code") != 200:
        print(f"❌ 失败: {result.get('msg', '未知错误')}")
        sys.exit(1)

    data = result.get("data", {})
    preview_url = data.get("preview_url", "")
    download_url = data.get("download_url", "")
    width = data.get("width", "")
    height = data.get("height", "")

    print(f"   PID: {args.pid}  尺寸: {width}×{height}")

    if args.preview_only or not download_url:
        print(f"🖼️  预览图 URL: {preview_url}")
        return

    os.makedirs(output_dir, exist_ok=True)

    # 从 URL 推断扩展名
    url_path = download_url.split("?")[0].split("/")[-1]
    if "." in url_path:
        filename = f"58pic_{args.pid}_{url_path}"
    else:
        filename = f"58pic_{args.pid}.jpg"

    output_path = os.path.join(output_dir, filename)

    print(f"⬇️  正在下载: {filename}")
    success = download_file(download_url, output_path)

    if success:
        file_size = os.path.getsize(output_path)
        print(f"📁 文件保存至: {output_path} ({file_size//1024}KB)")

        # 更新 session.json
        session = load_session(output_dir)
        session["downloads"].append({
            "pid": str(args.pid),
            "filename": filename,
            "path": output_path,
            "preview_url": preview_url,
            "width": str(width),
            "height": str(height),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        session_file = save_session(session, output_dir)

        result_info = {
            "success": True,
            "pid": args.pid,
            "filename": filename,
            "output_path": output_path,
            "preview_url": preview_url,
            "session_file": session_file,
            "output_dir": output_dir,
        }
        print(f"📋 Session 已更新: {session_file}")
        print(f"\n__DOWNLOAD_RESULT__:{json.dumps(result_info, ensure_ascii=False)}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
