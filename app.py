"""
app.py — brand-pixel Gradio Web 界面

两个功能区：
  风格工坊 → 上传参考图 → 提色 → 命名保存预设
  像素画生成 → 上传目标照片 → 选预设（内置+自定义）→ 生成
"""
import os
import gradio as gr
import numpy as np
from PIL import Image as PILImage

from config import PRESETS, get_style_names, get_style
from brand_pixel import BrandPixel, extract_palette
from custom_presets import save_preset, list_custom, list_custom_names, delete_preset

TEMP_DIR = os.path.join(os.path.dirname(__file__), "output", "web")
os.makedirs(TEMP_DIR, exist_ok=True)

BUILTIN_NAMES = [p["name"] for p in PRESETS]


# ===== 工具 =====

def _make_chip(hex_colors, height=24):
    """生成色带图"""
    if not hex_colors:
        return None
    w = len(hex_colors) * 28
    chip = PILImage.new("RGB", (w, height))
    for i, c in enumerate(hex_colors):
        r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
        for x in range(i * 28, (i + 1) * 28):
            for y in range(height):
                chip.putpixel((x, y), (r, g, b))
    return np.array(chip)


def _colors_html(hex_list):
    """颜色列表 → HTML色块"""
    if not hex_list:
        return ""
    swatches = "".join(
        f'<span style="display:inline-block;width:22px;height:22px;background:{c};border:1px solid #555;vertical-align:middle;margin:0 2px;border-radius:2px" title="{c}"></span>'
        for c in hex_list
    )
    return f'<div style="font-size:11px;color:#888;margin:4px 0;line-height:28px">{swatches} {" ".join(hex_list)}</div>'


# =======================================================
#  功能区1：风格工坊
# =======================================================

def workshop_upload_ref(ref_img, n_colors):
    """上传参考图 → 提取配色 → 显示预览"""
    if ref_img is None:
        return [None, "", "", ""]
    path = os.path.join(TEMP_DIR, "_ref.png")
    PILImage.fromarray(ref_img).save(path)
    try:
        colors = extract_palette(path, n_colors=n_colors)
    except Exception as e:
        return [None, f"提取失败: {e}", "", ""]
    chip = _make_chip(colors)
    html = _colors_html(colors)
    hex_str = ", ".join(colors)
    return [chip, html, hex_str, colors]


def workshop_adjust_colors(hex_text):
    """手动调整颜色 → 更新色带"""
    colors = [c.strip() for c in hex_text.split(",") if c.strip()]
    if len(colors) < 2:
        return [gr.update(value=None), ""]
    chip = _make_chip(colors)
    html = _colors_html(colors)
    return [gr.update(value=chip), html]


def workshop_save(name, hex_text, description):
    """保存自定义预设"""
    if not name or not name.strip():
        return "⚠️ 请输入预设名称"
    if not hex_text or not hex_text.strip():
        return "⚠️ 请先提取配色"
    colors = [c.strip() for c in hex_text.split(",") if c.strip()]
    if len(colors) < 2:
        return "⚠️ 至少需要2种颜色"
    name = name.strip()
    try:
        save_preset(name, colors, description=description)
        return f"✅ 预设「{name}」已保存"
    except Exception as e:
        return f"❌ 保存失败: {e}"


# =======================================================
#  功能区2：像素画生成
# =======================================================

def generate_on_preset_change(preset_name):
    """切换预设 → 显示该预设的配色预览"""
    try:
        style = get_style(preset_name)
        chip = _make_chip(style["colors"])
        html = _colors_html(style["colors"])
        return [gr.update(value=chip), html]
    except Exception:
        return [None, ""]


def generate_image(input_img, preset_name, factor, dither, upscale, do_compare):
    """上传目标照片 + 选预设 → 生成像素画"""
    if input_img is None:
        return None, '<div class="output-info">⚠️ 请先上传目标照片</div>'

    temp_input = os.path.join(TEMP_DIR, "_target.png")
    PILImage.fromarray(input_img).save(temp_input)

    try:
        bp = BrandPixel(temp_input)
    except Exception as e:
        return None, f'<div class="output-info">❌ 读取图片失败: {e}</div>'

    # 用选中的预设
    try:
        bp.with_style(preset_name)
    except Exception as e:
        return None, f'<div class="output-info">❌ 预设错误: {e}</div>'

    h, w = bp.image_shape[:2]
    info_lines = [
        f"原图: {w}×{h}",
        f"预设: {preset_name}",
        f"配色: {' '.join(bp.palette_hex)}",
    ]

    try:
        pixel = bp.generate(factor=factor, dither=dither, upscale=upscale)
    except Exception as e:
        return None, f'<div class="output-info">❌ 生成失败: {e}</div>'

    out_h, out_w = pixel.shape[:2]
    info_lines.append(f"输出: {out_w}×{out_h} | factor={factor} | dither={dither}")

    if do_compare:
        from skimage.transform import resize
        orig = resize(input_img, (out_h, out_w), anti_aliasing=True, preserve_range=True).astype(np.uint8)
        gap = np.ones((out_h, 6, 3), dtype=np.uint8) * 180
        display = np.concatenate([orig, gap, pixel], axis=1)
    else:
        display = pixel

    html = f'<div class="output-info">{"<br>".join(info_lines)}</div>'
    return display, html


