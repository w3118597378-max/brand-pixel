"""
custom_presets.py - 用户自定义预设风格存储
"""
import os
import json
from datetime import datetime

_PRESETS_FILE = os.path.join(os.path.dirname(__file__), "custom_presets.json")


def _load_all():
    """加载所有自定义预设"""
    if not os.path.exists(_PRESETS_FILE):
        return {}
    try:
        with open(_PRESETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_all(data):
    """覆盖写入所有自定义预设"""
    with open(_PRESETS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_custom():
    """返回 {名称: {colors, description}}"""
    return _load_all()


def list_custom_names():
    """返回所有自定义预设的名称列表"""
    return sorted(_load_all().keys())


def save_preset(name, colors, description="", source=""):
    """
    保存一个自定义预设
    name: 预设名称
    colors: Hex颜色列表
    description: 描述
    source: 来源文件名
    """
    data = _load_all()
    data[name] = {
        "colors": colors,
        "description": description or f"从 {source} 提取" if source else "自定义",
        "source": source,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    _save_all(data)
    return name


def delete_preset(name):
    """删除一个自定义预设"""
    data = _load_all()
    if name in data:
        del data[name]
        _save_all(data)
        return True
    return False


def get_preset(name):
    """获取单个自定义预设"""
    data = _load_all()
    return data.get(name)
