import os
import json
import math
import tempfile
import threading
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage
from kivy.graphics.texture import Texture
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.utils import platform
from plyer import filechooser, storage, sharing, permissions
import requests
import piexif
from pathlib import Path

# ===================== Android 条件导入 =====================
InputStream = None
FileOutputStream = None
activity = None
ContentValues = None
MediaStore = None
if platform == "android":
    from android import activity
    from java import jclass
    InputStream = jclass("java.io.InputStream")
    FileOutputStream = jclass("java.io.FileOutputStream")
    ContentValues = jclass("android.content.ContentValues")
    MediaStore = jclass("android.provider.MediaStore")

# ===================== 全局配置 =====================
DEFAULT_CONFIG = {
    "font_size": 30,
    "font_color": [255, 255, 255],
    "bg_color": [0, 0, 0],
    "bg_alpha": 0,
    "padding": 18,
    "line_spacing": 32
}
FAKE_WIDTH = 640
FAKE_HEIGHT = 480
JPG_SUFFIXES = {".jpg", ".jpeg"}
RAW_SUFFIXES = {".nef", ".arw", ".raf", ".cr2", ".orf", ".rw2", ".pef", ".x3f", ".dng", ".srw"}
ICON_SIZE = 40
ICON_TEXT_GAP = 22
LINE_WIDTH = 2
BOX_PADDING = 18
LINE_SPACING = 14
STANDARD_META_SCHEMA = {
    "shoot_time": "N/A",
    "camera_brand": "N/A",
    "camera_model": "N/A",
    "shutter_speed": "N/A",
    "aperture": "N/A",
    "iso": "N/A",
    "focal_length": "N/A",
    "lens_full_name": "N/A",
    "lens_id_raw": "N/A",
    "lens_id_decoded": "N/A"
}
SERVER_URL = "http://81.70.35.197:8000/api/parse_exif"


# ===================== 工具函数 =====================
def get_file_raw_exif_blob(src_path: str) -> bytes:
    suffix = Path(src_path).suffix.lower()
    if suffix in JPG_SUFFIXES:
        with open(src_path, "rb") as f:
            jpg_bytes = f.read()
        try:
            exif_dict = piexif.load(jpg_bytes)
            return piexif.dump(exif_dict)
        except Exception:
            return b""
    if suffix in RAW_SUFFIXES:
        with open(src_path, "rb") as f:
            raw_buffer = f.read()
        soi_mark = b"\xff\xd8"
        eoi_mark = b"\xff\xd9"
        start = raw_buffer.find(soi_mark)
        if start == -1:
            return b""
        end = raw_buffer.find(eoi_mark, start + 2)
        if end == -1:
            return b""
        preview_jpg_bin = raw_buffer[start: end + 2]
        try:
            exif_dict = piexif.load(preview_jpg_bin)
            return piexif.dump(exif_dict)
        except Exception:
            return b""
    return b""


def generate_empty_fake_jpg_with_raw_exif(source_file: str, output_jpg: str) -> str:
    src = Path(source_file)
    out = Path(output_jpg)
    exif_blob = get_file_raw_exif_blob(str(src))
    blank_canvas = Image.new("RGB", (FAKE_WIDTH, FAKE_HEIGHT), color=(128, 128, 128))
    save_options = {"format": "JPEG", "quality": 85}
    if exif_blob:
        save_options["exif"] = exif_blob
    blank_canvas.save(str(out), **save_options)
    blank_canvas.close()
    return str(out.resolve())


