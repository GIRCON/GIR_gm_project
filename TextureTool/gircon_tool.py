import colorsys
import math
import random
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageDraw, ImageOps, ImageTk
except ImportError as error:
    raise SystemExit("Нужна библиотека Pillow: pip install Pillow") from error

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    APP_BASE = TkinterDnD.Tk
    DRAG_AND_DROP_ENABLED = True
except ImportError:
    DND_FILES = None
    TkinterDnD = None
    APP_BASE = tk.Tk
    DRAG_AND_DROP_ENABLED = False


APP_BG = "#11151c"
PANEL_BG = "#1b2430"
CARD_BG = "#243041"
INPUT_BG = "#10161f"
TEXT_MAIN = "#edf2f7"
TEXT_MUTED = "#9fb0c6"
ACCENT = "#4ea8de"
ACCENT_ALT = "#91d7ff"
SUCCESS = "#62d2a2"
PREVIEW_BG = "#0e131a"
PREVIEW_EMPTY = "#6e8097"
DROP_BG = "#16202c"
DROP_BORDER = "#2c3c52"
PREVIEW_SIZE_LARGE = (430, 430)
PREVIEW_SIZE_SMALL = (270, 270)
VIEWER_BG = "#05080d"
IMAGE_TYPES = [
    ("Изображения", "*.png;*.jpg;*.jpeg;*.bmp;*.tga;*.tif;*.tiff;*.webp"),
    ("Все файлы", "*.*"),
]
SAVE_TYPES = [
    ("PNG", "*.png"),
    ("TGA", "*.tga"),
    ("BMP", "*.bmp"),
    ("Все файлы", "*.*"),
]
APP_VERSION = "1.2"
NOISE_FEATURE_LEVEL = 2
NOISE_PREVIEW_MAX_SIZE = 256
HIGH_BIT_GRAYSCALE_MODES = {"I;16", "I;16L", "I;16B", "I;16N"}
NOISE_PRESETS = [
    {
        "name": "Облака",
        "scale": 180.0,
        "octaves": 5,
        "persistence": 0.46,
        "lacunarity": 1.85,
        "contrast": 0.72,
        "rotation": 0.0,
        "seed": "cloud-soft",
        "low": "#405777",
        "high": "#d7e6ff",
        "hint": "Мягкие крупные пятна для неба, дыма и фоновых масок.",
    },
    {
        "name": "Гранит",
        "scale": 34.0,
        "octaves": 8,
        "persistence": 0.62,
        "lacunarity": 2.35,
        "contrast": 1.65,
        "rotation": 18.0,
        "seed": "granite-rock",
        "low": "#22252a",
        "high": "#d4d0c4",
        "hint": "Плотный зернистый шум под камень, скалы и roughness-карты.",
    },
    {
        "name": "Песок",
        "scale": 18.0,
        "octaves": 9,
        "persistence": 0.54,
        "lacunarity": 2.65,
        "contrast": 1.28,
        "rotation": 7.0,
        "seed": "sand-grain",
        "low": "#7b6743",
        "high": "#ead8a3",
        "hint": "Мелкое зерно для песка, пыли и слабых height-карт.",
    },
    {
        "name": "Мрамор",
        "scale": 92.0,
        "octaves": 7,
        "persistence": 0.58,
        "lacunarity": 2.15,
        "contrast": 2.15,
        "rotation": 35.0,
        "seed": "marble-vein",
        "low": "#20242f",
        "high": "#f2f1e9",
        "hint": "Контрастные плавные разводы как база для мрамора и прожилок.",
    },
    {
        "name": "Бетон",
        "scale": 64.0,
        "octaves": 6,
        "persistence": 0.50,
        "lacunarity": 2.05,
        "contrast": 1.05,
        "rotation": 0.0,
        "seed": "concrete-wall",
        "low": "#3b3b37",
        "high": "#b8b5aa",
        "hint": "Ровный строительный шум для бетона, штукатурки и грязи.",
    },
    {
        "name": "Поры",
        "scale": 24.0,
        "octaves": 7,
        "persistence": 0.70,
        "lacunarity": 2.10,
        "contrast": 2.55,
        "rotation": 0.0,
        "seed": "pores-mask",
        "low": "#121212",
        "high": "#d8d8d8",
        "hint": "Жёсткая маска с мелкими порами для dirt/ao/roughness.",
    },
    {
        "name": "Вода",
        "scale": 126.0,
        "octaves": 6,
        "persistence": 0.43,
        "lacunarity": 2.55,
        "contrast": 1.35,
        "rotation": 12.0,
        "seed": "water-waves",
        "low": "#123140",
        "high": "#7bd7f0",
        "hint": "Плавная волнистая основа для воды, льда и влажных масок.",
    },
    {
        "name": "Кора",
        "scale": 46.0,
        "octaves": 8,
        "persistence": 0.67,
        "lacunarity": 2.30,
        "contrast": 2.05,
        "rotation": 82.0,
        "seed": "bark-wood",
        "low": "#2c1d12",
        "high": "#aa7748",
        "hint": "Рваный контрастный шум для древесной коры и грубых материалов.",
    },
]


# Безопасная работа с 16-bit PNG. Прямой convert("L") у Pillow теряет точность таких карт.
def is_high_bit_grayscale(image):
    if image.mode in HIGH_BIT_GRAYSCALE_MODES:
        return True
    if image.mode == "I":
        minimum, maximum = image.getextrema()
        return minimum < 0 or maximum > 255
    return False


def grayscale_to_8bit(image):
    if is_high_bit_grayscale(image):
        source = image.convert("I") if image.mode != "I" else image
        width, height = source.size
        result = Image.new("L", (width, height))
        source_pixels = source.load()
        result_pixels = result.load()
        max_value = 65535 if image.mode in HIGH_BIT_GRAYSCALE_MODES else max(1, source.getextrema()[1])
        scale = 255.0 / max_value

        for y in range(height):
            for x in range(width):
                value = max(0, min(max_value, int(source_pixels[x, y])))
                result_pixels[x, y] = max(0, min(255, int(value * scale + 0.5)))

        return result

    return ImageOps.grayscale(image)


def display_ready_image(image):
    if is_high_bit_grayscale(image):
        return grayscale_to_8bit(image)
    if "A" in image.getbands():
        return image.convert("RGBA")
    if image.mode == "L":
        return image
    if image.mode not in ("RGB", "L"):
        return image.convert("RGB")
    return image


def height_source_for_normals(source_image):
    if is_high_bit_grayscale(source_image):
        source = source_image.convert("I") if source_image.mode != "I" else source_image
        max_value = 65535 if source_image.mode in HIGH_BIT_GRAYSCALE_MODES else max(1, source.getextrema()[1])
        return source, max_value

    return ImageOps.grayscale(source_image), 255


def create_normal_map(source_image, strength, convention, invert_height, preserve_alpha):
    height_map, max_value = height_source_for_normals(source_image)
    width, height = height_map.size
    pixels = height_map.load()
    source_rgba = source_image.convert("RGBA")
    alpha_channel = source_rgba.getchannel("A") if preserve_alpha else None
    alpha_pixels = alpha_channel.load() if alpha_channel else None

    result = Image.new("RGBA" if preserve_alpha else "RGB", (width, height))
    result_pixels = result.load()

    for y in range(height):
        y_top = max(y - 1, 0)
        y_bottom = min(y + 1, height - 1)

        for x in range(width):
            x_left = max(x - 1, 0)
            x_right = min(x + 1, width - 1)

            left = max(0.0, min(1.0, pixels[x_left, y] / max_value))
            right = max(0.0, min(1.0, pixels[x_right, y] / max_value))
            top = max(0.0, min(1.0, pixels[x, y_top] / max_value))
            bottom = max(0.0, min(1.0, pixels[x, y_bottom] / max_value))

            if invert_height:
                left = 1.0 - left
                right = 1.0 - right
                top = 1.0 - top
                bottom = 1.0 - bottom

            normal_x = (left - right) * strength
            normal_y = (top - bottom) * strength

            if convention == "DirectX":
                normal_y = -normal_y

            length = math.sqrt(normal_x * normal_x + normal_y * normal_y + 1.0)
            normal_x /= length
            normal_y /= length
            normal_z = 1.0 / length

            red = int((normal_x * 0.5 + 0.5) * 255)
            green = int((normal_y * 0.5 + 0.5) * 255)
            blue = int((normal_z * 0.5 + 0.5) * 255)

            if preserve_alpha and alpha_pixels:
                result_pixels[x, y] = (red, green, blue, alpha_pixels[x, y])
            else:
                result_pixels[x, y] = (red, green, blue)

    return result


# Сборка одного RGBA-изображения из отдельных чёрно-белых каналов.
def build_argb_image(r_image, g_image, b_image, alpha_mode, alpha_value, alpha_image, alpha_opacity, invert_alpha):
    base_r = grayscale_to_8bit(r_image)
    size = base_r.size
    resample = Image.Resampling.LANCZOS

    base_g = grayscale_to_8bit(g_image).resize(size, resample)
    base_b = grayscale_to_8bit(b_image).resize(size, resample)

    if alpha_mode == "image":
        if alpha_image is None:
            raise ValueError("Для режима alpha из изображения сначала загрузите alpha-карту.")
        base_a = grayscale_to_8bit(alpha_image).resize(size, resample)
    else:
        base_a = Image.new("L", size, color=int(alpha_value))

    if invert_alpha:
        base_a = ImageOps.invert(base_a)

    opacity_scale = max(0, min(200, int(alpha_opacity))) / 100
    if opacity_scale != 1:
        base_a = base_a.point(lambda pixel: min(255, int(pixel * opacity_scale)))

    return Image.merge("RGBA", (base_r, base_g, base_b, base_a))


# Разбор обычного RGBA-изображения на отдельные каналы.
def split_rgba_image(source_image):
    if is_high_bit_grayscale(source_image):
        gray = grayscale_to_8bit(source_image)
        alpha = Image.new("L", gray.size, 255)
        return {
            "R": gray.copy(),
            "G": gray.copy(),
            "B": gray.copy(),
            "A": alpha,
        }

    rgba_image = source_image.convert("RGBA")
    red, green, blue, alpha = rgba_image.split()
    return {
        "R": red,
        "G": green,
        "B": blue,
        "A": alpha,
    }


def seed_from_text(seed_text):
    text = str(seed_text).strip()
    if not text:
        return random_seed_value()

    try:
        return int(text) & 0xFFFFFFFF
    except ValueError:
        value = 2166136261
        for char in text:
            value ^= ord(char)
            value = (value * 16777619) & 0xFFFFFFFF
        return value


def random_seed_value():
    return random.randint(0, 2**31 - 1)


def build_permutation(seed):
    rng = random.Random(seed)
    values = list(range(256))
    rng.shuffle(values)
    return values * 2


def fade(value):
    return value * value * value * (value * (value * 6 - 15) + 10)


def lerp(start, end, amount):
    return start + amount * (end - start)


def gradient(hash_value, x, y):
    h = hash_value & 7
    u = x if h < 4 else y
    v = y if h < 4 else x
    return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)


