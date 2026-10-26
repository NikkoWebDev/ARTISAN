#!/usr/bin/env python3
"""Image optimization utility for Artisan product catalog.

Converts large source images (JPEG/PNG) to optimized WebP format
(quality ~82, max-width 1200px) and generates web-ready thumbnails (max-width 400px).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

from PIL import Image, ImageOps

DEFAULT_MAX_WIDTH = 1200
DEFAULT_THUMB_WIDTH = 400
DEFAULT_QUALITY = 82
MIN_VALID_FILE_SIZE = 50  # Ignore dummy placeholder files (< 50 bytes)


def optimize_image(
    input_path: Path | str,
    output_dir: Optional[Path | str] = None,
    max_width: int = DEFAULT_MAX_WIDTH,
    thumb_width: int = DEFAULT_THUMB_WIDTH,
    quality: int = DEFAULT_QUALITY,
) -> Optional[Tuple[str, str]]:
    """Optimize a single image into full WebP and thumbnail WebP.

    Returns a tuple of (full_webp_path, thumb_webp_path) or None if skipped/invalid.
    """
    src = Path(input_path).resolve()
    if not src.is_file():
        return None

    if src.stat().st_size < MIN_VALID_FILE_SIZE:
        return None

    out_directory = Path(output_dir).resolve() if output_dir else src.parent
    out_directory.mkdir(parents=True, exist_ok=True)

    dest_stem = src.stem
    dest_full = out_directory / f"{dest_stem}.webp"
    dest_thumb = out_directory / f"{dest_stem}_thumb.webp"

    try:
        with Image.open(src) as raw_img:
            img = ImageOps.exif_transpose(raw_img)

            # Preserve transparency if RGBA or paletted with alpha; else RGB
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                img = img.convert("RGBA")
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # 1. Full-size optimized WebP
            width, height = img.size
            if width > max_width:
                new_height = int(round(height * (max_width / width)))
                full_img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            else:
                full_img = img

            full_img.save(dest_full, format="WEBP", quality=quality, method=6)

            # 2. Thumbnail WebP
            if width > thumb_width:
                new_thumb_height = int(round(height * (thumb_width / width)))
                thumb_img = img.resize((thumb_width, new_thumb_height), Image.Resampling.LANCZOS)
            else:
                thumb_img = img

            thumb_img.save(dest_thumb, format="WEBP", quality=quality, method=6)

            return str(dest_full), str(dest_thumb)

    except Exception as exc:
        print(f"[WARN] Error optimizing {src.name}: {exc}", file=sys.stderr)
        return None


def batch_optimize(
    target_dir: Optional[Path | str] = None,
    max_width: int = DEFAULT_MAX_WIDTH,
    thumb_width: int = DEFAULT_THUMB_WIDTH,
    quality: int = DEFAULT_QUALITY,
) -> Dict[str, Dict[str, int | str]]:
    """Batch-optimize all valid JPEG/PNG images in the target directory."""
    if target_dir is None:
        target_dir = Path(__file__).resolve().parent.parent / "static" / "img" / "productos"
    else:
        target_dir = Path(target_dir).resolve()

    if not target_dir.is_dir():
        raise FileNotFoundError(f"Directory not found: {target_dir}")

    results: Dict[str, Dict[str, int | str]] = {}
    valid_exts = {".jpg", ".jpeg", ".png"}

    total_orig_size = 0
    total_opt_size = 0

    files = sorted(os.listdir(target_dir))
    for fname in files:
        fpath = target_dir / fname
        if not fpath.is_file():
            continue

        ext = fpath.suffix.lower()
        if ext not in valid_exts or fname.endswith("_thumb.webp"):
            continue

        orig_size = fpath.stat().st_size
        if orig_size < MIN_VALID_FILE_SIZE:
            continue

        res = optimize_image(
            fpath,
            output_dir=target_dir,
            max_width=max_width,
            thumb_width=thumb_width,
            quality=quality,
        )

        if res:
            full_path, thumb_path = res
            opt_size = os.path.getsize(full_path)
            thumb_size = os.path.getsize(thumb_path)
            total_orig_size += orig_size
            total_opt_size += opt_size

            savings = 100.0 * (1.0 - (opt_size / orig_size)) if orig_size > 0 else 0.0

            results[fname] = {
                "orig_size": orig_size,
                "opt_size": opt_size,
                "thumb_size": thumb_size,
                "savings_pct": f"{savings:.1f}%",
                "webp": os.path.basename(full_path),
                "thumb": os.path.basename(thumb_path),
            }
            print(
                f"[OK] {fname:45} | {orig_size / 1024 / 1024:5.2f}MB -> {opt_size / 1024:6.1f}KB "
                f"({savings:.1f}% savings) | thumb: {thumb_size / 1024:5.1f}KB"
            )

    net_savings = (
        100.0 * (1.0 - (total_opt_size / total_orig_size)) if total_orig_size > 0 else 0.0
    )
    print("=" * 80)
    print(
        f"OPTIMIZATION SUMMARY: {len(results)} images processed.\n"
        f"Original Total:  {total_orig_size / 1024 / 1024:.2f} MB\n"
        f"Optimized Total: {total_opt_size / 1024 / 1024:.2f} MB\n"
        f"Overall Savings: {net_savings:.1f}%"
    )
    print("=" * 80)
    return results


if __name__ == "__main__":
    cli_dir = sys.argv[1] if len(sys.argv) > 1 else None
    batch_optimize(cli_dir)