def draw_icon(draw, x, y, icon_type, line_color=(255, 255, 255)):
    s = ICON_SIZE
    cx = x + s / 2
    cy = y + s / 2
    lw = LINE_WIDTH
    margin_ratio = 0.12
    m = s * margin_ratio
    area_left = x + m
    area_right = x + s - m
    area_top = y + m
    area_bottom = y + s - m
    center_x = (area_left + area_right) / 2
    center_y = (area_top + area_bottom) / 2
    total_heigth = area_bottom - area_top
    if icon_type == "shutter_lightning":
        scale = total_heigth * 0.7
        line_w = LINE_WIDTH
        col = line_color
        head_r = scale * 0.2
        draw.ellipse(
            [center_x + scale * 0.37 - head_r, center_y - scale * 0.41 - head_r,
             center_x + scale * 0.37 + head_r, center_y - scale * 0.41 + head_r],
            outline=col, width=line_w
        )
        seg1 = [(center_x - scale * 0.5 / 1.732 + head_r, center_y + scale * 0.5),
                (center_x + scale * 0.25 / 1.732 + head_r, center_y - scale * 0.25)]
        draw.line(seg1, fill=col, width=line_w)
        seg3 = [(center_x + head_r - 1 / 12 * scale, center_y + 1 / 12 * scale * 1.732),
                (center_x + scale / 6 + head_r, center_y + scale / 4)]
        draw.line(seg3, fill=col, width=line_w)
        seg2 = [(center_x + scale / 6 + head_r, center_y + scale / 4),
                (center_x + scale / 6 - scale / 8 / 0.577 + head_r, center_y + scale * (1 / 3 + 1 / 8))]
        draw.line(seg2, fill=col, width=line_w)
        seg4 = [(center_x + head_r + scale * (0.25 / 1.732 + 1 / 4 / 1.732), center_y + scale * (-1 / 4 + 1 / 4)),
                (center_x + head_r + scale * (0.25 / 1.732 + 1 / 4 / 1.732 + 1 / 6 / 0.577),
                 center_y + scale * (-1 / 4 + 1 / 4 - 1 / 6))]
        draw.line(seg4, fill=col, width=line_w)
        seg5 = [(center_x + scale * 0.25 / 1.732 + head_r, center_y - scale * 0.25),
                (center_x + head_r + scale * (0.25 / 1.732 + 1 / 4 / 1.732), center_y + scale * (-1 / 4 + 1 / 4))]
        draw.line(seg5, fill=col, width=line_w)
        seg6 = [(center_x + scale * 0.25 / 1.732 + head_r, center_y - scale * 0.25),
                (center_x + scale * (0.25 / 1.732 - 1 / 5) + head_r, center_y - scale * 0.25)]
        draw.line(seg6, fill=col, width=line_w)
        seg7 = [(center_x + scale * (0.25 / 1.732 - 1 / 5) + head_r, center_y - scale * 0.25),
                (center_x + scale * (0.25 / 1.732 - 1 / 5 - 1 / 6) + head_r,
                 center_y + scale * (-0.25 + 1 / 6 * 1.732))]
        draw.line(seg7, fill=col, width=line_w)
        speed_lines = [
            (center_x - scale * 0.85, center_y - scale * 0.2, center_x - scale * 0.41, center_y - scale * 0.2),
            (center_x - scale * 0.70, center_y + scale * 0.02, center_x - scale * 0.33, center_y + scale * 0.02),
            (center_x - scale * 0.86, center_y + scale * 0.25, center_x - scale * 0.55, center_y + scale * 0.25),
        ]
        for x1, y1, x2, y2 in speed_lines:
            draw.line([(x1, y1), (x2, y2)], fill=col, width=line_w)
    elif icon_type == "aperture":
        outer_r = total_heigth * 0.41
        inner_r = total_heigth * 0.09
        draw.ellipse(
            [center_x - outer_r, center_y - outer_r,
             center_x + outer_r, center_y + outer_r],
            outline=line_color,
            width=LINE_WIDTH
        )
        lines = [
            ((center_x + outer_r * math.cos(math.radians(90)), center_y - outer_r * math.sin(math.radians(90))),
             (center_x + inner_r * math.cos(math.radians(122)), center_y - inner_r * math.sin(math.radians(122)))),
            ((center_x + outer_r * math.cos(math.radians(141)), center_y - outer_r * math.sin(math.radians(141))),
             (center_x + inner_r * math.cos(math.radians(182)), center_y - inner_r * math.sin(math.radians(182)))),
            ((center_x + outer_r * math.cos(math.radians(193)), center_y - outer_r * math.sin(math.radians(193))),
             (center_x + inner_r * math.cos(math.radians(242)), center_y - inner_r * math.sin(math.radians(242)))),
            ((center_x + outer_r * math.cos(math.radians(245)), center_y - outer_r * math.sin(math.radians(245))),
             (center_x + inner_r * math.cos(math.radians(302)), center_y - inner_r * math.sin(math.radians(302)))),
            ((center_x + outer_r * math.cos(math.radians(297)), center_y - outer_r * math.sin(math.radians(297))),
             (center_x + inner_r * math.cos(math.radians(2)), center_y - inner_r * math.sin(math.radians(2)))),
            ((center_x + outer_r * math.cos(math.radians(349)), center_y - outer_r * math.sin(math.radians(349))),
             (center_x + inner_r * math.cos(math.radians(62)), center_y - inner_r * math.sin(math.radians(62)))),
            ((center_x + outer_r * math.cos(math.radians(47)), center_y - outer_r * math.sin(math.radians(47))),
             (center_x + inner_r * math.cos(math.radians(62)), center_y - inner_r * math.sin(math.radians(62)))),
        ]
        for p1, p2 in lines:
            draw.line([p1, p2], fill=line_color, width=LINE_WIDTH)
    elif icon_type == "clock":
        draw.ellipse([x + 4, y + 4, x + s - 4, y + s - 4], outline=line_color, width=lw)
        draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=line_color)
        draw.line([cx, cy, cx, y + 10], fill=line_color, width=lw)
        draw.line([cx, cy, x + s - 10, cy], fill=line_color, width=lw)
    elif icon_type == "camera":
        body_height = total_heigth * 0.8
        body_top_y = area_bottom - body_height
        body_expand = total_heigth * 0.09
        body_left = area_left - body_expand
        body_right = area_right + body_expand
        corner_radius = total_heigth * 0.22
        draw.rounded_rectangle(
            [body_left, body_top_y, body_right, area_bottom],
            radius=corner_radius,
            outline=line_color,
            width=LINE_WIDTH
        )
        peak_height = total_heigth * 0.20
        side_offset = (area_right - area_left) * 0.21
        curve_step = total_heigth * 0.07
        viewfinder_points = [
            (area_left + side_offset, body_top_y),
            (area_left + side_offset + curve_step, body_top_y - peak_height),
            (area_right - side_offset - curve_step, body_top_y - peak_height),
            (area_right - side_offset, body_top_y)
        ]
        draw.line(viewfinder_points[:3], fill=line_color, width=LINE_WIDTH)
        draw.line([viewfinder_points[2], viewfinder_points[3]], fill=line_color, width=LINE_WIDTH)
        lens_down_offset = total_heigth * 0.08
        lens_center_y = center_y + lens_down_offset
        outer_lens_r = total_heigth * 0.33
        inner_lens_r = outer_lens_r * 0.54
        draw.ellipse(
            [center_x - outer_lens_r, lens_center_y - outer_lens_r,
             center_x + outer_lens_r, lens_center_y + outer_lens_r],
            outline=line_color, width=LINE_WIDTH
        )
        draw.ellipse(
            [center_x - inner_lens_r, lens_center_y - inner_lens_r,
             center_x + inner_lens_r, lens_center_y + inner_lens_r],
            outline=line_color, width=LINE_WIDTH
        )
        dot_radius = total_heigth * 0.075
        dot_pos_x = area_right - total_heigth * 0.17
        dot_pos_y = body_top_y + total_heigth * 0.24
        draw.ellipse(
            [dot_pos_x - dot_radius, dot_pos_y - dot_radius,
             dot_pos_x + dot_radius, dot_pos_y + dot_radius],
            outline=line_color, width=LINE_WIDTH
        )
    elif icon_type == "iso_text":
        try:
            font_icon = ImageFont.truetype("/system/fonts/DroidSans.ttf", 24)
        except Exception:
            font_icon = ImageFont.load_default(size=24)
        bb = draw.textbbox((0, 0), "ISO", font=font_icon)
        txt_h = bb[3] - bb[1]
        text_y = y + s / 2 - txt_h / 2 - 2
        draw.text((x + 5, text_y - 5), "ISO", fill=line_color, font=font_icon)
    elif icon_type == "lens_ruler":
        scale = total_heigth * 0.7
        line_w = LINE_WIDTH
        col = line_color
        sqrt3 = 1.732
        f_dist = scale
        focus_x = center_x - f_dist
        focus_point = (focus_x, center_y)
        draw.line([(focus_x - scale * 0.3, center_y), (center_x + scale * 0.3, center_y)], fill=col, width=line_w)
        dot_r = line_w
        draw.ellipse(
            [focus_x - dot_r, center_y - dot_r, focus_x + dot_r, center_y + dot_r],
            fill=col
        )
        seg_up = [
            (focus_x, center_y),
            (center_x + scale * 0.25 / sqrt3, center_y - scale * 0.25)
        ]
        seg_down = [
            (focus_x, center_y),
            (center_x + scale * 0.25 / sqrt3, center_y + scale * 0.25)
        ]
        draw.line(seg_up, fill=col, width=line_w)
        draw.line(seg_down, fill=col, width=line_w)
        out_extend = scale * 0.3
        top_out_end = (center_x + out_extend, seg_up[1][1])
        draw.line([seg_up[1], top_out_end], fill=col, width=line_w)
        bottom_out_end = (center_x + out_extend, seg_down[1][1])
        draw.line([seg_down[1], bottom_out_end], fill=col, width=line_w)
        arrow_len = scale * 0.08

        def draw_arrow(end_point, y_offset):
            x, y = end_point
            draw.polygon([
                (x, y),
                (x - arrow_len, y - y_offset),
                (x - arrow_len, y + y_offset)
            ], fill=col)

        draw_arrow(top_out_end, arrow_len // 2)
        draw_arrow(bottom_out_end, arrow_len // 2)
        lens_half_h = scale * 0.5
        lens_thick = scale * 0.06
        draw.arc(
            [center_x - lens_thick * 3, center_y - lens_half_h,
             center_x + lens_thick * 3, center_y + lens_half_h],
            start=90, end=270, fill=col, width=line_w
        )
        draw.arc(
            [center_x - lens_thick * 3, center_y - lens_half_h,
             center_x + lens_thick * 3, center_y + lens_half_h],
            start=270, end=90, fill=col, width=line_w
        )
        try:
            font_f = ImageFont.truetype("/system/fonts/DroidSans.ttf", int(scale * 0.8))
        except Exception:
            font_f = ImageFont.load_default(size=int(scale * 0.8))
        text_x = (focus_x + center_x) / 2 - scale * 0.05
        text_y = center_y + scale * 0.22
        draw.text((text_x, text_y), "f", fill=col, font=font_f)
    elif icon_type == "tele_lens":
        scale = total_heigth * 0.9
        line_w = LINE_WIDTH
        col = line_color
        seg1 = [(center_x - scale * 0.5, center_y + scale * 0.35 / 2),
                (center_x - scale * 0.5, center_y - scale * 0.35 / 2)]
        draw.line(seg1, fill=col, width=line_w)
        seg2 = [(center_x - scale * (0.5 - 1 / 66), center_y + scale * 0.37 / 2),
                (center_x - scale * (0.5 - 1 / 66), center_y - scale * 0.37 / 2)]
        draw.line(seg2, fill=col, width=line_w)
        seg3 = [(center_x - scale * 55 / 200, center_y + scale * 0.48 / 2),
                (center_x - scale * 55 / 200, center_y - scale * 0.48 / 2)]
        draw.line(seg3, fill=col, width=line_w)
        seg4 = [(center_x - scale * 52 / 200, center_y + scale * 0.48 / 2),
                (center_x - scale * 52 / 200, center_y - scale * 0.48 / 2)]
        draw.line(seg4, fill=col, width=line_w)
        seg5 = [(center_x - scale * 21 / 200, center_y + scale * 0.48 / 2),
                (center_x - scale * 21 / 200, center_y - scale * 0.48 / 2)]
        draw.line(seg5, fill=col, width=line_w)
        seg6 = [(center_x - scale * 19 / 200, center_y + scale * 0.48 / 2),
                (center_x - scale * 19 / 200, center_y - scale * 0.48 / 2)]
        draw.line(seg6, fill=col, width=line_w)
        seg7 = [(center_x - scale * 17 / 200, center_y + scale * 0.48 / 2),
                (center_x - scale * 17 / 200, center_y - scale * 0.48 / 2)]
        draw.line(seg7, fill=col, width=line_w)
        seg8 = [(center_x + scale * 25 / 200, center_y + scale * 0.48 / 2),
                (center_x + scale * 25 / 200, center_y - scale * 0.48 / 2)]
        draw.line(seg8, fill=col, width=line_w)
        seg9 = [(center_x + scale * 28 / 200, center_y + scale * 0.48 / 2),
                (center_x + scale * 28 / 200, center_y - scale * 0.48 / 2)]
        draw.line(seg9, fill=col, width=line_w)
        seg10 = [(center_x - scale * 0.5, center_y + scale * 0.35 / 2),
                  (center_x - scale * 55 / 200, center_y + scale * 0.48 / 2)]
        draw.line(seg10, fill=col, width=line_w)
        seg11 = [(center_x - scale * 0.5, center_y - scale * 0.35 / 2),
                  (center_x - scale * 55 / 200, center_y - scale * 0.48 / 2)]
        draw.line(seg11, fill=col, width=line_w)
        seg12 = [(center_x - scale * 0.55 / 2, center_y - scale * 0.48 / 2),
                  (center_x + scale * 25 / 200, center_y - scale * 0.48 / 2)]
        draw.line(seg12, fill=col, width=line_w)
        seg13 = [(center_x - scale * 0.55 / 2, center_y + scale * 0.48 / 2),
                  (center_x + scale * 25 / 200, center_y + scale * 0.48 / 2)]
        draw.line(seg13, fill=col, width=line_w)
        seg14 = [(center_x + scale * 25 / 200, center_y + scale * 0.48 / 2),
                  (center_x + scale * 81 / 200, center_y + scale * 0.81 / 2)]
        draw.line(seg14, fill=col, width=line_w)
        seg15 = [(center_x + scale * 25 / 200, center_y - scale * 0.48 / 2),
                  (center_x + scale * 81 / 200, center_y - scale * 0.81 / 2)]
        draw.line(seg15, fill=col, width=line_w)
        seg16 = [(center_x + scale * 63 / 200, center_y + scale * 0.48 / 2),
                  (center_x + scale * 81 / 200, center_y + scale * 0.81 / 2)]
        draw.line(seg16, fill=col, width=line_w)
        seg17 = [(center_x + scale * 63 / 200, center_y - scale * 0.48 / 2),
                  (center_x + scale * 81 / 200, center_y - scale * 0.81 / 2)]
        draw.line(seg17, fill=col, width=line_w)
        seg18 = [(center_x + scale * 63 / 200, center_y + scale * 0.48 / 2),
                  (center_x + scale * 81 / 200, center_y)]
        draw.line(seg18, fill=col, width=line_w)
        seg19 = [(center_x + scale * 63 / 200, center_y - scale * 0.48 / 2),
                  (center_x + scale * 81 / 200, center_y)]
        draw.line(seg19, fill=col, width=line_w)


def copy_content_uri_to_temp(uri: str) -> str:
    if platform != "android":
        return uri
    if not uri.startswith("content://"):
        return uri

    resolver = activity.getContentResolver()
    cache_dir = App.get_running_app().user_data_dir
    fd, temp_path = tempfile.mkstemp(suffix=".jpg", dir=cache_dir)
    os.close(fd)

    input_stream = None
    output_stream = None
    try:
        input_stream = resolver.openInputStream(uri)
        output_stream = FileOutputStream(temp_path)
        buf = bytes(4096)
        n = input_stream.read(buf)
        while n != -1:
            output_stream.write(buf, 0, n)
            n = input_stream.read(buf)
    finally:
        if input_stream is not None:
            input_stream.close()
        if output_stream is not None:
            output_stream.close()
    return temp_path


def save_image_to_public_album(pil_image: Image.Image, filename: str):
    """
    将PIL图片写入安卓公共相册DCIM，Android10+不需要WRITE_EXTERNAL_STORAGE
    返回：保存成功content uri字符串；失败返回None
    """
    if platform != "android":
        # PC端直接保存当前目录
        out_path = os.path.abspath(filename)
        pil_image.save(out_path, format="JPEG", quality=90)
        print(f"PC保存:{out_path}")
        return out_path

    resolver = activity.getContentResolver()
    values = ContentValues()
    values.put(MediaStore.Images.Media.DISPLAY_NAME, filename)
    values.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg")
    # 保存到 DCIM/EXIFWatermark 目录
    values.put(MediaStore.Images.Media.RELATIVE_PATH, "DCIM/EXIFWatermark")

    uri = resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
    if uri is None:
        print("MediaStore insert失败")
        return None

    output_stream = None
    try:
        output_stream = resolver.openOutputStream(uri)
        pil_image.save(output_stream, format="JPEG", quality=90)
    except Exception as e:
        print(f"写入相册异常:{e}")
        return None
    finally:
        if output_stream:
            output_stream.close()
    print(f"相册保存成功 uri={uri}")
    return uri


# ===================== APP主界面 =====================
class ExifWatermarkRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = 10
        self.padding = 10
        self.img_path = None
        self.img = None
        self.raw_pil_img = None
        self.source_filename = None
        self.processed_pil_img = None
        self.rotate_angle = 0
        self.render_cache = []
        self.temp_fake_jpg = ""
        self.last_saved_uri = None
        self.is_loading_exif = False

        btn_layout = BoxLayout(size_hint_y=0.1, spacing=8)
        self.btn_open = Button(text="打开", on_press=self.action_open)
        self.btn_rotate = Button(text="旋转", on_press=self.action_rotate)
        self.btn_save = Button(text="保存", on_press=self.action_save)
        self.btn_share = Button(text="分享", on_press=self.action_share)
        btn_layout.add_widget(self.btn_open)
        btn_layout.add_widget(self.btn_rotate)
        btn_layout.add_widget(self.btn_save)
        btn_layout.add_widget(self.btn_share)
        self.add_widget(btn_layout)

        self.img_widget = KivyImage(size_hint_y=0.9, allow_stretch=True, keep_ratio=True)
        self.add_widget(self.img_widget)

    def get_needed_storage_permissions(self):
        if platform != "android":
            return []
        from android import api_version
        if api_version >= 33:
            return ["android.permission.READ_MEDIA_IMAGES"]
        else:
            return ["android.permission.READ_EXTERNAL_STORAGE"]

    def on_permission_callback(self, granted, **kwargs):
        if granted:
            filechooser.open_file(
                filters=["*.jpg", "*.jpeg", "*.nef", "*.arw", "*.raf", "*.cr2", "*.orf", "*.rw2", "*.pef", "*.x3f",
                         "*.dng", "*.srw"],
                on_selection=self.on_file_selected
            )
        else:
            print("用户拒绝存储权限，无法选择图片")

    def action_open(self, instance):
        perms = self.get_needed_storage_permissions()
        if not perms:
            filechooser.open_file(
                filters=["*.jpg", "*.jpeg", "*.nef", "*.arw", "*.raf", "*.cr2", "*.orf", "*.rw2", "*.pef", "*.x3f",
                         "*.dng", "*.srw"],
                on_selection=self.on_file_selected
            )
        else:
            permissions.request_permissions(perms, callback=self.on_permission_callback)

    def on_file_selected(self, selection):
        if not selection:
            return
        self.img_path = selection[0]

        from urllib.parse import urlparse
        if self.img_path.startswith("content://"):
            parsed = urlparse(self.img_path)
            self.source_filename = os.path.basename(parsed.path) or "output.jpg"
        else:
            self.source_filename = os.path.basename(self.img_path)

        real_path = None
        try:
            real_path = copy_content_uri_to_temp(self.img_path)
            self.img = Image.open(real_path)
            self.raw_pil_img = ImageOps.exif_transpose(self.img)
            self.img = self.raw_pil_img.copy()
            self.exif_dict = piexif.load(real_path)
            self.rotate_angle = 0
            self.render_cache = []
            self.refresh_preview()
            if not self.is_loading_exif:
                self.is_loading_exif = True
                threading.Thread(target=self.read_exif_remote, args=(real_path,), daemon=True).start()
        except Exception as e:
            print(f"读取图片异常: {e}")
            self.img = None
            self.raw_pil_img = None
            self.exif_dict = None
            self.source_filename = None
        finally:
            if real_path is not None and os.path.exists(real_path):
                try:
                    os.unlink(real_path)
                except Exception:
                    pass

    def read_exif_remote(self, local_img_path):
        fake_file = None
        try:
            tmp_dir = storage.get_cache_dir()
            self.temp_fake_jpg = os.path.join(tmp_dir, "temp_fake.jpg")
            fake_file = self.temp_fake_jpg
            generate_empty_fake_jpg_with_raw_exif(local_img_path, self.temp_fake_jpg)
            with open(self.temp_fake_jpg, "rb") as f:
                files = {"file": (os.path.basename(self.temp_fake_jpg), f)}
                resp = requests.post(SERVER_URL, files=files, timeout=25)
            resp.raise_for_status()
            res_json = resp.json()
            code = res_json.get("code")
            data = res_json.get("data", {})
            if code != 200:
                return
            meta = STANDARD_META_SCHEMA.copy()
            meta.update(data)
            self.render_cache = [
                (meta["shoot_time"], "clock"),
                (f"{meta['camera_brand']}", "camera"),
                (meta["shutter_speed"], "shutter_lightning"),
                (meta["aperture"], "aperture"),
                (f"ISO {meta['iso']}", "iso_text"),
                (f"{meta['focal_length']}", "lens_ruler"),
                (meta["lens_full_name"], "tele_lens")
            ]
            self.update_ui_preview()
        except Exception as e:
            print("读取EXIF异常", e)
        finally:
            self.is_loading_exif = False
            if fake_file is not None and os.path.exists(fake_file):
                try:
                    os.unlink(fake_file)
                except Exception:
                    pass

    @mainthread
    def update_ui_preview(self):
        self.refresh_preview()

    def action_rotate(self, instance):
        if self.raw_pil_img is None:
            return
        self.rotate_angle = (self.rotate_angle + 90) % 360
        self.refresh_preview()

    def draw_watermark_on_image(self, pil_img):
        draw = ImageDraw.Draw(pil_img)
        data = self.render_cache
        cfg = DEFAULT_CONFIG
        try:
            font = ImageFont.truetype("/system/fonts/DroidSans.ttf", cfg["font_size"])
        except Exception:
            font = ImageFont.load_default(size=cfg["font_size"])

        if not data:
            draw.text((30, 30), "正在读取EXIF...", fill=(255, 255, 255), font=font)
            return pil_img

        pad = BOX_PADDING
        ls = LINE_SPACING
        img_w, img_h = pil_img.size
        lines = []
        maxw = 0
        totalh = 0
        for val, ico in data:
            bb = draw.textbbox((0, 0), val, font=font)
            ww = bb[2] - bb[0]
            hh = bb[3] - bb[1]
            lines.append((val, ico, ww, hh))
            if ww > maxw:
                maxw = ww
            totalh += ICON_SIZE + ls
        totalh -= ls

        bw = ICON_SIZE + ICON_TEXT_GAP + maxw + pad * 2
        bh = totalh + pad * 2
        box_x, box_y = 30, 30
        if box_x + bw > img_w:
            box_x = img_w - bw - 15
        if box_y + bh > img_h:
            box_y = img_h - bh - 15

        cy = box_y + pad
        text_color = tuple(cfg["font_color"])
        for val, ico, ww, hh in lines:
            ix = box_x + pad
            icon_top = cy
            icon_center_y = cy + ICON_SIZE / 2
            draw_icon(draw, ix, icon_top, ico, text_color)
            text_bbox = draw.textbbox((0, 0), val, font=font)
            text_height = text_bbox[3] - text_bbox[1]
            text_top_y = icon_center_y - (text_height / 2) - 5
            text_x = ix + ICON_SIZE + ICON_TEXT_GAP
            draw.text((text_x, text_top_y), val, fill=text_color, font=font)
            cy += ICON_SIZE + ls
        return pil_img

    def refresh_preview(self):
        if self.raw_pil_img is None:
            return
        rotated = self.raw_pil_img.rotate(self.rotate_angle, expand=True)
        blurred = rotated.filter(ImageFilter.GaussianBlur(radius=3))
        watermarked = self.draw_watermark_on_image(blurred.copy())
        self.processed_pil_img = watermarked
        w, h = watermarked.size
        buf = watermarked.tobytes()
        texture = Texture.create(size=(w, h))
        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        texture.flip_vertical()
        self.img_widget.texture = texture

    def action_save(self, instance):
        if not hasattr(self, "source_filename") or not self.source_filename:
            print("尚未打开图片，无法保存")
            return None
        if self.processed_pil_img is None:
            print("没有可保存图片")
            return None

        base_name, _ext = os.path.splitext(self.source_filename)
        out_filename = f"{base_name}_wm.jpg"
        saved_uri = save_image_to_public_album(self.processed_pil_img, out_filename)
        self.last_saved_uri = saved_uri
        return saved_uri

    def action_share(self, instance):
        if not self.last_saved_uri:
            self.last_saved_uri = self.action_save(None)
        if self.last_saved_uri:
            sharing.share_file(path=self.last_saved_uri, title="分享水印图片")


class ExifWatermarkApp(App):
    def build(self):
        self.title = "EXIF水印工具"
        return ExifWatermarkRoot()


if __name__ == "__main__":
    ExifWatermarkApp().run()