# =======================================================
#  CSS
# =======================================================

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
:root {
  --bg: #1a1a1a; --card: #222; --border: #333;
  --accent: #ffb000; --accent2: #9185cf;
  --text: #e0d8c8; --text-dim: #666;
}
body { background: var(--bg) !important; }
.gradio-container { max-width: 960px !important; margin: 0 auto !important; font-family: 'Courier New', monospace !important; background: var(--bg) !important; color: var(--text) !important; }
.app-title { text-align: center; padding: 20px 0 8px; border-bottom: 2px dotted var(--accent2); margin-bottom: 16px; }
.app-title h1 { font-family: 'Press Start 2P', monospace; font-size: 18px; color: var(--accent); letter-spacing: 2px; margin: 0; }
.app-title p { font-size: 11px; color: var(--text-dim); margin: 6px 0 0; }
.card { background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: 0 !important; padding: 10px !important; }
.card-title { font-size: 11px !important; color: var(--accent2) !important; text-transform: uppercase !important; letter-spacing: 1px !important; margin-bottom: 6px !important; }
.gr-button-primary { background: var(--accent) !important; color: #111 !important; border: none !important; border-radius: 0 !important; font-family: 'Courier New', monospace !important; font-weight: bold !important; font-size: 13px !important; letter-spacing: 2px !important; text-transform: uppercase !important; padding: 10px 20px !important; }
.gr-button-primary:hover { background: #ffc830 !important; }
.gr-button-secondary { border: 1px solid var(--accent2) !important; color: var(--accent2) !important; background: transparent !important; border-radius: 0 !important; font-family: 'Courier New', monospace !important; font-size: 12px !important; }
input, textarea, select { background: #111 !important; border: 1px solid var(--border) !important; border-radius: 0 !important; color: var(--text) !important; font-family: 'Courier New', monospace !important; }
input:focus, textarea:focus, select:focus { border-color: var(--accent) !important; box-shadow: none !important; }
.output-info { font-size: 11px; color: var(--text-dim); line-height: 1.7; padding: 8px; background: #111; border: 1px solid var(--border); }
.gr-slider input[type=range] { accent-color: var(--accent) !important; }
label { font-size: 11px !important; color: var(--text-dim) !important; font-family: 'Courier New', monospace !important; }
.gr-image img { image-rendering: pixelated !important; }
.gr-checkbox { accent-color: var(--accent2) !important; }
.tabs { border: none !important; }
.tab-nav { font-family: 'Courier New', monospace !important; font-size: 12px !important; letter-spacing: 1px !important; }
.footer { text-align: center; font-size: 10px; color: #444; padding: 20px 0; border-top: 1px solid var(--border); margin-top: 20px; }
"""


# =======================================================
#  构建界面
# =======================================================

def build_app():
    with gr.Blocks(title="brand-pixel 品牌像素画工厂") as app:

        gr.HTML("""
        <div class="app-title">
          <h1>✦ BRAND-PIXEL ✦</h1>
          <p>品牌像素画工厂</p>
        </div>
        """)

        # 共享状态：预设列表（用于跨Tab同步）
        presets_state = gr.State(get_style_names())

        with gr.Tabs() as tabs:
            # ======== TAB 1: 风格工坊 ========
            with gr.Tab("🎨 风格工坊"):
                gr.HTML('<p style="font-size:11px;color:#666;margin:0 0 10px">上传参考图 → 提取配色 → 命名保存 → 之后在"像素画生成"里使用</p>')
                with gr.Row(equal_height=False):
                    with gr.Column(scale=2):
                        with gr.Group(elem_classes="card"):
                            gr.HTML('<div class="card-title">📷 上传参考图</div>')
                            ref_input = gr.Image(label=None, type="numpy", height=240, show_label=False)
                        with gr.Row():
                            n_colors_slider = gr.Slider(minimum=3, maximum=12, value=8, step=1, label="提取色数")
                            extract_btn = gr.Button("提取配色", variant="primary", size="sm")
                    with gr.Column(scale=3):
                        with gr.Group(elem_classes="card"):
                            gr.HTML('<div class="card-title">🎨 提取的配色</div>')
                            ref_chip = gr.Image(label=None, height=26, show_label=False)
                            ref_html = gr.HTML(value="上传参考图后点击「提取配色」")
                        with gr.Group(elem_classes="card"):
                            gr.HTML('<div class="card-title">💾 保存为预设</div>')
                            with gr.Row():
                                preset_name = gr.Textbox(label="预设名称", placeholder="例: 贴纸风、电影色调", lines=1, scale=2)
                                save_btn = gr.Button("保存预设", variant="primary", size="sm", scale=1)
                            preset_desc = gr.Textbox(label="描述（可选）", placeholder="从哪张图提取的灵感", lines=1)
                            hex_colors_text = gr.Textbox(label="Hex颜色（可手动微调）", lines=1)
                            save_status = gr.HTML(value="")
                            ref_colors_state = gr.State([])

                # 事件
                extract_btn.click(
                    fn=workshop_upload_ref,
                    inputs=[ref_input, n_colors_slider],
                    outputs=[ref_chip, ref_html, hex_colors_text, ref_colors_state],
                )
                save_btn.click(
                    fn=workshop_save,
                    inputs=[preset_name, hex_colors_text, preset_desc],
                    outputs=[save_status],
                )
                # 编辑Hex颜色 → 更新色带预览
                hex_colors_text.change(
                    fn=workshop_adjust_colors,
                    inputs=[hex_colors_text],
                    outputs=[ref_chip, ref_html],
                )

            # ======== TAB 2: 像素画生成 ========
            with gr.Tab("🖼️ 像素画生成"):
                gr.HTML('<p style="font-size:11px;color:#666;margin:0 0 10px">上传目标照片 → 选预设（内置/自定义）→ 生成像素画</p>')
                with gr.Row(equal_height=False):
                    with gr.Column(scale=2):
                        with gr.Group(elem_classes="card"):
                            gr.HTML('<div class="card-title">📷 目标照片</div>')
                            target_input = gr.Image(label=None, type="numpy", height=240, show_label=False)

                        with gr.Group(elem_classes="card"):
                            gr.HTML('<div class="card-title">🎨 选预设</div>')
                            # 合并内置+自定义的预设列表
                            all_presets = get_style_names()
                            gen_preset = gr.Dropdown(
                                choices=all_presets, value="品牌暗调",
                                label="预设风格",
                            )
                            gen_chip = gr.Image(label=None, height=22, show_label=False)
                            gen_html = gr.HTML(value="选择预设后自动显示配色")

                        with gr.Group(elem_classes="card"):
                            gr.HTML('<div class="card-title">⚙️ 参数</div>')
                            gen_factor = gr.Slider(minimum=2, maximum=30, value=8, step=1, label="Factor")
                            with gr.Row():
                                gen_dither = gr.Dropdown(
                                    choices=["none", "naive", "floyd", "atkinson"],
                                    value="none", label="Dither",
                                )
                                gen_upscale = gr.Slider(minimum=1, maximum=4, value=1, step=1, label="放大")
                            gen_compare = gr.Checkbox(label="对比模式（原图 vs 像素画）", value=False)

                    with gr.Column(scale=3):
                        with gr.Group(elem_classes="card"):
                            gr.HTML('<div class="card-title">✨ 像素画</div>')
                            gen_output = gr.Image(label=None, height=420, show_label=False)
                        gen_info = gr.HTML(value='<div class="output-info">上传目标照片 → 选预设 → 生成</div>')

                with gr.Row():
                    gen_btn = gr.Button("✦ 生成像素画 ✦", variant="primary", size="lg")

                # 事件
                gen_preset.change(
                    fn=generate_on_preset_change,
                    inputs=[gen_preset],
                    outputs=[gen_chip, gen_html],
                )
                gen_btn.click(
                    fn=generate_image,
                    inputs=[target_input, gen_preset, gen_factor, gen_dither, gen_upscale, gen_compare],
                    outputs=[gen_output, gen_info],
                )

        gr.HTML('<div class="footer">brand-pixel · 品牌像素画工厂</div>')

        # ====== 跨Tab同步：每次切换tab刷新预设下拉 ======
        def refresh_presets():
            """刷新预设下拉列表（从JSON读取最新数据）"""
            return gr.update(choices=get_style_names())

        tabs.select(
            fn=refresh_presets,
            outputs=[gen_preset],
        )

        # 页面加载时初始化预设预览
        app.load(
            fn=generate_on_preset_change,
            inputs=[gen_preset],
            outputs=[gen_chip, gen_html],
        )

    return app


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="127.0.0.1", server_port=7860, share=False, css=CSS)
