"""
config.py — brand-pixel 预设风格配置
你以后加/改风格只改这个文件就行

每条风格包含：
  - name: 中文名称
  - colors: Hex颜色列表（建议 5~8 色）
  - description: 灵感来源说明
"""
import os
from custom_presets import list_custom, get_preset as get_custom_preset

PRESETS = [
    {
        "name": "品牌暗调",
        "colors": ["#93134a", "#3c2866", "#cf5e5e", "#9185cf", "#fff0e0", "#ffffff", "#111111"],
        "description": "你的品牌色 (#93134a 暗红 + #3c2866 深紫)，加白/黑防底色染色"
    },
    {
        "name": "琥珀终端",
        "colors": ["#1a0a00", "#ffb000", "#ff8c00", "#ffd700", "#2a1500"],
        "description": "老式琥珀色显示器"
    },
    {
        "name": "绿幕终端",
        "colors": ["#0a0a0a", "#00ff41", "#008f11", "#ffffff", "#383838"],
        "description": "经典绿色终端"
    },
    {
        "name": "暮色",
        "colors": ["#1a0a2e", "#e94560", "#f5a623", "#2d1b4e", "#ffd6a5"],
        "description": "日落晚霞渐变"
    },
    {
        "name": "海雾",
        "colors": ["#1a2a3a", "#4a7a8a", "#8ab4c8", "#d4e8f0", "#2a4a5a"],
        "description": "雾蒙蒙的海岸清晨"
    },
    {
        "name": "焦糖",
        "colors": ["#2a1a0a", "#8b5e3c", "#d4a574", "#f5deb3", "#3a2510"],
        "description": "深度烘焙咖啡色系"
    },
    {
        "name": "紫夜",
        "colors": ["#0a001a", "#3a1a5a", "#6b3fa0", "#b08ad0", "#1a0a2a"],
        "description": "深夜紫色天空"
    },
    {
        "name": "黑白摄影",
        "colors": ["#000000", "#333333", "#666666", "#999999", "#FFFFFF"],
        "description": "经典黑白胶片"
    },
    {
        "name": "薄荷",
        "colors": ["#0a1a0a", "#2a5a3a", "#5a9a6a", "#8ac48a", "#e8f5e8"],
        "description": "清凉薄荷绿"
    },
    {
        "name": "锈红",
        "colors": ["#1a0a0a", "#5a1a0a", "#8b3a1a", "#c45a2a", "#f5d4b0"],
        "description": "铁锈和陶土"
    },
    {
        "name": "雾蓝",
        "colors": ["#0a1a2a", "#2a4a6a", "#5a7a9a", "#8aaac4", "#d4e4f0"],
        "description": "雾霾蓝灰调"
    },
]


def get_style_names():
    """返回所有预设风格名称列表（内置 + 自定义）"""
    builtin = [p["name"] for p in PRESETS]
    custom = list_custom().keys()
    return builtin + sorted(custom)


def get_style(name):
    """按名称查找预设风格（内置 + 自定义）"""
    for p in PRESETS:
        if p["name"] == name:
            return p
    custom = get_custom_preset(name)
    if custom:
        return {
            "name": name,
            "colors": custom["colors"],
            "description": custom.get("description", "自定义风格"),
        }
    raise ValueError(f"未知风格 '{name}'，可选：{', '.join(get_style_names())}")


def list_styles():
    """打印所有风格（内置 + 自定义）"""
    builtin_count = len(PRESETS)
    print(f"内置风格（{builtin_count}种）：")
    for p in PRESETS:
        swatches = " ".join(f"\033[48;2;{int(c[1:3],16)};{int(c[3:5],16)};{int(c[5:7],16)}m  \033[0m" for c in p["colors"])
        print(f"  {p['name']:8s}  {swatches}  {p['description']}")
    custom = list_custom()
    if custom:
        print(f"\n自定义风格（{len(custom)}种）：")
        for name, data in sorted(custom.items()):
            swatches = " ".join(f"\033[48;2;{int(c[1:3],16)};{int(c[3:5],16)};{int(c[5:7],16)}m  \033[0m" for c in data["colors"])
            print(f"  {name:8s}  {swatches}  {data.get('description', '')}")
