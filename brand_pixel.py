"""
brand_pixel.py — 品牌像素画工厂 核心类

支持的三种配色方式：
  1. --colors "#hex,#hex,..."    直接传Hex颜色列表
  2. --style "风格名"             用预设风格
  3. --from-image ref.jpg         从参考图提取颜色

用法示例：
  from brand_pixel import BrandPixel
  bp = BrandPixel("photo.jpg")
  bp.with_style("品牌暗调").save("output.png")
"""
import os
import numpy as np
from skimage import io
from pyxelate import Pyx, Pal
from sklearn.cluster import KMeans

from config import get_style, get_style_names


class BrandPixel:
    """品牌像素画工厂"""

    def __init__(self, input_path):
        """
        参数：
          input_path: 输入图片路径（支持 jpg/png/bmp/webp）
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"找不到图片: {input_path}")
        self.input_path = input_path
        self._image = io.imread(input_path)
        self._palette = None          # Pal 对象
        self._palette_hex = None      # 原始Hex列表（用于显示）
        self._style_name = None       # 风格名称（用于显示）
        self._n_colors = 8            # 自动取色时的色数

    # ========== 三种配色方式 ==========

    def with_colors(self, hex_colors):
        """方式1：直接传Hex颜色列表"""
        self._palette = Pal.from_hex(hex_colors)
        self._palette_hex = hex_colors
        self._style_name = None
        return self

    def with_style(self, style_name):
        """方式2：用预设风格"""
        style = get_style(style_name)
        self._palette = Pal.from_hex(style["colors"])
        self._palette_hex = style["colors"]
        self._style_name = style_name
        return self

    def from_image(self, ref_path, n_colors=5):
        """方式3：从参考图提取颜色
        参数：
          ref_path: 参考图片路径
          n_colors: 提取几种主色（默认5）
        """
        ref_img = io.imread(ref_path)
        h, w = ref_img.shape[:2]
        # 缩小参考图加速
        scale = min(1.0, 200 / max(h, w))
        if scale < 1:
            from skimage.transform import resize
            ref_img = resize(ref_img, (int(h * scale), int(w * scale)), anti_aliasing=True)
            ref_img = (ref_img * 255).astype(np.uint8)

        pixels = ref_img.reshape(-1, 3)
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=5)
        kmeans.fit(pixels)
        colors = kmeans.cluster_centers_.astype(int)
        hex_colors = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in colors]

        self._palette = Pal.from_hex(hex_colors)
        self._palette_hex = hex_colors
        self._style_name = None
        return self

    # ========== 生成逻辑 ==========

    def generate(self, factor=8, dither="none", upscale=1):
        """执行像素画生成
        参数：
          factor: 像素块大小（默认8，越大块越大）
          dither: 抖动类型 (none/naive/floyd/atkinson)
          upscale: 输出放大倍数（默认1）
        返回：
          numpy array (像素画)
        """
        if self._palette is None:
            # 没指定配色 → 自动取色
            pyx = Pyx(factor=factor, palette=self._n_colors, dither=dither, upscale=upscale)
        else:
            pyx = Pyx(factor=factor, palette=self._palette, dither=dither, upscale=upscale)
        return pyx.fit_transform(self._image)

    def save(self, output_path, factor=8, dither="none", upscale=1):
        """生成并保存到文件
        返回：
          保存路径
        """
        result = self.generate(factor=factor, dither=dither, upscale=upscale)
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        io.imsave(output_path, result)
        return output_path

    # ========== 信息 ==========

    def info(self):
        """打印本次处理的信息"""
        h, w = self._image.shape[:2]
        lines = [
            f"输入: {os.path.basename(self.input_path)} ({w}x{h})",
        ]
        if self._style_name:
            lines.append(f"风格: {self._style_name}")
        if self._palette_hex:
            lines.append(f"配色: {' '.join(self._palette_hex)}")
        else:
            lines.append(f"配色: 自动取色 {self._n_colors}色")
        return "\n".join(lines)

    @property
    def palette_hex(self):
        return self._palette_hex

    @property
    def image_shape(self):
        return self._image.shape


# ========== 颜色提取工具（独立使用） ==========

def extract_palette(image_path, n_colors=5):
    """从图片提取主色
    返回：Hex颜色列表
    """
    img = io.imread(image_path)
    h, w = img.shape[:2]
    scale = min(1.0, 200 / max(h, w))
    if scale < 1:
        from skimage.transform import resize
        img = resize(img, (int(h * scale), int(w * scale)), anti_aliasing=True)
        img = (img * 255).astype(np.uint8)
    pixels = img.reshape(-1, 3)
    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=5)
    kmeans.fit(pixels)
    colors = kmeans.cluster_centers_.astype(int)
    return [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in colors]