def perlin_2d(x, y, permutation):
    x_floor = math.floor(x)
    y_floor = math.floor(y)
    xi = x_floor & 255
    yi = y_floor & 255
    xf = x - x_floor
    yf = y - y_floor
    u = fade(xf)
    v = fade(yf)

    aa = permutation[permutation[xi] + yi]
    ab = permutation[permutation[xi] + yi + 1]
    ba = permutation[permutation[xi + 1] + yi]
    bb = permutation[permutation[xi + 1] + yi + 1]

    x1 = lerp(gradient(aa, xf, yf), gradient(ba, xf - 1, yf), u)
    x2 = lerp(gradient(ab, xf, yf - 1), gradient(bb, xf - 1, yf - 1), u)
    return lerp(x1, x2, v)


def generate_perlin_noise_image(width, height, scale, octaves, persistence, lacunarity, contrast, seed, rotation=0.0):
    width = max(16, int(width))
    height = max(16, int(height))
    scale = max(1.0, float(scale))
    octaves = max(1, min(10, int(octaves)))
    persistence = max(0.05, min(0.95, float(persistence)))
    lacunarity = max(1.1, min(4.0, float(lacunarity)))
    contrast = max(0.1, min(5.0, float(contrast)))
    angle = math.radians(float(rotation) % 360.0)
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    center_x = width / 2.0
    center_y = height / 2.0
    permutation = build_permutation(seed)
    values = []
    minimum = float("inf")
    maximum = float("-inf")

    for y in range(height):
        row = []
        for x in range(width):
            local_x = x - center_x
            local_y = y - center_y
            sample_x = local_x * cos_angle - local_y * sin_angle + center_x
            sample_y = local_x * sin_angle + local_y * cos_angle + center_y
            amplitude = 1.0
            frequency = 1.0
            total = 0.0
            max_amplitude = 0.0

            for _octave in range(octaves):
                total += perlin_2d((sample_x / scale) * frequency, (sample_y / scale) * frequency, permutation) * amplitude
                max_amplitude += amplitude
                amplitude *= persistence
                frequency *= lacunarity

            value = total / max_amplitude if max_amplitude else 0.0
            row.append(value)
            minimum = min(minimum, value)
            maximum = max(maximum, value)
        values.append(row)

    result = Image.new("L", (width, height))
    pixels = result.load()
    value_range = maximum - minimum

    for y, row in enumerate(values):
        for x, value in enumerate(row):
            normalized = 0.5 if value_range <= 0.000001 else (value - minimum) / value_range
            normalized = 0.5 + (normalized - 0.5) * contrast
            pixels[x, y] = max(0, min(255, int(normalized * 255 + 0.5)))

    return result


def hex_to_rgb(color):
    if isinstance(color, tuple):
        return color

    value = color.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def rgb_to_hex(color):
    red, green, blue = color
    return f"#{red:02x}{green:02x}{blue:02x}"


def clamp_rgb_value(value):
    return max(0, min(255, int(round(value))))


def colorize_noise(image, low_color, high_color):
    low = hex_to_rgb(low_color)
    high = hex_to_rgb(high_color)
    source = ImageOps.autocontrast(image.convert("L"))
    result = Image.new("RGB", source.size)
    source_pixels = source.load()
    result_pixels = result.load()

    for y in range(source.height):
        for x in range(source.width):
            amount = source_pixels[x, y] / 255.0
            result_pixels[x, y] = tuple(int(low[channel] + (high[channel] - low[channel]) * amount) for channel in range(3))

    return result


def create_noise_preset_thumbnail(preset, size=(48, 48)):
    image = generate_perlin_noise_image(
        size[0],
        size[1],
        scale=max(6.0, float(preset["scale"]) / 5.0),
        octaves=preset["octaves"],
        persistence=preset["persistence"],
        lacunarity=preset["lacunarity"],
        contrast=preset["contrast"],
        seed=seed_from_text(preset["seed"]),
        rotation=preset.get("rotation", 0.0),
    )
    return colorize_noise(image, preset["low"], preset["high"])


# Карточка предпросмотра для изображения и его краткой информации.
class PreviewCard(ttk.Frame):
    def __init__(self, master, title, preview_size, empty_info="Ожидание изображения"):
        super().__init__(master, style="Card.TFrame", padding=12)
        self.preview_size = preview_size
        self.empty_info = empty_info
        self.current_image = None
        self.current_checker = False
        self.open_callback = None
        self.info_var = tk.StringVar(value=empty_info)
        self.title_label = ttk.Label(self, text=title, style="CardTitle.TLabel")
        self.title_label.pack(anchor="w")
        self.canvas = tk.Label(
            self,
            bg=PREVIEW_BG,
            fg=PREVIEW_EMPTY,
            text="Нет изображения",
            font=("Segoe UI", 11),
            width=preview_size[0] // 10,
            height=preview_size[1] // 22,
            bd=0,
            relief="flat",
        )
        self.canvas.pack(fill="both", expand=True, pady=(10, 10))
        self.info_label = ttk.Label(self, textvariable=self.info_var, style="Muted.TLabel", wraplength=preview_size[0] - 20)
        self.info_label.pack(anchor="w")

    def clear(self, info_text=None):
        self.current_image = None
        self.current_checker = False
        self.canvas.configure(image="", text="Нет изображения")
        self.canvas.image = None
        self.info_var.set(info_text or self.empty_info)

    def drop_widgets(self):
        return [self, self.title_label, self.canvas, self.info_label]

    def bind_open(self, callback):
        self.open_callback = callback
        for widget in self.drop_widgets():
            widget.bind("<Double-Button-1>", self._open_image)

    def _open_image(self, _event=None):
        if self.current_image is not None and self.open_callback is not None:
            self.open_callback(self.current_image, self.info_var.get(), self.current_checker)

    def show_image(self, image, info_text, checker=False):
        if image is None:
            self.clear(info_text)
            return

        self.current_image = image.copy()
        self.current_checker = checker
        preview = prepare_preview_image(image, self.preview_size, checker=checker)
        photo = ImageTk.PhotoImage(preview)
        self.canvas.configure(image=photo, text="")
        self.canvas.image = photo
        self.info_var.set(info_text)


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip_window or not self.text:
            return

        x = (event.x_root if event else self.widget.winfo_rootx()) + 14
        y = (event.y_root if event else self.widget.winfo_rooty()) + 18
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tip_window,
            text=self.text,
            justify="left",
            bg="#f5f0d8",
            fg="#121212",
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=6,
            wraplength=280,
            font=("Segoe UI", 9),
        )
        label.pack()

    def hide(self, _event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


def add_tooltip(widget, text):
    ToolTip(widget, text)
    return widget


class ColorWheelPicker(tk.Toplevel):
    def __init__(self, master, initial_color, on_color, title_text):
        super().__init__(master)
        self.on_color = on_color
        self.wheel_size = 220
        self.padding = 10
        self.radius = self.wheel_size / 2
        red, green, blue = initial_color
        hue, saturation, value = colorsys.rgb_to_hsv(red / 255.0, green / 255.0, blue / 255.0)
        self.hue = hue
        self.saturation = saturation
        self.value_var = tk.DoubleVar(value=max(0.05, value))
        self.selected_color = tuple(clamp_rgb_value(channel) for channel in initial_color)
        self.photo = None

        self.title(title_text)
        self.configure(bg=PANEL_BG)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        root = ttk.Frame(self, style="Panel.TFrame", padding=14)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="Выберите цвет на RGB-круге", style="PanelLabel.TLabel").pack(anchor="w")
        self.canvas = tk.Canvas(
            root,
            width=self.wheel_size + self.padding * 2,
            height=self.wheel_size + self.padding * 2,
            bg=PANEL_BG,
            highlightthickness=0,
            cursor="crosshair",
        )
        self.canvas.pack(pady=(10, 8))
        self.canvas.bind("<Button-1>", self._on_wheel_pick)
        self.canvas.bind("<B1-Motion>", self._on_wheel_pick)

        ttk.Label(root, text="Яркость", style="PanelLabel.TLabel").pack(anchor="w")
        ttk.Scale(root, from_=0.05, to=1.0, variable=self.value_var, command=lambda _value: self._on_value_changed()).pack(fill="x", pady=(6, 8))

        preview_row = ttk.Frame(root, style="Panel.TFrame")
        preview_row.pack(fill="x", pady=(2, 10))
        self.swatch = tk.Label(preview_row, width=6, height=2, bg=rgb_to_hex(self.selected_color), bd=1, relief="solid")
        self.swatch.pack(side="left")
        self.rgb_label = ttk.Label(preview_row, text=self._rgb_text(), style="PanelLabel.TLabel")
        self.rgb_label.pack(side="left", padx=(10, 0))

        ttk.Button(root, text="Закрыть", command=self.destroy, style="Ghost.TButton").pack(fill="x")
        self.bind("<Escape>", lambda _event: self.destroy())
        self._render_wheel()

    def _rgb_text(self):
        red, green, blue = self.selected_color
        return f"RGB: {red}, {green}, {blue}"

    def _render_wheel(self):
        value = float(self.value_var.get())
        image = Image.new("RGBA", (self.wheel_size + self.padding * 2, self.wheel_size + self.padding * 2), (0, 0, 0, 0))
        pixels = image.load()
        center = self.padding + self.radius

        for y in range(image.height):
            for x in range(image.width):
                dx = x - center
                dy = y - center
                distance = math.sqrt(dx * dx + dy * dy)
                if distance > self.radius:
                    pixels[x, y] = (27, 36, 48, 255)
                    continue

                hue = (math.atan2(dy, dx) / (2 * math.pi)) % 1.0
                saturation = min(1.0, distance / self.radius)
                red, green, blue = colorsys.hsv_to_rgb(hue, saturation, value)
                pixels[x, y] = (clamp_rgb_value(red * 255), clamp_rgb_value(green * 255), clamp_rgb_value(blue * 255), 255)

        draw = ImageDraw.Draw(image)
        marker_x, marker_y = self._marker_position()
        draw.ellipse((marker_x - 5, marker_y - 5, marker_x + 5, marker_y + 5), outline="white", width=2)
        draw.ellipse((marker_x - 7, marker_y - 7, marker_x + 7, marker_y + 7), outline="black", width=1)
        self.photo = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")

    def _marker_position(self):
        angle = self.hue * 2 * math.pi
        distance = self.saturation * self.radius
        center = self.padding + self.radius
        return center + math.cos(angle) * distance, center + math.sin(angle) * distance

    def _on_wheel_pick(self, event):
        center = self.padding + self.radius
        dx = event.x - center
        dy = event.y - center
        distance = math.sqrt(dx * dx + dy * dy)
        if distance > self.radius:
            return

        self.hue = (math.atan2(dy, dx) / (2 * math.pi)) % 1.0
        self.saturation = min(1.0, distance / self.radius)
        self._apply_current_color()
        self._render_wheel()

    def _on_value_changed(self):
        self._apply_current_color()
        self._render_wheel()

    def _apply_current_color(self):
        red, green, blue = colorsys.hsv_to_rgb(self.hue, self.saturation, float(self.value_var.get()))
        self.selected_color = (clamp_rgb_value(red * 255), clamp_rgb_value(green * 255), clamp_rgb_value(blue * 255))
        self.swatch.configure(bg=rgb_to_hex(self.selected_color))
        self.rgb_label.configure(text=self._rgb_text())
        self.on_color(self.selected_color)


