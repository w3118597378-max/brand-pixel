#!/usr/bin/env python3
"""
cli.py — brand-pixel 命令行入口（Phase 3 增强版）

用法：
  python cli.py photo.jpg --style "品牌暗调"
  python cli.py photo.jpg --colors "#93134a,#3c2866"
  python cli.py photo.jpg --from-image ref.png
  python cli.py --folder ./photos/ --style "暮色" --gallery
  python cli.py --folder ./photos/ --compare --factor 8
  python cli.py --list-styles
"""
import argparse
import os
import sys
from glob import glob
from pathlib import Path

from config import get_style_names, list_styles
from brand_pixel import BrandPixel


def find_images(folder):
    """在文件夹里找所有图片（大小写不敏感，去重）"""
    exts = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp", "*.JPG", "*.JPEG", "*.PNG", "*.BMP", "*.WEBP"]
    sources = set()
    for ext in exts:
        for f in glob(os.path.join(folder, ext)):
            sources.add(os.path.normpath(f))
    return sorted(sources)


def suggest_factor(image_path):
    """根据图片尺寸建议合适的 factor
    原则：输出像素画短边 ≈ 300~500px 之间
    """
    try:
        from skimage import io
        img = io.imread(image_path)
        h, w = img.shape[:2]
        short_side = min(h, w)
        # 目标短边 400px 左右
        target = 400
        factor = max(2, short_side // target)
        return factor
    except Exception:
        return 8  # 失败用默认值


def parse_args():
    parser = argparse.ArgumentParser(
        description="brand-pixel — 品牌像素画工厂",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cli.py photo.jpg --style "品牌暗调"
  python cli.py photo.jpg --colors "#93134a,#3c2866" --factor 10
  python cli.py photo.jpg --from-image ref.png --dither floyd
  python cli.py --folder ./photos/ --style "暮色" --factor 8
  python cli.py --folder ./photos/ --gallery              ← 批量+画廊
  python cli.py photo.jpg --compare                       ← 对比模式
  python cli.py --list-styles
        """,
    )

    # 输入（三选一组）
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--input", "-i", help="单张图片路径")
    group.add_argument("--folder", "-f", help="批量处理整个文件夹")

    # 也支持位置参数
    parser.add_argument("positional_input", nargs="?", help="图片路径（位置参数）")

    # 配色方式
    parser.add_argument("--colors", "-c", help="直接传Hex颜色，逗号分隔，例: #93134a,#3c2866")
    parser.add_argument("--style", "-s", help=f"预设风格，可选：{', '.join(get_style_names())}")
    parser.add_argument("--from-image", help="从参考图提取颜色")

    # Phase 3 增强参数
    parser.add_argument("--factor", type=int, default=0,
                        help="像素块大小（默认0=自适应，大=粗犷，小=精细）")
    parser.add_argument("--auto-factor", action="store_true", default=True,
                        help="根据图片尺寸自动选择 factor（默认开启，设 --factor 时关闭）")
    parser.add_argument("--dither", choices=["none", "naive", "floyd", "atkinson"],
                        default="none", help="抖动类型（默认none）")
    parser.add_argument("--upscale", type=int, default=1, help="输出放大倍数（默认1）")
    parser.add_argument("--palette", type=int, default=8, help="自动取色时的色数（默认8）")
    parser.add_argument("--n-colors", type=int, default=5, help="从参考图提取的主色数量（默认5）")

    # 输出
    parser.add_argument("--output", "-o", default="./output/", help="输出目录（默认./output/）")
    parser.add_argument("--show-palette", action="store_true", help="输出时附一张调色板色卡")

    # === Phase 3 新增 ===
    parser.add_argument("--gallery", action="store_true",
                        help="批量处理后生成 index.html 画廊页面")
    parser.add_argument("--compare", action="store_true",
                        help="生成原图 vs 像素画 左右对比图")
    parser.add_argument("--progress", action="store_true", default=True,
                        help="显示进度条（默认开启）")

    # 工具
    parser.add_argument("--list-styles", action="store_true", help="列出所有预设风格")
    parser.add_argument("--extract", help="从指定图片提取主色并打印")

    return parser.parse_args()


def pick_color_mode(bp, args, src):
    """根据参数给 BrandPixel 选择配色方式"""
    if args.style:
        bp.with_style(args.style)
    elif args.colors:
        colors = [c.strip() for c in args.colors.split(",")]
        bp.with_colors(colors)
    elif args.from_image:
        bp.from_image(args.from_image, n_colors=args.n_colors)
    else:
        # 默认：自动取色
        from brand_pixel import extract_palette
        auto_colors = extract_palette(src, n_colors=args.palette)
        bp.with_colors(auto_colors)
    return bp


def process_single_image(bp, args, output_path=None):
    """处理单张图片，返回输出路径"""
    factor = args.factor if args.factor > 0 else suggest_factor(bp.input_path)

    if output_path is None:
        base_name = os.path.splitext(os.path.basename(bp.input_path))[0]
        suffix = "_pixel"
        if args.compare:
            suffix = "_compare"
        output_path = os.path.join(args.output, f"{base_name}{suffix}.png")

    # === 对比模式：先生成像素画，再拼原图 ===
    if args.compare:
        pixel = bp.generate(factor=factor, dither=args.dither, upscale=args.upscale)
        from skimage.transform import resize
        orig = bp._image
        # 把原图缩到跟像素画一样显示尺寸（但保持真实像素，不插值）
        h_px, w_px = pixel.shape[:2]
        orig_resized = resize(orig, (h_px * args.upscale, w_px * args.upscale),
                              anti_aliasing=True, preserve_range=True).astype(pixel.dtype)
        # 左右拼接
        import numpy as np
        gap = np.ones((h_px * args.upscale, 8, 3), dtype=pixel.dtype) * 220
        combined = np.concatenate([orig_resized, gap, pixel], axis=1)
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        from skimage import io
        io.imsave(output_path, combined)
        saved = output_path
        size_info = f"({os.path.getsize(saved)//1024}KB)"
    else:
        saved = bp.save(output_path, factor=factor, dither=args.dither, upscale=args.upscale)
        size_info = f"({os.path.getsize(saved)//1024}KB)"

    h, w = bp.image_shape[:2]
    out_img = __import__("skimage").io.imread(saved)
    out_h, out_w = out_img.shape[:2]
    print(f"  ✅ {os.path.basename(saved)}  {out_w}x{out_h}  {size_info}")

    # 显示配色信息
    details = []
    if args.style:
        details.append(f"风格:{args.style}")
    details.append(f"factor:{factor}")
    if bp.palette_hex:
        details.append(f"色:{' '.join(bp.palette_hex)}")
    print(f"     {' | '.join(details)}")

    # 调色板色卡
    if args.show_palette and bp.palette_hex:
        _save_palette_card(bp.palette_hex, saved.replace(".png", "_palette.png"))

    return saved, factor


def _save_palette_card(hex_colors, output_path):
    """生成调色板色卡"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        fig, ax = plt.subplots(figsize=(len(hex_colors) * 0.8, 1))
        ax.set_xlim(0, len(hex_colors))
        ax.set_ylim(0, 1)
        ax.axis("off")
        for i, c in enumerate(hex_colors):
            rect = mpatches.Rectangle((i, 0), 1, 1, facecolor=c, edgecolor="none")
            ax.add_patch(rect)
            text_color = "#fff" if int(c[1:3], 16) < 128 else "#000"
            ax.text(i + 0.5, 0.3, c, ha="center", va="center", fontsize=8, color=text_color)
        plt.tight_layout(pad=0)
        plt.savefig(output_path, dpi=100, bbox_inches="tight", pad_inches=0)
        plt.close()
        print(f"    调色板: {os.path.basename(output_path)}")
    except Exception as e:
        print(f"    调色板生成失败: {e}")


def _generate_gallery(output_dir, results):
    """生成画廊 index.html"""
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>brand-pixel · 像素画画廊</title>
<style>
body { font-family: 'Courier New', monospace; background: #111; color: #ccc; max-width: 1100px; margin: 0 auto; padding: 20px; }
h1 { color: #ffb000; font-size: 1.1em; letter-spacing: 2px; border-bottom: 1px solid #333; padding-bottom: 6px; }
h2 { color: #8ab4c8; font-size: 0.75em; margin: 20px 0 4px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; margin-bottom: 20px; }
.card { background: #1a1a1a; border: 1px solid #2a2a2a; padding: 6px; text-align: center; }
.card img { width: 100%; image-rendering: pixelated; }
.card .label { font-size: 0.55em; color: #888; margin-top: 3px; }
.card .dim { font-size: 0.45em; color: #555; }
.footer { text-align: center; font-size: 0.6em; color: #444; margin-top: 30px; }
</style>
</head>
<body>
<h1>✦ brand-pixel · 像素画画廊</h1>
<p style="font-size:0.65em;color:#666;">生成时间: {time}</p>
<div class="grid">
"""
    for name, w, h, factor, style_name in results:
        html += f'<div class="card">\n'
        html += f'  <img src="{name}" alt="{name}">\n'
        html += f'  <div class="label">{name}</div>\n'
        html += f'  <div class="dim">{w}x{h} | factor={factor}</div>\n'
        html += f'</div>\n'

    html += """</div>
<div class="footer">brand-pixel · 品牌像素画工厂</div>
</body>
</html>"""
    from datetime import datetime
    html = html.replace("{time}", datetime.now().strftime("%Y-%m-%d %H:%M"))
    path = os.path.join(output_dir, "index.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n  🖼️  画廊: {path}")
    return path


def main():
    args = parse_args()

    # --list-styles
    if args.list_styles:
        list_styles()
        return

    # --extract
    if args.extract:
        from brand_pixel import extract_palette
        colors = extract_palette(args.extract, n_colors=args.n_colors)
        print(f"提取的主色 ({len(colors)}色):")
        for c in colors:
            print(f"  {c}")
        return

    # 确定输入来源
    input_path = args.input or args.positional_input
    sources = []

    if args.folder:
        sources = find_images(args.folder)
        if not sources:
            print(f"❌ {args.folder} 里没有找到图片")
            sys.exit(1)
        print(f"📁 找到 {len(sources)} 张图片，开始批量处理...\n")
    elif input_path:
        sources = [input_path]
    else:
        print("❌ 请指定输入图片（--input / --folder / 位置参数）")
        print("   用 --list-styles 查看可用风格")
        print("   用 --help 查看完整帮助")
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)

    # 开始处理
    success = 0
    total = len(sources)
    gallery_results = [] if args.gallery else None

    for i, src in enumerate(sources):
        if not os.path.exists(src):
            print(f"  ⚠️ 跳过: {src}")
            continue

        prefix = f"[{i+1}/{total}]" if total > 1 else ""
        print(f"{prefix} 📷 {os.path.basename(src)}")

        try:
            bp = BrandPixel(src)
            bp = pick_color_mode(bp, args, src)

            # 如果是单张，当 args.compare 生效时 process_single_image 处理
            saved_path, used_factor = process_single_image(bp, args)
            success += 1

            if gallery_results is not None:
                from skimage import io as skio
                out_img = skio.imread(saved_path)
                out_h, out_w = out_img.shape[:2]
                gallery_results.append((
                    os.path.basename(saved_path),
                    out_w, out_h, used_factor,
                    args.style or "自定义"
                ))
        except Exception as e:
            print(f"  ❌ 失败: {e}")

    # 汇总
    print(f"\n{'='*40}")
    print(f"完成！成功 {success}/{total} 张")
    print(f"输出目录: {os.path.abspath(args.output)}")

    if gallery_results and success > 0:
        _generate_gallery(args.output, gallery_results)

    # 顺便打印一条快捷命令
    if success > 0 and not args.gallery:
        print(f"  提示: 加 --gallery 生成画廊首页")


if __name__ == "__main__":
    main()
