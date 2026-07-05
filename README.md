# brand-pixel · 品牌像素画工厂

> Turn your photos into brand-consistent pixel art — with your own color palette.
> 把你的照片转成跟品牌风格一致的像素画。

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python)](https://python.org)
[![Pyxelate](https://img.shields.io/badge/Pyxelate-2.1-FF6B35)](https://github.com/sedthh/pyxelate)
[![Gradio](https://img.shields.io/badge/Gradio-6-FFB000)](https://gradio.app)

---

## Overview · 概览

**brand-pixel** is a tool that converts photos into pixel art using a custom brand color palette. Designed for indie-web creators, personal bloggers, and anyone who wants their site images to share a unified style.

核心思路：输入一张照片 + 一组品牌色 → 输出跟品牌风格一致的像素画。

### Three ways to choose colors · 三种配色方式

| Method | Description |
|--------|-------------|
| 🎨 **Preset styles** · 预设风格 | Pick from 11 built-in color schemes |
| 🖌️ **From reference image** · 从参考图提取 | Upload any image → auto-extract dominant colors → save as preset |
| ✏️ **Custom hex** · 自定义颜色 | Type hex colors directly |

### Two interfaces · 两种使用方式

- **Web UI** (Gradio) — drag & drop, visual, no coding
- **CLI** — batch processing, scripting, automation

---

## Quick Start · 快速开始

```bash
# Install dependencies · 安装依赖
pip install -r requirements.txt

# Launch web interface · 启动Web界面
python app.py
# → http://127.0.0.1:7860
```

---

## Web Interface · Web 界面

```bash
python app.py
```

Two tabs:

### 🎨 Style Workshop · 风格工坊

1. Upload a **reference image** (logo, sticker, any inspiration photo)
2. Click "提取配色" — auto-extracts 8 dominant colors
3. Edit colors if needed, type a name, click "保存预设"
4. Your preset is saved to `custom_presets.json` (persists across restarts)

### 🖼️ Pixel Art Generator · 像素画生成

1. Upload your **target photo**
2. Select a preset (built-in + your custom ones)
3. Adjust `factor` (pixel block size) and `dither`
4. Generate and download

---

## CLI Usage · 命令行用法

### Single image · 单张图片

```bash
# Preset style · 预设风格
python cli.py photo.jpg --style "品牌暗调"

# Custom colors · 自定义颜色
python cli.py photo.jpg --colors "#93134a,#3c2866"

# Extract from reference · 从参考图提取
python cli.py photo.jpg --from-image logo.png
```

### Compare mode · 对比模式

```bash
python cli.py photo.jpg --style "品牌暗调" --compare
```
Generates a side-by-side comparison: original | pixel art.

### Batch processing · 批量处理

```bash
python cli.py --folder ./photos/ --style "暮色" --gallery
```

Automatically generates an `index.html` gallery page.

### Auto factor · 自适应 factor

When `--factor` is omitted, the tool automatically calculates the optimal pixel block size based on image dimensions (target: ~400px on the short side).

### List all presets · 查看所有预设

```bash
python cli.py --list-styles
```

---

## Parameters · 参数说明

| Flag | Default | Description |
|------|---------|-------------|
| `--style / -s` | — | Preset style name |
| `--colors / -c` | — | Hex colors, comma-separated |
| `--from-image` | — | Extract colors from reference image |
| `--factor` | auto | Pixel block size (higher = chunkier) |
| `--dither` | none | Dithering: none / naive / floyd / atkinson |
| `--upscale` | 1 | Output scale multiplier |
| `--output / -o` | ./output/ | Output directory |
| `--compare` | off | Side-by-side comparison mode |
| `--gallery` | off | Generate index.html gallery after batch |
| `--show-palette` | off | Output palette swatch card |
| `--extract` | — | Extract dominant colors from an image |

---

## Built-in Presets · 内置预设风格 (11)

| # | Name · 名称 | Vibe |
|---|-------------|------|
| 1 | **品牌暗调** | Brand dark — your brand colors (#93134a + #3c2866) with white/black |
| 2 | **琥珀终端** | Amber terminal — retro amber monitor glow |
| 3 | **绿幕终端** | Green terminal — classic green phosphor |
| 4 | **暮色** | Dusk — sunset gradient |
| 5 | **海雾** | Sea fog — misty coastal morning |
| 6 | **焦糖** | Caramel — deep roasted coffee |
| 7 | **紫夜** | Purple night — late-night purple sky |
| 8 | **黑白摄影** | B&W — classic black & white film |
| 9 | **薄荷** | Mint — cool mint green |
| 10 | **锈红** | Rust — iron and clay |
| 11 | **雾蓝** | Fog blue — hazy blue-gray |

---

## Project Structure · 项目结构

```
F:\brand-pixel\
├── brand_pixel.py     Core engine · 核心引擎
├── cli.py             CLI entry (batch/compare/gallery) · 命令行入口
├── app.py             Gradio web UI · Web 界面
├── config.py          Built-in presets · 内置预设风格
├── custom_presets.py  Custom preset storage · 自定义预设存储
├── custom_presets.json  Your saved presets · 你保存的预设
├── requirements.txt   Dependencies · 依赖
├── ──README.md         This file · 本文件
└── photos/            Your images · 你的图片（gitignored）
```

---

## How It Works · 工作原理

Under the hood, brand-pixel uses:

1. **Pyxelate** ([sedthh/pyxelate](https://github.com/sedthh/pyxelate)) — an improved pixel art downsampling algorithm with palette transfer, extended from scikit-learn transformers
2. **KMeans clustering** (scikit-learn) — for auto-extracting dominant colors from reference images
3. **Gradio** — for the web interface

The pipeline:
```
Input image → Downsample via Pyxelate → Map to brand palette → Dither → Output
```

The **7-color brand palette** (5 brand colors + white + black) solves the common "color bleeding" issue where white backgrounds get tinted by similar brand colors.

---

## License · 许可证

MIT — free for personal and commercial use.

---

*Built with ❤️ for the indie-web community.*
