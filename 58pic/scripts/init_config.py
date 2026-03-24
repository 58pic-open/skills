#!/usr/bin/env python3
"""
千图网 (58pic) 配置初始化脚本
保存 API Key 和默认偏好设置到 ~/.58pic_config.json

API Base URL: https://ai.58pic.com/api/
鉴权: Authorization: Bearer <api_key> 或 X-API-Key: <api_key>
"""

import argparse
import json
import os
import sys

CONFIG_FILE = os.path.expanduser("~/.58pic_config.json")
DEFAULT_BASE_URL = "https://ai.58pic.com/api/"


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    os.chmod(CONFIG_FILE, 0o600)  # 仅用户可读


def mask_key(key):
    if len(key) <= 12:
        return "sk_***"
    return key[:6] + "..." + key[-4:]


def main():
    parser = argparse.ArgumentParser(description="千图 API 配置初始化")
    parser.add_argument("--api-key", help="千图 API Key（格式：sk_...）")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"API Base URL（默认: {DEFAULT_BASE_URL}）")
    parser.add_argument("--default-model", help="默认 AI 模型 ID（从 list_models.py 获取）")
    parser.add_argument("--show", action="store_true", help="显示当前配置（脱敏）")
    parser.add_argument("--reset", action="store_true", help="清空所有配置")
    args = parser.parse_args()

    if args.reset:
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
            print("✅ 配置已清空")
        else:
            print("ℹ️  配置文件不存在")
        return

    config = load_config()

    if args.show:
        if config:
            display = config.copy()
            if "api_key" in display:
                display["api_key"] = mask_key(display["api_key"])
            print("📋 当前配置：")
            print(json.dumps(display, ensure_ascii=False, indent=2))
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
        print(f"   Base URL: {config['base_url']}")

    if args.default_model:
        config.setdefault("defaults", {})["model"] = str(args.default_model)
        changed = True
        print(f"✅ 默认模型 ID 已设置：{args.default_model}")

    if changed:
        save_config(config)
        print(f"\n💾 配置已保存至：{CONFIG_FILE}")
        print("✨ 您现在可以使用 58pic 素材搜索和 AI 做同款功能了！")
    elif not args.show and not args.reset:
        print("ℹ️  未提供任何参数。使用 --show 查看当前配置，--help 查看帮助。")


if __name__ == "__main__":
    main()