# Прокручиваемая левая панель с настройками и кнопками.
class ScrollablePanel(ttk.Frame):
    def __init__(self, master, width):
        super().__init__(master, style="Panel.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            self,
            bg=PANEL_BG,
            highlightthickness=0,
            bd=0,
            width=width,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.content = ttk.Frame(self.canvas, style="Panel.TFrame", padding=16)
        self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.content.bind("<Configure>", self._sync_scroll_region)
        self.canvas.bind("<Configure>", self._sync_content_width)
        self.content.bind("<Enter>", self._bind_mousewheel)
        self.content.bind("<Leave>", self._unbind_mousewheel)

    def _sync_scroll_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _sync_content_width(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _bind_mousewheel(self, _event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event=None):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        delta = -1 * int(event.delta / 120) if event.delta else 0
        self.canvas.yview_scroll(delta, "units")


# Полноэкранный просмотрщик с zoom, pan, миникартой и индикатором масштаба.
class ImageViewer(tk.Toplevel):
    def __init__(self, master, image, title_text, checker=False):
        super().__init__(master)
        self.original_image = image.copy()
        self.title(title_text or "Image Viewer")
        self.configure(bg=VIEWER_BG)
        self.attributes("-fullscreen", True)

        self.zoom = 1.0
        self.zoom_initialized = False
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.drag_position = None
        self.image_item = None
        self.rendered_photo = None
        self.current_width = 0
        self.current_height = 0
        self.draw_x = 0
        self.draw_y = 0
        self.display_image = self._prepare_image(self.original_image, checker)

        self.canvas = tk.Canvas(self, bg=VIEWER_BG, highlightthickness=0, bd=0, cursor="fleur")
        self.canvas.pack(fill="both", expand=True)

        self.hint_label = tk.Label(
            self,
            text="Esc - закрыть | Колесо - zoom | Удержание ЛКМ - перемещение",
            bg="#0b1017",
            fg=TEXT_MUTED,
            font=("Segoe UI", 11),
            padx=14,
            pady=8,
        )
        self.hint_label.place(relx=0.5, y=18, anchor="n")

        self.scale_label = tk.Label(
            self,
            text="100%",
            bg="#0b1017",
            fg=TEXT_MAIN,
            font=("Segoe UI Semibold", 11),
            padx=12,
            pady=6,
        )
        self.scale_label.place(relx=1.0, x=-20, y=18, anchor="ne")

        self.minimap = tk.Canvas(self, width=220, height=150, bg="#0b1017", highlightthickness=1, highlightbackground="#334155", bd=0)
        self.minimap.place(relx=1.0, rely=1.0, x=-20, y=-20, anchor="se")

        self.canvas.bind("<Configure>", lambda _event: self.render_image(force=True))
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._drag_image)
        self.canvas.bind("<ButtonRelease-1>", lambda _event: self._stop_drag())
        self.canvas.bind("<Double-Button-1>", lambda _event: self._toggle_fullscreen())
        self.bind("<Escape>", lambda _event: self.destroy())
        self.bind("<F11>", lambda _event: self._toggle_fullscreen())

        self.after(10, lambda: self.render_image(force=True))

    def _prepare_image(self, image, checker):
        prepared = display_ready_image(image).copy()

        if checker and "A" in prepared.getbands():
            background = create_checkerboard(prepared.size, cell=24)
            background.paste(prepared, mask=prepared.getchannel("A"))
            prepared = background
        elif prepared.mode == "RGBA":
            prepared = prepared.convert("RGB")
        elif prepared.mode == "L":
            prepared = prepared.convert("RGB")
        elif prepared.mode not in ("RGB", "L"):
            prepared = prepared.convert("RGB")

        return prepared

    def _toggle_fullscreen(self):
        current_state = bool(self.attributes("-fullscreen"))
        self.attributes("-fullscreen", not current_state)
        self.after(10, lambda: self.render_image(force=True))

    def _start_drag(self, event):
        self.drag_position = (event.x, event.y)

    def _drag_image(self, event):
        if self.drag_position is None:
            return

        delta_x = event.x - self.drag_position[0]
        delta_y = event.y - self.drag_position[1]
        self.drag_position = (event.x, event.y)
        self.offset_x += delta_x
        self.offset_y += delta_y
        self._update_image_position()
        self._update_minimap()

    def _stop_drag(self):
        self.drag_position = None

    def _on_mousewheel(self, event):
        if event.delta == 0:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            return

        zoom_factor = 1.15 if event.delta > 0 else 1 / 1.15
        old_zoom = self.zoom
        new_zoom = min(20.0, max(0.1, self.zoom * zoom_factor))
        if abs(new_zoom - old_zoom) < 0.0001:
            return

        center_x = canvas_width / 2
        center_y = canvas_height / 2
        self.offset_x = event.x - center_x - (new_zoom / old_zoom) * (event.x - center_x - self.offset_x)
        self.offset_y = event.y - center_y - (new_zoom / old_zoom) * (event.y - center_y - self.offset_y)
        self.zoom = new_zoom
        self.render_image(force=True)

    def _update_image_position(self):
        if self.image_item is None:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        self.draw_x = int((canvas_width - self.current_width) / 2 + self.offset_x)
        self.draw_y = int((canvas_height - self.current_height) / 2 + self.offset_y)
        self.canvas.coords(self.image_item, self.draw_x, self.draw_y)
        self._update_scale_label()

    def _update_scale_label(self):
        self.scale_label.configure(text=f"Масштаб: {int(self.zoom * 100)}%")

    def _update_minimap(self):
        map_width = int(self.minimap.winfo_width())
        map_height = int(self.minimap.winfo_height())
        if map_width <= 1 or map_height <= 1:
            return

        self.minimap.delete("all")
        image_width = self.display_image.width
        image_height = self.display_image.height
        fit = min((map_width - 20) / image_width, (map_height - 20) / image_height)
        fit = max(0.01, fit)
        mini_width = image_width * fit
        mini_height = image_height * fit
        base_x = (map_width - mini_width) / 2
        base_y = (map_height - mini_height) / 2

        self.minimap.create_rectangle(base_x, base_y, base_x + mini_width, base_y + mini_height, outline="#667892", width=1)

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        left = max(0.0, (-self.draw_x) / self.zoom)
        top = max(0.0, (-self.draw_y) / self.zoom)
        right = min(image_width, (canvas_width - self.draw_x) / self.zoom)
        bottom = min(image_height, (canvas_height - self.draw_y) / self.zoom)

        if right > left and bottom > top:
            self.minimap.create_rectangle(
                base_x + left * fit,
                base_y + top * fit,
                base_x + right * fit,
                base_y + bottom * fit,
                outline=ACCENT_ALT,
                width=2,
            )

    def render_image(self, force=False):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            return

        if not self.zoom_initialized:
            fit_zoom = min(canvas_width / self.display_image.width, canvas_height / self.display_image.height)
            self.zoom = min(1.0, max(0.1, fit_zoom))
            self.zoom_initialized = True

        resized_width = max(1, int(self.display_image.width * self.zoom))
        resized_height = max(1, int(self.display_image.height * self.zoom))

        if force or resized_width != self.current_width or resized_height != self.current_height or self.image_item is None:
            resized = self.display_image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)
            self.rendered_photo = ImageTk.PhotoImage(resized)
            self.current_width = resized_width
            self.current_height = resized_height

            if self.image_item is None:
                self.image_item = self.canvas.create_image(0, 0, image=self.rendered_photo, anchor="nw")
            else:
                self.canvas.itemconfigure(self.image_item, image=self.rendered_photo)

        self._update_image_position()
        self._update_minimap()


def prepare_preview_image(image, size, checker=False):
    preview = display_ready_image(image).copy()

    if checker and "A" in preview.getbands():
        background = create_checkerboard(preview.size)
        background.paste(preview, mask=preview.getchannel("A"))
        preview = background
    elif preview.mode == "RGBA":
        preview = preview.convert("RGB")
    elif preview.mode not in ("RGB", "L"):
        preview = preview.convert("RGB")

    if preview.mode == "L":
        preview = preview.convert("RGB")

    preview = ImageOps.contain(preview, size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, PREVIEW_BG)
    offset_x = (size[0] - preview.width) // 2
    offset_y = (size[1] - preview.height) // 2
    canvas.paste(preview, (offset_x, offset_y))
    return canvas


