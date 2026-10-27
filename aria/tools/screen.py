"""
Screen capture tool for ARIA.
Supports:
- Wayland native capture via `grim` (fastest, lossless)
- Fallback via Pillow ImageGrab / pyscreenshot / scrot for X11
Returns PIL Image and base64 encoded strings for AI Vision models.
"""

import base64
import io
import os
import shutil
import subprocess
import tempfile
from typing import Optional, Tuple
from PIL import Image
from aria.utils.logger import logger
from aria.config import config


def capture_screen(region: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
    """
    Capture the entire screen or a specific bounding box (x, y, width, height).
    Returns a PIL Image object.
    """
    is_wayland = config.display_server == "wayland"

    # Try grim on Wayland
    if is_wayland and shutil.which("grim"):
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name

            cmd = ["grim"]
            if region:
                # grim geometry format: "x,y widthxheight"
                x, y, w, h = region
                cmd.extend(["-g", f"{x},{y} {w}x{h}"])
            cmd.append(tmp_path)

            res = subprocess.run(cmd, capture_output=True, timeout=5)
            if res.returncode == 0 and os.path.exists(tmp_path):
                img = Image.open(tmp_path).convert("RGB")
                return img
        except Exception as e:
            logger.debug(f"grim capture failed ({e}), trying fallback methods")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    # Try gnome-screenshot (standard on GNOME / Ubuntu Wayland)
    if shutil.which("gnome-screenshot"):
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
            cmd = ["gnome-screenshot", "-f", tmp_path]
            res = subprocess.run(cmd, capture_output=True, timeout=5)
            if res.returncode == 0 and os.path.exists(tmp_path):
                img = Image.open(tmp_path).convert("RGB")
                if region:
                    x, y, w, h = region
                    img = img.crop((x, y, x + w, y + h))
                return img
        except Exception as e:
            logger.debug(f"gnome-screenshot failed ({e})")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    # Fallback to Pillow ImageGrab
    try:
        from PIL import ImageGrab
        bbox = None
        if region:
            x, y, w, h = region
            bbox = (x, y, x + w, y + h)
        img = ImageGrab.grab(bbox=bbox)
        if img:
            return img.convert("RGB")
    except Exception as e:
        logger.debug(f"ImageGrab failed: {e}")

    # Fallback to scrot or import
    for tool, cmd_args in [("scrot", ["scrot", "-z", "-"]), ("import", ["import", "-window", "root", "png:-"])]:
        if shutil.which(tool):
            try:
                proc = subprocess.run(cmd_args, capture_output=True, timeout=5)
                if proc.returncode == 0 and proc.stdout:
                    return Image.open(io.BytesIO(proc.stdout)).convert("RGB")
            except Exception:
                continue

    # Return dummy placeholder if screen capture is unavailable in headless environment
    logger.warning("No screen capture mechanism succeeded. Generating empty frame.")
    return Image.new("RGB", (1920, 1080), color=(30, 30, 30))


def encode_image_base64(image: Image.Image, max_dim: int = 1280, quality: int = 85) -> str:
    """
    Resize image to prevent exceeding LLM context limits and return base64 string.
    """
    img = image.copy()
    # Downscale if larger than max_dim to save bandwidth & token cost
    w, h = img.size
    if max(w, h) > max_dim:
        scale = max_dim / float(max(w, h))
        new_w, new_h = int(w * scale), int(h * scale)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def get_screen_data_url(image: Image.Image) -> str:
    """Return data:image/jpeg;base64,... string."""
    b64 = encode_image_base64(image)
    return f"data:image/jpeg;base64,{b64}"
