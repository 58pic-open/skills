#!/usr/bin/env python3
"""
千图 AI 可用模型列表查询脚本
API: GET https://ai.58pic.com/api/?r=open-platform/available-models
无请求参数，需要 API Key
每类型最多返回 10 条模型（按 sort 降序）
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

CONFIG_FILE = os.path.expanduser("~/.58pic_config.json")
MODELS_CACHE_FILE = "/tmp/58pic_models.json"

MEDIA_TYPE_NAMES = {
    "image": "图片",
    "video": "视频",
    "music": "音乐",
    "three_d": "3D",
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        print("❌ 未找到配置文件！请先运行：")
        print("   python3 init_config.py --api-key sk_your_key")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_models(config):
    base_url = config.get("base_url", "https://ai.58pic.com/api/")
    api_key = config["api_key"]
    url = f"{base_url}?r=open-platform/available-models"

    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("User-Agent", "58pic-skill/1.0")

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"❌ 获取模型列表失败 (HTTP {e.code}): {e.reason}")
        if e.code == 401:
            print("   → API Key 无效，请重新配置")
            sys.exit(1)
        return None
    except Exception as e:
        print(f"⚠️  获取模型列表失败: {e}")
        return None


def format_capabilities(caps):
    """格式化模型能力摘要"""
    if not caps:
        return []
    info = []
    if caps.get("single_reference_supported"):
        info.append("支持单图垫图")
    if caps.get("multi_reference_supported"):
        max_ref = caps.get("multi_reference_max", "多")
        info.append(f"支持多图垫图(最多{max_ref}张)")
    max_num = caps.get("max_generate_num")
    if max_num:
        info.append(f"单次最多生成{max_num}张")
    if caps.get("custom_pixel_supported"):
        info.append("支持自定义尺寸")

    # 列出下拉选项
    for opt in (caps.get("select_options") or []):
        key = opt.get("submit_key", "")
        choices = opt.get("choices", [])
        if choices:
            labels = [c.get("label", c.get("value_english", "")) for c in choices[:6]]
            info.append(f"{opt.get('name', key)}: {' / '.join(labels)}")
    return info


def main():
    config = load_config()

    print("🤖 正在获取可用 AI 模型列表...\n")

    result = get_models(config)

    if not result or result.get("code") != 200:
        print("❌ 获取模型列表失败")
        sys.exit(1)

    data = result.get("data", {})
    is_member = data.get("is_member", False)
    models_by_type = data.get("models", {})

    member_str = "✅ 会员" if is_member else "❌ 非会员（部分模型不可用）"
    print(f"👤 账户状态：{member_str}\n")

    all_image_models = []

    for media_type, type_name in MEDIA_TYPE_NAMES.items():
        models = models_by_type.get(media_type, [])
        if not models:
            continue

        print(f"📂 {type_name}类模型（{len(models)} 个）：")
        print("─" * 60)

        for i, model in enumerate(models, 1):
            model_id = model.get("id")
            name = model.get("name", "未知模型")
            caps = model.get("capabilities") or {}

            print(f"  {i}. {name}")
            print(f"     ID: {model_id}")

            cap_info = format_capabilities(caps)
            for info in cap_info:
                print(f"     • {info}")

            if media_type == "image":
                all_image_models.append({
                    "id": model_id,
                    "name": name,
                    "capabilities": caps,
                })

        print()

    if not models_by_type:
        print("⚠️  未返回任何模型（可能账户无权限或接口配置问题）")

    # 保存模型缓存
    cache_data = {
        "is_member": is_member,
        "models": models_by_type,
        "image_models": all_image_models,
        "cached_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(MODELS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

    print(f"💾 模型列表已缓存至: {MODELS_CACHE_FILE}")

    # 显示当前配置
    defaults = config.get("defaults", {})
    default_model = defaults.get("model")
    if default_model:
        print(f"\n⭐ 当前默认模型 ID: {default_model}")
    else:
        if all_image_models:
            first_id = all_image_models[0]["id"]
            print(f"\n💡 推荐使用第一个图片模型 ID: {first_id}")
            print(f"   运行: python3 init_config.py --default-model {first_id}")


if __name__ == "__main__":
    main()