def create_checkerboard(size, cell=18):
    image = Image.new("RGB", size, "#202a38")
    draw = ImageDraw.Draw(image)

    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if ((x // cell) + (y // cell)) % 2 == 0:
                draw.rectangle((x, y, x + cell, y + cell), fill="#314154")

    return image


def image_info_text(path, image):
    file_name = Path(path).name if path else "Без имени"
    bit_depth = "16-bit" if is_high_bit_grayscale(image) else "8-bit"
    return f"{file_name} | {image.width}x{image.height} | {image.mode} | {bit_depth}"


class GirconTool(APP_BASE):
    def __init__(self):
        super().__init__()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = min(1320, max(980, screen_width - 80))
        window_height = min(820, max(620, screen_height - 140))
        position_x = max(20, (screen_width - window_width) // 2)
        position_y = max(20, (screen_height - window_height) // 2)

        self.title(f"Texture Tool {APP_VERSION}")
        self.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
        self.minsize(
            min(980, max(860, screen_width - 180)),
            min(680, max(600, screen_height - 220)),
        )
        self.configure(bg=APP_BG)

        # Переменные состояния для режима normal map.
        self.height_source = None
        self.height_result = None
        self.height_path = ""

        # Переменные состояния для режима сборки aRGB.
        self.channel_images = {"R": None, "G": None, "B": None, "A": None}
        self.channel_paths = {"R": "", "G": "", "B": "", "A": ""}
        self.argb_result = None

        # Переменные состояния для режима распаковки RGBA.
        self.unpack_source = None
        self.unpack_path = ""
        self.unpack_channels = {"R": None, "G": None, "B": None, "A": None}

        # Переменные состояния для генератора шума Перлина.
        self.noise_result = None
        self.noise_refresh_after_id = None
        self.noise_preset_images = []
        self.noise_width_var = tk.StringVar(value="512")
        self.noise_height_var = tk.StringVar(value="512")
        self.noise_scale_var = tk.DoubleVar(value=96.0)
        self.noise_scale_text = tk.StringVar(value="96.0")
        self.noise_octaves_var = tk.DoubleVar(value=6.0)
        self.noise_octaves_text = tk.StringVar(value="6")
        self.noise_persistence_var = tk.DoubleVar(value=0.50)
        self.noise_persistence_text = tk.StringVar(value="0.50")
        self.noise_lacunarity_var = tk.DoubleVar(value=2.00)
        self.noise_lacunarity_text = tk.StringVar(value="2.00")
        self.noise_contrast_var = tk.DoubleVar(value=1.00)
        self.noise_contrast_text = tk.StringVar(value="1.00")
        self.noise_rotation_var = tk.DoubleVar(value=0.0)
        self.noise_rotation_text = tk.StringVar(value="0°")
        self.noise_seed_var = tk.StringVar(value=str(random_seed_value()))
        self.noise_low_r_var = tk.StringVar(value="0")
        self.noise_low_g_var = tk.StringVar(value="0")
        self.noise_low_b_var = tk.StringVar(value="0")
        self.noise_high_r_var = tk.StringVar(value="255")
        self.noise_high_g_var = tk.StringVar(value="255")
        self.noise_high_b_var = tk.StringVar(value="255")
        self.noise_low_swatch = None
        self.noise_high_swatch = None
        self.noise_result_is_preview = False
        self.noise_result_full_size = (0, 0)

        ready_text = "Готово к работе. Перетаскивание файлов включено." if DRAG_AND_DROP_ENABLED else "Готово к работе. Drag-and-drop отключён: установите tkinterdnd2."
        self.status_var = tk.StringVar(value=ready_text)
        self.height_strength_var = tk.DoubleVar(value=4.0)
        self.height_strength_text = tk.StringVar(value="4.0")
        self.height_convention_var = tk.StringVar(value="OpenGL")
        self.height_invert_var = tk.BooleanVar(value=False)
        self.height_alpha_var = tk.BooleanVar(value=False)

        self.alpha_mode_var = tk.StringVar(value="slider")
        self.alpha_value_var = tk.IntVar(value=255)
        self.alpha_value_text = tk.StringVar(value="255")
        self.alpha_opacity_var = tk.IntVar(value=100)
        self.alpha_opacity_text = tk.StringVar(value="100%")
        self.alpha_invert_var = tk.BooleanVar(value=False)
        self.unpack_prefix_var = tk.StringVar(value="split_")

        self._build_style()
        self._build_layout()
        self._connect_traces()
        self._setup_drop_targets()

    def _build_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame", background=APP_BG)
        style.configure("Panel.TFrame", background=PANEL_BG)
        style.configure("Card.TFrame", background=CARD_BG)
        style.configure("TLabel", background=APP_BG, foreground=TEXT_MAIN, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=APP_BG, foreground=TEXT_MAIN, font=("Segoe UI Semibold", 22))
        style.configure("Subtitle.TLabel", background=APP_BG, foreground=TEXT_MUTED, font=("Segoe UI", 10))
        style.configure("Section.TLabelframe", background=PANEL_BG, foreground=TEXT_MAIN)
        style.configure("Section.TLabelframe.Label", background=PANEL_BG, foreground=ACCENT_ALT, font=("Segoe UI Semibold", 11))
        style.configure("CardTitle.TLabel", background=CARD_BG, foreground=TEXT_MAIN, font=("Segoe UI Semibold", 12))
        style.configure("Muted.TLabel", background=CARD_BG, foreground=TEXT_MUTED, font=("Segoe UI", 9))
        style.configure("PanelLabel.TLabel", background=PANEL_BG, foreground=TEXT_MAIN, font=("Segoe UI", 10))
        style.configure("Accent.TButton", background=ACCENT, foreground="#071018", font=("Segoe UI Semibold", 10), padding=(12, 8), borderwidth=0)
        style.map("Accent.TButton", background=[("active", ACCENT_ALT), ("pressed", "#3796ce")])
        style.configure("Ghost.TButton", background=CARD_BG, foreground=TEXT_MAIN, padding=(12, 8), borderwidth=0)
        style.map("Ghost.TButton", background=[("active", "#2f4055"), ("pressed", "#1c2838")])
        style.configure("TEntry", fieldbackground=INPUT_BG, foreground=TEXT_MAIN, insertcolor=TEXT_MAIN, bordercolor="#334155")
        style.configure("Readonly.TEntry", fieldbackground=INPUT_BG, foreground=TEXT_MAIN, bordercolor="#334155")
        style.configure("TCombobox", fieldbackground=INPUT_BG, background=INPUT_BG, foreground=TEXT_MAIN, arrowcolor=TEXT_MAIN)
        style.configure("TCheckbutton", background=PANEL_BG, foreground=TEXT_MAIN)
        style.configure("TRadiobutton", background=PANEL_BG, foreground=TEXT_MAIN)
        style.configure(
            "TNotebook",
            background=APP_BG,
            borderwidth=0,
            tabmargins=(0, 0, 0, 0),
        )
        style.configure("TNotebook.Tab", background=CARD_BG, foreground=TEXT_MUTED, padding=(18, 10), font=("Segoe UI Semibold", 10))
        style.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", "#071018")])
        style.configure("Status.TLabel", background=APP_BG, foreground=SUCCESS, font=("Segoe UI", 10))

    def _build_layout(self):
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text=f"Texture Tool {APP_VERSION}", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Normal map, сборка aRGB, распаковка RGBA и генерация профессионального шума Перлина.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        notebook = ttk.Notebook(root)
        notebook.grid(row=1, column=0, sticky="nsew")

        self.height_tab = ttk.Frame(notebook)
        self.argb_tab = ttk.Frame(notebook)
        self.unpack_tab = ttk.Frame(notebook)
        self.noise_tab = ttk.Frame(notebook)
        notebook.add(self.height_tab, text="Height -> Normal")
        notebook.add(self.argb_tab, text="BW -> aRGB")
        notebook.add(self.unpack_tab, text="RGBA -> Channels")
        notebook.add(self.noise_tab, text="Perlin Noise")

        self._build_height_tab()
        self._build_argb_tab()
        self._build_unpack_tab()
        self._build_noise_tab()
        self._bind_preview_viewers()

        status_bar = ttk.Label(root, textvariable=self.status_var, style="Status.TLabel")
        status_bar.grid(row=2, column=0, sticky="ew", pady=(12, 0))

    def _build_height_tab(self):
        # Вкладка генерации normal map из карты высот.
        self.height_tab.columnconfigure(0, weight=0)
        self.height_tab.columnconfigure(1, weight=1)
        self.height_tab.rowconfigure(0, weight=1)

        controls_panel = ScrollablePanel(self.height_tab, width=360)
        controls_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 14), pady=6)
        controls = controls_panel.content

        preview = ttk.Frame(self.height_tab)
        preview.grid(row=0, column=1, sticky="nsew", pady=6)
        preview.columnconfigure(0, weight=1)
        preview.columnconfigure(1, weight=1)
        preview.rowconfigure(0, weight=1)

        source_box = ttk.LabelFrame(controls, text="Источник", style="Section.TLabelframe", padding=14)
        source_box.pack(fill="x")

        ttk.Label(source_box, text="Карта высот", style="PanelLabel.TLabel").pack(anchor="w")
        self.height_path_entry = ttk.Entry(source_box, state="readonly", style="Readonly.TEntry")
        self.height_path_entry.pack(fill="x", pady=(8, 10))
        ttk.Button(source_box, text="Открыть изображение", command=self.load_height_image, style="Ghost.TButton").pack(fill="x")
        ttk.Label(
            source_box,
            text="Можно перетащить файл прямо на левую карточку предпросмотра.",
            style="PanelLabel.TLabel",
            wraplength=300,
            justify="left",
        ).pack(anchor="w", pady=(10, 0))

        options_box = ttk.LabelFrame(controls, text="Параметры normal map", style="Section.TLabelframe", padding=14)
        options_box.pack(fill="x", pady=(14, 0))

        ttk.Label(options_box, text="Сила рельефа", style="PanelLabel.TLabel").pack(anchor="w")
        ttk.Scale(options_box, from_=0.1, to=100.0, variable=self.height_strength_var).pack(fill="x", pady=(8, 4))
        ttk.Label(options_box, textvariable=self.height_strength_text, style="PanelLabel.TLabel").pack(anchor="w")

        ttk.Label(options_box, text="Формат", style="PanelLabel.TLabel").pack(anchor="w", pady=(12, 0))
        convention_box = ttk.Combobox(
            options_box,
            textvariable=self.height_convention_var,
            values=("OpenGL", "DirectX"),
            state="readonly",
        )
        convention_box.pack(fill="x", pady=(8, 0))

        ttk.Checkbutton(options_box, text="Инвертировать карту высот", variable=self.height_invert_var).pack(anchor="w", pady=(12, 0))
        ttk.Checkbutton(options_box, text="Сохранить alpha из исходника", variable=self.height_alpha_var).pack(anchor="w", pady=(6, 0))

        info_box = ttk.LabelFrame(controls, text="Что делает режим", style="Section.TLabelframe", padding=14)
        info_box.pack(fill="x", pady=(14, 0))
        ttk.Label(
            info_box,
            text="OpenGL и DirectX отличаются только зелёным каналом. Если normal map выглядит 'вдавленной', просто переключите формат.",
            style="PanelLabel.TLabel",
            wraplength=300,
            justify="left",
        ).pack(anchor="w")

        actions_box = ttk.Frame(controls, style="Panel.TFrame")
        actions_box.pack(fill="x", pady=(14, 0))
        ttk.Button(actions_box, text="Сгенерировать normal map", command=self.generate_height_result, style="Accent.TButton").pack(fill="x")
        ttk.Button(actions_box, text="Сохранить результат", command=self.save_height_result, style="Ghost.TButton").pack(fill="x", pady=(10, 0))

        self.height_source_card = PreviewCard(
            preview,
            "Исходная карта высот",
            PREVIEW_SIZE_LARGE,
            empty_info="Перетащите карту высот сюда или откройте её кнопкой слева",
        )
        self.height_source_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.height_result_card = PreviewCard(
            preview,
            "Результат: normal map",
            PREVIEW_SIZE_LARGE,
            empty_info="После генерации normal map результат появится здесь",
        )
        self.height_result_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.height_source_card.clear()
        self.height_result_card.clear()

    def _build_argb_tab(self):
        # Вкладка сборки одного aRGB изображения из отдельных каналов.
        self.argb_tab.columnconfigure(0, weight=0)
        self.argb_tab.columnconfigure(1, weight=1)
        self.argb_tab.rowconfigure(0, weight=1)

        controls_panel = ScrollablePanel(self.argb_tab, width=410)
        controls_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 14), pady=6)
        controls = controls_panel.content

        preview = ttk.Frame(self.argb_tab)
        preview.grid(row=0, column=1, sticky="nsew", pady=6)
        preview.columnconfigure(0, weight=1)
        preview.columnconfigure(1, weight=1)
        preview.rowconfigure(0, weight=1)
        preview.rowconfigure(1, weight=1)

        channels_box = ttk.LabelFrame(controls, text="Каналы", style="Section.TLabelframe", padding=14)
        channels_box.pack(fill="x")

        for channel_name, button_text in (
            ("R", "Загрузить R"),
            ("G", "Загрузить G"),
            ("B", "Загрузить B"),
            ("A", "Загрузить Alpha"),
        ):
            row = ttk.Frame(channels_box, style="Panel.TFrame")
            row.pack(fill="x", pady=(0, 10))
            row.columnconfigure(1, weight=1)

            ttk.Label(row, text=channel_name, style="PanelLabel.TLabel", width=4).grid(row=0, column=0, sticky="w")
            button = ttk.Button(row, text=button_text, style="Ghost.TButton", command=lambda name=channel_name: self.load_channel_image(name))
            button.grid(row=0, column=1, sticky="ew", padx=(6, 8))

        argb_info = ttk.Label(
            channels_box,
            text="Размер итогового изображения берётся из канала R. G, B и alpha при необходимости подгоняются автоматически.",
            style="PanelLabel.TLabel",
            wraplength=340,
            justify="left",
        )
        argb_info.pack(anchor="w")

        self.bulk_drop_label = tk.Label(
            channels_box,
            text="Или перетащите сюда сразу 3-4 файла в порядке R -> G -> B -> A",
            bg=DROP_BG,
            fg=TEXT_MUTED,
            font=("Segoe UI", 10),
            padx=12,
            pady=10,
            bd=1,
            relief="solid",
            justify="left",
        )
        self.bulk_drop_label.pack(fill="x", pady=(10, 10))

        self.channel_info_labels = {}
        for channel_name in ("R", "G", "B", "A"):
            var = tk.StringVar(value=f"{channel_name}: не загружено")
            self.channel_info_labels[channel_name] = var
            ttk.Label(channels_box, textvariable=var, style="PanelLabel.TLabel", wraplength=340).pack(anchor="w", pady=(0, 4))

        alpha_box = ttk.LabelFrame(controls, text="Alpha", style="Section.TLabelframe", padding=14)
        alpha_box.pack(fill="x", pady=(14, 0))

        ttk.Radiobutton(alpha_box, text="Постоянное значение", value="slider", variable=self.alpha_mode_var).pack(anchor="w")
        ttk.Radiobutton(alpha_box, text="Из alpha-изображения", value="image", variable=self.alpha_mode_var).pack(anchor="w", pady=(4, 0))

        self.alpha_drop_label = tk.Label(
            alpha_box,
            text="Перетащите сюда alpha-карту",
            bg=DROP_BG,
            fg=TEXT_MUTED,
            font=("Segoe UI", 10),
            padx=12,
            pady=10,
            bd=1,
            relief="solid",
        )
        self.alpha_drop_label.pack(fill="x", pady=(10, 0))

        ttk.Label(alpha_box, text="Значение alpha", style="PanelLabel.TLabel").pack(anchor="w", pady=(12, 0))
        ttk.Scale(alpha_box, from_=0, to=255, variable=self.alpha_value_var).pack(fill="x", pady=(8, 4))
        ttk.Label(alpha_box, textvariable=self.alpha_value_text, style="PanelLabel.TLabel").pack(anchor="w")

        ttk.Label(alpha_box, text="Прозрачность результата", style="PanelLabel.TLabel").pack(anchor="w", pady=(12, 0))
        ttk.Scale(alpha_box, from_=0, to=200, variable=self.alpha_opacity_var).pack(fill="x", pady=(8, 4))
        ttk.Label(alpha_box, textvariable=self.alpha_opacity_text, style="PanelLabel.TLabel").pack(anchor="w")

        ttk.Checkbutton(alpha_box, text="Инвертировать alpha", variable=self.alpha_invert_var).pack(anchor="w", pady=(12, 0))

        actions_box = ttk.Frame(controls, style="Panel.TFrame")
        actions_box.pack(fill="x", pady=(14, 0))
        ttk.Button(actions_box, text="Собрать aRGB", command=self.generate_argb_result, style="Accent.TButton").pack(fill="x")
        ttk.Button(actions_box, text="Сохранить результат", command=self.save_argb_result, style="Ghost.TButton").pack(fill="x", pady=(10, 0))

        self.argb_cards = {
            "R": PreviewCard(preview, "Канал R", PREVIEW_SIZE_SMALL, empty_info="Перетащите сюда изображение канала R"),
            "G": PreviewCard(preview, "Канал G", PREVIEW_SIZE_SMALL, empty_info="Перетащите сюда изображение канала G"),
            "B": PreviewCard(preview, "Канал B", PREVIEW_SIZE_SMALL, empty_info="Перетащите сюда изображение канала B"),
            "RESULT": PreviewCard(preview, "Результат: aRGB", PREVIEW_SIZE_SMALL, empty_info="После сборки итог появится здесь"),
        }
        self.argb_cards["R"].grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        self.argb_cards["G"].grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))
        self.argb_cards["B"].grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(8, 0))
        self.argb_cards["RESULT"].grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(8, 0))

        for card in self.argb_cards.values():
            card.clear()

    def _build_unpack_tab(self):
        # Вкладка обратного режима: RGBA -> R, G, B, A.
        self.unpack_tab.columnconfigure(0, weight=0)
        self.unpack_tab.columnconfigure(1, weight=1)
        self.unpack_tab.rowconfigure(0, weight=1)

        controls_panel = ScrollablePanel(self.unpack_tab, width=390)
        controls_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 14), pady=6)
        controls = controls_panel.content

        preview = ttk.Frame(self.unpack_tab)
        preview.grid(row=0, column=1, sticky="nsew", pady=6)
        preview.columnconfigure(0, weight=1)
        preview.columnconfigure(1, weight=1)
        preview.rowconfigure(0, weight=1)
        preview.rowconfigure(1, weight=1)
        preview.rowconfigure(2, weight=1)

        source_box = ttk.LabelFrame(controls, text="Источник RGBA", style="Section.TLabelframe", padding=14)
        source_box.pack(fill="x")

        ttk.Label(source_box, text="Исходное изображение", style="PanelLabel.TLabel").pack(anchor="w")
        self.unpack_path_entry = ttk.Entry(source_box, state="readonly", style="Readonly.TEntry")
        self.unpack_path_entry.pack(fill="x", pady=(8, 10))
        ttk.Button(source_box, text="Открыть RGBA-изображение", command=self.load_unpack_image, style="Ghost.TButton").pack(fill="x")
        ttk.Label(
            source_box,
            text="Можно перетащить файл прямо на большую карточку предпросмотра.",
            style="PanelLabel.TLabel",
            wraplength=320,
            justify="left",
        ).pack(anchor="w", pady=(10, 0))

        save_box = ttk.LabelFrame(controls, text="Сохранение каналов", style="Section.TLabelframe", padding=14)
        save_box.pack(fill="x", pady=(14, 0))
        ttk.Label(save_box, text="Префикс файлов", style="PanelLabel.TLabel").pack(anchor="w")
        self.unpack_prefix_entry = ttk.Entry(save_box, textvariable=self.unpack_prefix_var)
        self.unpack_prefix_entry.pack(fill="x", pady=(8, 0))
        ttk.Label(
            save_box,
            text="Файлы будут сохранены как prefix + имя_исходника + _R/_G/_B/_A.png",
            style="PanelLabel.TLabel",
            wraplength=320,
            justify="left",
        ).pack(anchor="w", pady=(10, 0))

        actions_box = ttk.Frame(controls, style="Panel.TFrame")
        actions_box.pack(fill="x", pady=(14, 0))
        ttk.Button(actions_box, text="Извлечь каналы", command=self.generate_unpack_channels, style="Accent.TButton").pack(fill="x")
        ttk.Button(actions_box, text="Сохранить все каналы", command=self.save_unpack_channels, style="Ghost.TButton").pack(fill="x", pady=(10, 0))

        self.unpack_source_card = PreviewCard(
            preview,
            "Исходное RGBA-изображение",
            PREVIEW_SIZE_LARGE,
            empty_info="Перетащите RGBA-изображение сюда или откройте его кнопкой слева",
        )
        self.unpack_source_card.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 8))

        self.unpack_cards = {
            "R": PreviewCard(preview, "Канал R", PREVIEW_SIZE_SMALL, empty_info="После извлечения появится канал R"),
            "G": PreviewCard(preview, "Канал G", PREVIEW_SIZE_SMALL, empty_info="После извлечения появится канал G"),
            "B": PreviewCard(preview, "Канал B", PREVIEW_SIZE_SMALL, empty_info="После извлечения появится канал B"),
            "A": PreviewCard(preview, "Канал A", PREVIEW_SIZE_SMALL, empty_info="После извлечения появится канал A"),
        }
        self.unpack_cards["R"].grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))
        self.unpack_cards["G"].grid(row=0, column=2, sticky="nsew", padx=(8, 0), pady=(0, 8))
        self.unpack_cards["B"].grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(8, 0))
        self.unpack_cards["A"].grid(row=1, column=2, sticky="nsew", padx=(8, 0), pady=(8, 0))

        preview.columnconfigure(2, weight=1)
        self.unpack_source_card.clear()
        for card in self.unpack_cards.values():
            card.clear()

    def _build_noise_tab(self):
        # Вкладка генерации процедурной карты шума Перлина/fBM.
        self.noise_tab.columnconfigure(0, weight=0)
        self.noise_tab.columnconfigure(1, weight=1)
        self.noise_tab.rowconfigure(0, weight=1)

        controls_panel = ScrollablePanel(self.noise_tab, width=390)
        controls_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 14), pady=6)
        controls = controls_panel.content

        preview = ttk.Frame(self.noise_tab)
        preview.grid(row=0, column=1, sticky="nsew", pady=6)
        preview.columnconfigure(0, weight=1)
        preview.rowconfigure(0, weight=1)

        presets_box = ttk.LabelFrame(controls, text="Пресеты текстур", style="Section.TLabelframe", padding=14)
        presets_box.pack(fill="x")
        ttk.Label(
            presets_box,
            text="Клик по миниатюре применяет настройки и сразу обновляет предпросмотр.",
            style="PanelLabel.TLabel",
            wraplength=320,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        preset_grid = ttk.Frame(presets_box, style="Panel.TFrame")
        preset_grid.pack(anchor="w")
        self.noise_preset_images = []
        for index, preset in enumerate(NOISE_PRESETS):
            photo = ImageTk.PhotoImage(create_noise_preset_thumbnail(preset))
            self.noise_preset_images.append(photo)
            preset_button = tk.Label(
                preset_grid,
                image=photo,
                bg=DROP_BG,
                bd=1,
                relief="solid",
                cursor="hand2",
                width=48,
                height=48,
            )
            preset_button.grid(row=index // 4, column=index % 4, padx=4, pady=4)
            preset_button.bind("<Button-1>", lambda _event, item=preset: self.apply_noise_preset(item))
            add_tooltip(preset_button, f"{preset['name']}\n{preset['hint']}")

        resolution_box = ttk.LabelFrame(controls, text="Размер", style="Section.TLabelframe", padding=14)
        resolution_box.pack(fill="x", pady=(14, 0))

        size_row = ttk.Frame(resolution_box, style="Panel.TFrame")
        size_row.pack(fill="x")
        size_row.columnconfigure(1, weight=1)
        size_row.columnconfigure(3, weight=1)

        width_label = ttk.Label(size_row, text="Ширина", style="PanelLabel.TLabel")
        width_label.grid(row=0, column=0, sticky="w")
        width_entry = ttk.Entry(size_row, textvariable=self.noise_width_var)
        width_entry.grid(row=0, column=1, sticky="ew", padx=(8, 12))
        height_label = ttk.Label(size_row, text="Высота", style="PanelLabel.TLabel")
        height_label.grid(row=0, column=2, sticky="w")
        height_entry = ttk.Entry(size_row, textvariable=self.noise_height_var)
        height_entry.grid(row=0, column=3, sticky="ew", padx=(8, 0))
        add_tooltip(width_label, "Ширина итоговой карты шума в пикселях.")
        add_tooltip(width_entry, "Введите целое число от 16 до 4096. Изменение применится автоматически.")
        add_tooltip(height_label, "Высота итоговой карты шума в пикселях.")
        add_tooltip(height_entry, "Введите целое число от 16 до 4096. Изменение применится автоматически.")

        ttk.Label(
            resolution_box,
            text="Допустимый размер: от 16 до 4096 px. Для быстрого предпросмотра удобно 512x512.",
            style="PanelLabel.TLabel",
            wraplength=320,
            justify="left",
        ).pack(anchor="w", pady=(10, 0))

        noise_box = ttk.LabelFrame(controls, text="Шум Перлина", style="Section.TLabelframe", padding=14)
        noise_box.pack(fill="x", pady=(14, 0))

        scale_label = ttk.Label(noise_box, text="Масштаб шума", style="PanelLabel.TLabel")
        scale_label.pack(anchor="w")
        scale_widget = ttk.Scale(noise_box, from_=8.0, to=512.0, variable=self.noise_scale_var)
        scale_widget.pack(fill="x", pady=(8, 4))
        scale_value = ttk.Label(noise_box, textvariable=self.noise_scale_text, style="PanelLabel.TLabel")
        scale_value.pack(anchor="w")
        add_tooltip(scale_label, "Размер крупных пятен шума. Больше значение - крупнее и мягче узор.")
        add_tooltip(scale_widget, "Двигайте ползунок: предпросмотр обновится автоматически.")

        octaves_label = ttk.Label(noise_box, text="Слои детализации", style="PanelLabel.TLabel")
        octaves_label.pack(anchor="w", pady=(12, 0))
        octaves_widget = ttk.Scale(noise_box, from_=1.0, to=10.0, variable=self.noise_octaves_var)
        octaves_widget.pack(fill="x", pady=(8, 4))
        octaves_value = ttk.Label(noise_box, textvariable=self.noise_octaves_text, style="PanelLabel.TLabel")
        octaves_value.pack(anchor="w")
        add_tooltip(octaves_label, "Количество наложенных слоёв шума. Больше слоёв - больше мелких деталей.")
        add_tooltip(octaves_widget, "Для большинства текстур хватает 4-8 слоёв.")

        persistence_label = ttk.Label(noise_box, text="Сила мелких слоёв", style="PanelLabel.TLabel")
        persistence_label.pack(anchor="w", pady=(12, 0))
        persistence_widget = ttk.Scale(noise_box, from_=0.05, to=0.95, variable=self.noise_persistence_var)
        persistence_widget.pack(fill="x", pady=(8, 4))
        persistence_value = ttk.Label(noise_box, textvariable=self.noise_persistence_text, style="PanelLabel.TLabel")
        persistence_value.pack(anchor="w")
        add_tooltip(persistence_label, "Насколько заметны мелкие слои. Низко - гладко, высоко - грубо и зернисто.")
        add_tooltip(persistence_widget, "Управляет вкладом мелких деталей в многослойном шуме.")

        lacunarity_label = ttk.Label(noise_box, text="Рост частоты слоёв", style="PanelLabel.TLabel")
        lacunarity_label.pack(anchor="w", pady=(12, 0))
        lacunarity_widget = ttk.Scale(noise_box, from_=1.1, to=4.0, variable=self.noise_lacunarity_var)
        lacunarity_widget.pack(fill="x", pady=(8, 4))
        lacunarity_value = ttk.Label(noise_box, textvariable=self.noise_lacunarity_text, style="PanelLabel.TLabel")
        lacunarity_value.pack(anchor="w")
        add_tooltip(lacunarity_label, "Насколько быстро каждый следующий слой становится мельче.")
        add_tooltip(lacunarity_widget, "2.0 - классическое значение, выше - более резкая детализация.")

        rotation_label = ttk.Label(noise_box, text="Поворот узора", style="PanelLabel.TLabel")
        rotation_label.pack(anchor="w", pady=(12, 0))
        rotation_widget = ttk.Scale(noise_box, from_=0.0, to=360.0, variable=self.noise_rotation_var)
        rotation_widget.pack(fill="x", pady=(8, 4))
        rotation_value = ttk.Label(noise_box, textvariable=self.noise_rotation_text, style="PanelLabel.TLabel")
        rotation_value.pack(anchor="w")
        add_tooltip(rotation_label, "Поворачивает координаты шума перед генерацией. Полезно для направления волокон, волн и прожилок.")
        add_tooltip(rotation_widget, "0-360 градусов. Автопредпросмотр обновляется в уменьшенном размере для быстрого отклика.")

        ttk.Label(
            noise_box,
            text="Многослойный Перлин складывает несколько слоёв: масштаб задаёт крупность пятен, слои добавляют микродеталь.",
            style="PanelLabel.TLabel",
            wraplength=320,
            justify="left",
        ).pack(anchor="w", pady=(12, 0))

        if NOISE_FEATURE_LEVEL >= 2:
            contrast_box = ttk.LabelFrame(controls, text="Контрастность", style="Section.TLabelframe", padding=14)
            contrast_box.pack(fill="x", pady=(14, 0))
            contrast_label = ttk.Label(contrast_box, text="Контраст шума", style="PanelLabel.TLabel")
            contrast_label.pack(anchor="w")
            contrast_widget = ttk.Scale(contrast_box, from_=0.1, to=5.0, variable=self.noise_contrast_var)
            contrast_widget.pack(fill="x", pady=(8, 4))
            contrast_value = ttk.Label(contrast_box, textvariable=self.noise_contrast_text, style="PanelLabel.TLabel")
            contrast_value.pack(anchor="w")
            add_tooltip(contrast_label, "Усиливает или смягчает переходы после генерации шума.")
            add_tooltip(contrast_widget, "0.1 - очень мягко, 1.0 - стандартно, 5.0 - жёсткая маска.")

        if NOISE_FEATURE_LEVEL >= 3:
            seed_box = ttk.LabelFrame(controls, text="Зерно генерации", style="Section.TLabelframe", padding=14)
            seed_box.pack(fill="x", pady=(14, 0))
            seed_label = ttk.Label(seed_box, text="Зерно", style="PanelLabel.TLabel")
            seed_label.pack(anchor="w")
            seed_entry = ttk.Entry(seed_box, textvariable=self.noise_seed_var)
            seed_entry.pack(fill="x", pady=(8, 10))
            random_button = ttk.Button(seed_box, text="Случайно", command=self.randomize_noise_seed, style="Ghost.TButton")
            random_button.pack(fill="x")
            add_tooltip(seed_label, "Зерно генерации: одинаковое значение повторяет тот же рисунок.")
            add_tooltip(seed_entry, "Можно ввести число или текст. Изменение применится автоматически.")
            add_tooltip(random_button, "Подставляет новое случайное зерно и сразу пересчитывает шум.")
            ttk.Label(
                seed_box,
                text="Одинаковое зерно даёт одинаковую карту. Можно вводить число или текст.",
                style="PanelLabel.TLabel",
                wraplength=320,
                justify="left",
            ).pack(anchor="w", pady=(10, 0))

        color_box = ttk.LabelFrame(controls, text="Цвет RGB", style="Section.TLabelframe", padding=14)
        color_box.pack(fill="x", pady=(14, 0))
        ttk.Label(
            color_box,
            text="Шум окрашивается градиентом от тёмного RGB к светлому RGB. Все значения: 0-255.",
            style="PanelLabel.TLabel",
            wraplength=320,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        for row_index, (title, target, vars_group, swatch_attr, hint) in enumerate((
            ("Тёмный цвет", "low", (self.noise_low_r_var, self.noise_low_g_var, self.noise_low_b_var), "noise_low_swatch", "Цвет самых тёмных участков шума."),
            ("Светлый цвет", "high", (self.noise_high_r_var, self.noise_high_g_var, self.noise_high_b_var), "noise_high_swatch", "Цвет самых светлых участков шума."),
        )):
            row = ttk.Frame(color_box, style="Panel.TFrame")
            row.pack(fill="x", pady=(0 if row_index == 0 else 8, 0))
            row.columnconfigure(2, weight=1)
            row.columnconfigure(4, weight=1)
            row.columnconfigure(6, weight=1)

            title_label = ttk.Label(row, text=title, style="PanelLabel.TLabel", width=13)
            title_label.grid(row=0, column=0, sticky="w")
            add_tooltip(title_label, hint)

            for start_column, channel_name, variable in ((1, "R", vars_group[0]), (3, "G", vars_group[1]), (5, "B", vars_group[2])):
                channel_label = ttk.Label(row, text=channel_name, style="PanelLabel.TLabel")
                channel_label.grid(row=0, column=start_column, sticky="e", padx=(6, 4))
                entry = ttk.Entry(row, textvariable=variable, width=5)
                entry.grid(row=0, column=start_column + 1, sticky="ew")
                add_tooltip(entry, f"Канал {channel_name}: целое число от 0 до 255. Предпросмотр обновится автоматически.")

            swatch = tk.Label(row, width=3, height=1, bg="#000000", bd=1, relief="solid", cursor="hand2")
            swatch.grid(row=0, column=7, padx=(10, 0), sticky="e")
            swatch.bind("<Button-1>", lambda _event, color_target=target: self.open_noise_color_picker(color_target))
            add_tooltip(swatch, "Кликните, чтобы выбрать цвет на RGB-круге.")
            setattr(self, swatch_attr, swatch)

            picker_button = ttk.Button(row, text="Круг RGB", command=lambda color_target=target: self.open_noise_color_picker(color_target), style="Ghost.TButton")
            picker_button.grid(row=0, column=8, padx=(8, 0), sticky="e")
            add_tooltip(picker_button, "Открывает палитру: цвет выбирается мышкой по RGB-кругу, как пипеткой.")

        actions_box = ttk.Frame(controls, style="Panel.TFrame")
        actions_box.pack(fill="x", pady=(14, 0))
        generate_button = ttk.Button(actions_box, text="Сгенерировать полный размер", command=lambda: self.generate_noise_result(preview_only=False), style="Accent.TButton")
        generate_button.pack(fill="x")
        save_button = ttk.Button(actions_box, text="Сохранить шум", command=self.save_noise_result, style="Ghost.TButton")
        save_button.pack(fill="x", pady=(10, 0))
        add_tooltip(generate_button, "Строит результат в полном заданном размере. Автоматические изменения считаются быстрее в режиме предпросмотра.")
        add_tooltip(save_button, "Сохраняет текущий результат в PNG/TGA/BMP.")

        self.noise_result_card = PreviewCard(
            preview,
            "Результат: шум Перлина",
            PREVIEW_SIZE_LARGE,
            empty_info="Меняйте параметры: предпросмотр обновляется автоматически",
        )
        self.noise_result_card.grid(row=0, column=0, sticky="nsew")
        self.noise_result_card.clear()
        self.after(150, lambda: self.generate_noise_result(show_errors=False, preview_only=True))

    def _bind_preview_viewers(self):
        preview_cards = [
            self.height_source_card,
            self.height_result_card,
            self.argb_cards["R"],
            self.argb_cards["G"],
            self.argb_cards["B"],
            self.argb_cards["RESULT"],
            self.unpack_source_card,
            self.unpack_cards["R"],
            self.unpack_cards["G"],
            self.unpack_cards["B"],
            self.unpack_cards["A"],
            self.noise_result_card,
        ]

        for card in preview_cards:
            card.bind_open(self.open_image_viewer)

    def _connect_traces(self):
        self.height_strength_var.trace_add("write", self._refresh_value_labels)
        self.alpha_value_var.trace_add("write", self._refresh_value_labels)
        self.alpha_opacity_var.trace_add("write", self._refresh_value_labels)
        self.noise_width_var.trace_add("write", self._on_noise_parameter_changed)
        self.noise_height_var.trace_add("write", self._on_noise_parameter_changed)
        self.noise_scale_var.trace_add("write", self._on_noise_parameter_changed)
        self.noise_octaves_var.trace_add("write", self._on_noise_parameter_changed)
        self.noise_persistence_var.trace_add("write", self._on_noise_parameter_changed)
        self.noise_lacunarity_var.trace_add("write", self._on_noise_parameter_changed)
        self.noise_contrast_var.trace_add("write", self._on_noise_parameter_changed)
        self.noise_rotation_var.trace_add("write", self._on_noise_parameter_changed)
        self.noise_seed_var.trace_add("write", self._on_noise_parameter_changed)
        self.noise_low_r_var.trace_add("write", self._on_noise_parameter_changed)
        self.noise_low_g_var.trace_add("write", self._on_noise_parameter_changed)
        self.noise_low_b_var.trace_add("write", self._on_noise_parameter_changed)
        self.noise_high_r_var.trace_add("write", self._on_noise_parameter_changed)
        self.noise_high_g_var.trace_add("write", self._on_noise_parameter_changed)
        self.noise_high_b_var.trace_add("write", self._on_noise_parameter_changed)
        self._refresh_value_labels()

    def _refresh_value_labels(self, *_):
        self.height_strength_text.set(f"{self.height_strength_var.get():.1f}")
        self.alpha_value_text.set(str(int(self.alpha_value_var.get())))
        self.alpha_opacity_text.set(f"{int(self.alpha_opacity_var.get())}%")
        self.noise_scale_text.set(f"{self.noise_scale_var.get():.1f}")
        self.noise_octaves_text.set(str(int(round(self.noise_octaves_var.get()))))
        self.noise_persistence_text.set(f"{self.noise_persistence_var.get():.2f}")
        self.noise_lacunarity_text.set(f"{self.noise_lacunarity_var.get():.2f}")
        self.noise_contrast_text.set(f"{self.noise_contrast_var.get():.2f}")
        self.noise_rotation_text.set(f"{int(round(self.noise_rotation_var.get()))}°")
        self._update_noise_color_swatches()

    def _read_rgb_value(self, variable, label):
        try:
            value = int(variable.get())
        except (ValueError, tk.TclError):
            raise ValueError(f"{label}: укажите целое число от 0 до 255.")

        if value < 0 or value > 255:
            raise ValueError(f"{label}: значение должно быть от 0 до 255.")
        return value

    def _read_rgb_color(self, variables, label):
        return (
            self._read_rgb_value(variables[0], f"{label} R"),
            self._read_rgb_value(variables[1], f"{label} G"),
            self._read_rgb_value(variables[2], f"{label} B"),
        )

    def _read_noise_colors(self):
        low_color = self._read_rgb_color((self.noise_low_r_var, self.noise_low_g_var, self.noise_low_b_var), "Тёмный цвет")
        high_color = self._read_rgb_color((self.noise_high_r_var, self.noise_high_g_var, self.noise_high_b_var), "Светлый цвет")
        return low_color, high_color

    def _update_noise_color_swatches(self):
        if self.noise_low_swatch is None or self.noise_high_swatch is None:
            return

        try:
            low_color, high_color = self._read_noise_colors()
        except ValueError:
            return

        self.noise_low_swatch.configure(bg=rgb_to_hex(low_color))
        self.noise_high_swatch.configure(bg=rgb_to_hex(high_color))

    def set_noise_color(self, target, color):
        variables = (
            (self.noise_low_r_var, self.noise_low_g_var, self.noise_low_b_var)
            if target == "low"
            else (self.noise_high_r_var, self.noise_high_g_var, self.noise_high_b_var)
        )
        for variable, channel in zip(variables, color):
            variable.set(str(clamp_rgb_value(channel)))

    def open_noise_color_picker(self, target):
        variables = (
            (self.noise_low_r_var, self.noise_low_g_var, self.noise_low_b_var)
            if target == "low"
            else (self.noise_high_r_var, self.noise_high_g_var, self.noise_high_b_var)
        )
        fallback = (0, 0, 0) if target == "low" else (255, 255, 255)
        try:
            initial_color = self._read_rgb_color(variables, "Цвет")
        except ValueError:
            initial_color = fallback

        title_text = "Тёмный цвет RGB" if target == "low" else "Светлый цвет RGB"
        ColorWheelPicker(self, initial_color, lambda color: self.set_noise_color(target, color), title_text)

    def _on_noise_parameter_changed(self, *_):
        self._refresh_value_labels()
        self._schedule_noise_refresh()

    def _schedule_noise_refresh(self, delay=350):
        if not hasattr(self, "noise_result_card"):
            return

        if self.noise_refresh_after_id is not None:
            self.after_cancel(self.noise_refresh_after_id)

        self.noise_refresh_after_id = self.after(delay, self._run_scheduled_noise_refresh)

    def _run_scheduled_noise_refresh(self):
        self.noise_refresh_after_id = None
        self.generate_noise_result(show_errors=False, preview_only=True)

    def _set_readonly_entry_text(self, entry, text):
        entry.configure(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, text)
        entry.configure(state="readonly")

    def _setup_drop_targets(self):
        if not DRAG_AND_DROP_ENABLED:
            return

        # Привязываем drag-and-drop к карточкам и зонам загрузки.
        self._register_drop_target(self.height_source_card, self._handle_height_drop)
        self._register_drop_target(self.argb_cards["R"], lambda event: self._handle_channel_drop(event, "R"))
        self._register_drop_target(self.argb_cards["G"], lambda event: self._handle_channel_drop(event, "G"))
        self._register_drop_target(self.argb_cards["B"], lambda event: self._handle_channel_drop(event, "B"))
        self._register_drop_target(self.bulk_drop_label, self._handle_bulk_channel_drop)
        self._register_drop_target(self.alpha_drop_label, lambda event: self._handle_channel_drop(event, "A"))
        self._register_drop_target(self.unpack_source_card, self._handle_unpack_drop)

    def _register_drop_target(self, widget, callback):
        widgets = widget.drop_widgets() if hasattr(widget, "drop_widgets") else [widget]

        for drop_widget in widgets:
            drop_widget.drop_target_register(DND_FILES)
            drop_widget.dnd_bind("<<Drop>>", callback)

    def _extract_drop_files(self, raw_data):
        try:
            parts = self.tk.splitlist(raw_data)
        except tk.TclError:
            parts = [raw_data]

        return [str(Path(part)) for part in parts if Path(part).is_file()]

    def _handle_height_drop(self, event):
        file_paths = self._extract_drop_files(event.data)
        if not file_paths:
            self.status_var.set("Не удалось прочитать файл из drag-and-drop")
            return

        self.load_height_image_from_path(file_paths[0])

    def _handle_channel_drop(self, event, channel_name):
        file_paths = self._extract_drop_files(event.data)
        if not file_paths:
            self.status_var.set("Не удалось прочитать файл из drag-and-drop")
            return

        self.load_channel_image_from_path(channel_name, file_paths[0])

    def _handle_bulk_channel_drop(self, event):
        file_paths = self._extract_drop_files(event.data)
        if not file_paths:
            self.status_var.set("Не удалось прочитать файлы из drag-and-drop")
            return

        loaded_channels = []
        for channel_name, file_path in zip(("R", "G", "B", "A"), file_paths):
            if self.load_channel_image_from_path(channel_name, file_path, update_status=False):
                loaded_channels.append(channel_name)

        if loaded_channels:
            self.status_var.set(f"Загружены каналы через drag-and-drop: {', '.join(loaded_channels)}")

    def _handle_unpack_drop(self, event):
        file_paths = self._extract_drop_files(event.data)
        if not file_paths:
            self.status_var.set("Не удалось прочитать файл из drag-and-drop")
            return

        self.load_unpack_image_from_path(file_paths[0])

    def open_image_viewer(self, image, title_text, checker=False):
        ImageViewer(self, image, title_text, checker=checker)

    def load_height_image(self):
        file_path = filedialog.askopenfilename(title="Открыть карту высот", filetypes=IMAGE_TYPES)
        if file_path:
            self.load_height_image_from_path(file_path)

    def load_height_image_from_path(self, file_path):
        # Загрузка исходной карты высот.
        try:
            with Image.open(file_path) as image:
                self.height_source = image.copy()
        except OSError as error:
            messagebox.showerror("Ошибка загрузки", f"Не удалось открыть изображение.\n\n{error}")
            return False

        self.height_path = file_path
        self.height_result = None
        self._set_readonly_entry_text(self.height_path_entry, file_path)
        self.height_source_card.show_image(grayscale_to_8bit(self.height_source), image_info_text(file_path, self.height_source))
        self.height_result_card.clear()
        self.status_var.set(f"Загружена карта высот: {Path(file_path).name}")
        return True

    def generate_height_result(self):
        # Генерация карты нормалей на основе настроек пользователя.
        if self.height_source is None:
            messagebox.showwarning("Нет изображения", "Сначала загрузите карту высот.")
            return

        self.height_result = create_normal_map(
            self.height_source,
            strength=float(self.height_strength_var.get()),
            convention=self.height_convention_var.get(),
            invert_height=self.height_invert_var.get(),
            preserve_alpha=self.height_alpha_var.get(),
        )
        self.height_result_card.show_image(
            self.height_result,
            f"{self.height_convention_var.get()} | {self.height_result.width}x{self.height_result.height} | {self.height_result.mode}",
            checker=self.height_result.mode == "RGBA",
        )
        self.status_var.set("Normal map сгенерирована")

    def save_height_result(self):
        if self.height_result is None:
            messagebox.showwarning("Нет результата", "Сначала сгенерируйте normal map.")
            return

        initial_name = "normal_map.png"
        if self.height_path:
            initial_name = f"{Path(self.height_path).stem}_normal.png"

        file_path = filedialog.asksaveasfilename(
            title="Сохранить normal map",
            defaultextension=".png",
            filetypes=SAVE_TYPES,
            initialfile=initial_name,
        )
        if not file_path:
            return

        try:
            self.height_result.save(file_path)
        except OSError as error:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить файл.\n\n{error}")
            return

        self.status_var.set(f"Сохранено: {Path(file_path).name}")

    def load_unpack_image(self):
        file_path = filedialog.askopenfilename(title="Открыть RGBA-изображение", filetypes=IMAGE_TYPES)
        if file_path:
            self.load_unpack_image_from_path(file_path)

    def load_unpack_image_from_path(self, file_path):
        # Загрузка исходного RGBA изображения для распаковки каналов.
        try:
            with Image.open(file_path) as image:
                self.unpack_source = image.copy()
        except OSError as error:
            messagebox.showerror("Ошибка загрузки", f"Не удалось открыть изображение.\n\n{error}")
            return False

        self.unpack_path = file_path
        self.unpack_channels = {"R": None, "G": None, "B": None, "A": None}
        self._set_readonly_entry_text(self.unpack_path_entry, file_path)
        self.unpack_source_card.show_image(self.unpack_source, image_info_text(file_path, self.unpack_source), checker="A" in self.unpack_source.getbands())
        for card in self.unpack_cards.values():
            card.clear()
        self.status_var.set(f"Загружено RGBA-изображение: {Path(file_path).name}")
        return True

    def generate_unpack_channels(self):
        # Извлекаем каналы и показываем их как отдельные Ч/Б изображения.
        if self.unpack_source is None:
            messagebox.showwarning("Нет изображения", "Сначала загрузите RGBA-изображение.")
            return False

        self.unpack_channels = split_rgba_image(self.unpack_source)
        for channel_name, image in self.unpack_channels.items():
            self.unpack_cards[channel_name].show_image(
                image,
                f"{channel_name} | {image.width}x{image.height} | L",
            )

        self.status_var.set("Каналы RGBA извлечены")
        return True

    def save_unpack_channels(self):
        if self.unpack_source is None:
            messagebox.showwarning("Нет изображения", "Сначала загрузите RGBA-изображение.")
            return

        if any(image is None for image in self.unpack_channels.values()):
            if not self.generate_unpack_channels():
                return

        folder_path = filedialog.askdirectory(title="Выберите папку для сохранения каналов")
        if not folder_path:
            return

        try:
            self.save_unpack_channels_to_folder(folder_path)
        except OSError as error:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить каналы.\n\n{error}")
            return

        self.status_var.set(f"Каналы сохранены в папку: {Path(folder_path).name}")

    def save_unpack_channels_to_folder(self, folder_path):
        # Сохраняем все каналы сразу в выбранную пользователем папку.
        if any(image is None for image in self.unpack_channels.values()):
            raise OSError("Каналы ещё не извлечены")

        source_stem = Path(self.unpack_path).stem if self.unpack_path else "image"
        prefix = self.unpack_prefix_var.get().strip()

        for channel_name, image in self.unpack_channels.items():
            target_path = Path(folder_path) / f"{prefix}{source_stem}_{channel_name}.png"
            image.save(target_path)

    def load_channel_image(self, channel_name):
        title_map = {
            "R": "Открыть канал R",
            "G": "Открыть канал G",
            "B": "Открыть канал B",
            "A": "Открыть alpha-изображение",
        }
        file_path = filedialog.askopenfilename(title=title_map[channel_name], filetypes=IMAGE_TYPES)
        if file_path:
            self.load_channel_image_from_path(channel_name, file_path)

    def load_channel_image_from_path(self, channel_name, file_path, update_status=True):
        # Загрузка одного канала для сборки итогового aRGB.
        try:
            with Image.open(file_path) as opened_image:
                image = opened_image.copy()
        except OSError as error:
            messagebox.showerror("Ошибка загрузки", f"Не удалось открыть изображение.\n\n{error}")
            return False

        self.channel_images[channel_name] = image
        self.channel_paths[channel_name] = file_path
        self.channel_info_labels[channel_name].set(image_info_text(file_path, image))

        if channel_name in self.argb_cards:
            self.argb_cards[channel_name].show_image(grayscale_to_8bit(image), image_info_text(file_path, image))
        elif channel_name == "A":
            self.alpha_drop_label.configure(text=f"Alpha: {Path(file_path).name} | {image.width}x{image.height} | {image.mode}")

        self.argb_result = None
        self.argb_cards["RESULT"].clear()

        if update_status:
            self.status_var.set(f"Загружен канал {channel_name}: {Path(file_path).name}")

        return True

    def generate_argb_result(self):
        # Сборка итогового изображения из каналов R, G, B и alpha.
        if self.channel_images["R"] is None or self.channel_images["G"] is None or self.channel_images["B"] is None:
            messagebox.showwarning("Не хватает каналов", "Загрузите минимум R, G и B изображения.")
            return

        try:
            self.argb_result = build_argb_image(
                self.channel_images["R"],
                self.channel_images["G"],
                self.channel_images["B"],
                alpha_mode=self.alpha_mode_var.get(),
                alpha_value=int(self.alpha_value_var.get()),
                alpha_image=self.channel_images["A"],
                alpha_opacity=int(self.alpha_opacity_var.get()),
                invert_alpha=self.alpha_invert_var.get(),
            )
        except ValueError as error:
            messagebox.showwarning("Проверьте alpha", str(error))
            return

        self.argb_cards["RESULT"].show_image(
            self.argb_result,
            f"aRGB / RGBA | {self.argb_result.width}x{self.argb_result.height}",
            checker=True,
        )
        self.status_var.set("aRGB-изображение собрано")

    def save_argb_result(self):
        if self.argb_result is None:
            messagebox.showwarning("Нет результата", "Сначала соберите RGBA-изображение.")
            return

        initial_name = "packed_argb.png"
        if self.channel_paths["R"]:
            initial_name = f"{Path(self.channel_paths['R']).stem}_argb.png"

        file_path = filedialog.asksaveasfilename(
            title="Сохранить aRGB-изображение",
            defaultextension=".png",
            filetypes=SAVE_TYPES,
            initialfile=initial_name,
        )
        if not file_path:
            return

        try:
            self.argb_result.save(file_path)
        except OSError as error:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить файл.\n\n{error}")
            return

        self.status_var.set(f"Сохранено: {Path(file_path).name}")

    def _read_noise_size(self):
        try:
            width = int(self.noise_width_var.get())
            height = int(self.noise_height_var.get())
        except (ValueError, tk.TclError):
            raise ValueError("Ширина и высота должны быть целыми числами.")

        if width < 16 or height < 16:
            raise ValueError("Минимальный размер шума: 16x16 px.")
        if width > 4096 or height > 4096:
            raise ValueError("Максимальный размер шума: 4096x4096 px.")
        return width, height

    def _read_noise_seed(self):
        if NOISE_FEATURE_LEVEL >= 3:
            seed_text = self.noise_seed_var.get().strip()
            if not seed_text:
                self.randomize_noise_seed()
                seed_text = self.noise_seed_var.get().strip()
            return seed_from_text(seed_text)

        return seed_from_text(self.noise_seed_var.get())

    def apply_noise_preset(self, preset):
        low_color = hex_to_rgb(preset["low"])
        high_color = hex_to_rgb(preset["high"])
        self.noise_scale_var.set(float(preset["scale"]))
        self.noise_octaves_var.set(float(preset["octaves"]))
        self.noise_persistence_var.set(float(preset["persistence"]))
        self.noise_lacunarity_var.set(float(preset["lacunarity"]))
        self.noise_contrast_var.set(float(preset["contrast"]))
        self.noise_rotation_var.set(float(preset.get("rotation", 0.0)))
        self.noise_seed_var.set(str(preset["seed"]))
        self.noise_low_r_var.set(str(low_color[0]))
        self.noise_low_g_var.set(str(low_color[1]))
        self.noise_low_b_var.set(str(low_color[2]))
        self.noise_high_r_var.set(str(high_color[0]))
        self.noise_high_g_var.set(str(high_color[1]))
        self.noise_high_b_var.set(str(high_color[2]))
        self.status_var.set(f"Пресет применён: {preset['name']}")
        self._schedule_noise_refresh(delay=60)

    def randomize_noise_seed(self):
        self.noise_seed_var.set(str(random_seed_value()))

    def _noise_render_size(self, width, height, scale, preview_only):
        if not preview_only:
            return width, height, scale, False

        longest_side = max(width, height)
        if longest_side <= NOISE_PREVIEW_MAX_SIZE:
            return width, height, scale, False

        ratio = NOISE_PREVIEW_MAX_SIZE / longest_side
        render_width = max(16, int(width * ratio))
        render_height = max(16, int(height * ratio))
        return render_width, render_height, max(1.0, scale * ratio), True

    def generate_noise_result(self, show_errors=True, preview_only=False):
        try:
            width, height = self._read_noise_size()
            scale = float(self.noise_scale_var.get())
            octaves = int(round(self.noise_octaves_var.get()))
            persistence = float(self.noise_persistence_var.get())
            lacunarity = float(self.noise_lacunarity_var.get())
            contrast = float(self.noise_contrast_var.get()) if NOISE_FEATURE_LEVEL >= 2 else 1.0
            rotation = float(self.noise_rotation_var.get())
            seed = self._read_noise_seed()
            low_color, high_color = self._read_noise_colors()
        except ValueError as error:
            if show_errors:
                messagebox.showwarning("Параметры шума", str(error))
            else:
                self.status_var.set(f"Проверьте параметры шума: {error}")
            return False

        render_width, render_height, render_scale, is_preview = self._noise_render_size(width, height, scale, preview_only)
        status_text = "Быстрый предпросмотр шума Перлина..." if is_preview else "Генерация шума Перлина..."
        self.status_var.set(status_text)
        self.update_idletasks()
        grayscale_noise = generate_perlin_noise_image(
            render_width,
            render_height,
            scale=render_scale,
            octaves=octaves,
            persistence=persistence,
            lacunarity=lacunarity,
            contrast=contrast,
            seed=seed,
            rotation=rotation,
        )
        self.noise_result = colorize_noise(grayscale_noise, low_color, high_color)
        self.noise_result_is_preview = is_preview
        self.noise_result_full_size = (width, height)
        info_text = f"Шум Перлина RGB | {width}x{height} | масштаб {scale:.1f} | поворот {int(round(rotation))}° | слои {octaves} | зерно {seed}"
        if is_preview:
            info_text += f" | быстрый предпросмотр {render_width}x{render_height}"
        self.noise_result_card.show_image(
            self.noise_result,
            info_text,
        )
        self.status_var.set("Быстрый предпросмотр обновлён" if is_preview else "Шум Перлина сгенерирован")
        return True

    def save_noise_result(self):
        if self.noise_result is None:
            messagebox.showwarning("Нет результата", "Сначала сгенерируйте шум Перлина.")
            return

        if self.noise_result_is_preview:
            if not self.generate_noise_result(show_errors=True, preview_only=False):
                return

        file_path = filedialog.asksaveasfilename(
            title="Сохранить шум Перлина",
            defaultextension=".png",
            filetypes=SAVE_TYPES,
            initialfile="perlin_noise.png",
        )
        if not file_path:
            return

        try:
            self.noise_result.save(file_path)
        except OSError as error:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить файл.\n\n{error}")
            return

        self.status_var.set(f"Сохранено: {Path(file_path).name}")


def main():
    app = GirconTool()
    app.mainloop()


if __name__ == "__main__":
    main()
