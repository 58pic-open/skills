#!/usr/bin/env python3
"""
千图网 (58pic) 配置初始化脚本
保存 API Key、默认模型、存放目录等到 ~/.58pic_config.json

配置项：
  api_key      - 千图 API Key（sk_...）
  output_dir   - 文件存放目录（搜索结果、下载素材、AI 生成图片、预览页面）
  base_url     - API 地址（通常无需修改）
  defaults.model - 默认 AI 做同款模型 ID
"""

import argparse
import json
import os

CONFIG_FILE = os.path.expanduser("~/.58pic_config.json")
DEFAULT_BASE_URL = "https://ai.58pic.com/api/"


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    os.chmod(CONFIG_FILE, 0o600)


def mask_key(key):
    if len(key) <= 12:
        return "sk_***"
    return key[:6] + "..." + key[-4:]


def check_needs_setup():
    """返回缺失的配置项列表，供 SKILL.md 引导用"""
    config = load_config()
    missing = []
    if not config.get("api_key"):
        missing.append("api_key")
    if not config.get("output_dir"):
        missing.append("output_dir")
    if not config.get("defaults", {}).get("model"):
        missing.append("default_model")
    return missing


def get_output_dir(fallback_cwd=True):
    """获取配置中的存放目录；若未配置且 fallback_cwd=True 则返回当前目录下 58pic_output"""
    config = load_config()
    d = config.get("output_dir", "")
    if d:
        return os.path.expanduser(d)
    if fallback_cwd:
        return os.path.join(os.getcwd(), "58pic_output")
    return ""


def main():
    parser = argparse.ArgumentParser(description="千图 API 配置初始化")
    parser.add_argument("--api-key",       help="千图 API Key（格式：sk_...）")
    parser.add_argument("--output-dir",    help="文件存放目录（下载素材、AI图片、预览页面）")
    parser.add_argument("--default-model", help="默认 AI 模型 ID（从 list_models.py 获取）")
    parser.add_argument("--base-url",      default=DEFAULT_BASE_URL,
                        help=f"API Base URL（默认: {DEFAULT_BASE_URL}）")
    parser.add_argument("--show",   action="store_true", help="显示当前配置（脱敏）")
    parser.add_argument("--check",  action="store_true", help="检查缺失项（返回 JSON 列表）")
    parser.add_argument("--reset",  action="store_true", help="清空所有配置")
    args = parser.parse_args()

    if args.reset:
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
            print("✅ 配置已清空")
        else:
            print("ℹ️  配置文件不存在")
        return

    if args.check:
        missing = check_needs_setup()
        print(json.dumps({"missing": missing, "config_file": CONFIG_FILE}))
        return

    config = load_config()

    if args.show:
        if config:
            display = config.copy()
            if "api_key" in display:
                display["api_key"] = mask_key(display["api_key"])
            print("📋 当前配置：")
            print(json.dumps(display, ensure_ascii=False, indent=2))
            effective_output = get_output_dir()
            if not config.get("output_dir"):
                print(f"\n💡 output_dir 未设置，将使用当前目录：{effective_output}")
        else:
            print("❌ 尚未配置，请运行:")
            print(f"   python3 init_config.py --api-key sk_your_key")
        return

    changed = False

    if args.api_key:
        if not args.api_key.startswith("sk_"):
            print("⚠️  警告：API Key 格式通常以 'sk_' 开头，请确认是否正确")
        config["api_key"] = args.api_key
        config["base_url"] = args.base_url or DEFAULT_BASE_URL
        changed = True
        print(f"✅ API Key 已保存：{mask_key(args.api_key)}")

    if args.output_dir:
        output_dir = os.path.abspath(os.path.expanduser(args.output_dir))
        config["output_dir"] = output_dir
        changed = True
        print(f"✅ 存放目录已设置：{output_dir}")

    if args.default_model:
        config.setdefault("defaults", {})["model"] = str(args.default_model)
        changed = True
        print(f"✅ 默认模型 ID 已设置：{args.default_model}")

    if changed:
        save_config(config)
        print(f"\n💾 配置已保存至：{CONFIG_FILE}")
    elif not args.show and not args.reset and not args.check:
        print("ℹ️  未提供任何参数。使用 --show 查看当前配置，--help 查看帮助。")


if __name__ == "__main__":
    main()
