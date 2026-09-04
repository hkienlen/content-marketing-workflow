#!/usr/bin/env python3
"""Validate and normalize a human-selected visual asset before GitHub ingestion.

This helper deliberately does not select assets and does not mutate GitHub or
Google Drive. The orchestrating capability resolves the selected Drive/runtime
file, canonical target path, branch and review state. This helper only turns
trusted selected image bytes into a deterministic production image plus a
verification manifest/base64 payload.

The output format is inferred from the canonical output filename:

- .webp -> WEBP, the current article default;
- .jpg/.jpeg -> JPEG, suitable for photographic social assets;
- .png -> PNG, suitable for text-heavy/flat social assets and transparency.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "asset-ingest requires Pillow in the execution environment."
    ) from exc

DEFAULT_WIDTH = 1600
DEFAULT_HEIGHT = 900
DEFAULT_QUALITY = 88
DEFAULT_MIN_QUALITY = 80
DEFAULT_TARGET_BYTES = 250 * 1024
DEFAULT_RATIO_TOLERANCE = 0.02
DEFAULT_MAX_UPSCALE = 1.25

OUTPUT_FORMATS = {
    ".webp": ("WEBP", "image/webp"),
    ".jpg": ("JPEG", "image/jpeg"),
    ".jpeg": ("JPEG", "image/jpeg"),
    ".png": ("PNG", "image/png"),
}
LOSSY_FORMATS = {"WEBP", "JPEG"}


def _ratio_distance(source_ratio: float, target_ratio: float) -> float:
    return abs(source_ratio - target_ratio) / target_ratio


def center_crop_to_ratio(
    img: Image.Image, width: int, height: int
) -> tuple[Image.Image, bool]:
    """Return a centered crop matching the target ratio and whether cropping occurred."""
    target_ratio = width / height
    src_w, src_h = img.size
    src_ratio = src_w / src_h

    if _ratio_distance(src_ratio, target_ratio) < 1e-9:
        return img, False

    if src_ratio > target_ratio:
        new_w = max(1, round(src_h * target_ratio))
        left = max(0, (src_w - new_w) // 2)
        return img.crop((left, 0, left + new_w, src_h)), True

    new_h = max(1, round(src_w / target_ratio))
    top = max(0, (src_h - new_h) // 2)
    return img.crop((0, top, src_w, top + new_h)), True


def _has_transparency(img: Image.Image) -> bool:
    return img.mode in {"RGBA", "LA"} or (
        img.mode == "P" and "transparency" in img.info
    )


def _flatten_to_rgb(img: Image.Image) -> Image.Image:
    """Convert to RGB, compositing transparent sources onto white deterministically."""
    if _has_transparency(img):
        rgba = img.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        return Image.alpha_composite(background, rgba).convert("RGB")
    return img.convert("RGB")


def _prepare_mode(img: Image.Image, output_format: str) -> tuple[Image.Image, bool]:
    """Prepare a Pillow image for the requested output format.

    PNG preserves source transparency when present. Lossy formats flatten
    transparency onto white so output bytes are deterministic and portable.
    """
    if output_format == "PNG":
        if _has_transparency(img):
            return img.convert("RGBA"), True
        return img.convert("RGB"), False
    return _flatten_to_rgb(img), False


def _encode(img: Image.Image, output_format: str, quality: int | None) -> bytes:
    buffer = io.BytesIO()
    if output_format == "WEBP":
        assert quality is not None
        img.save(buffer, "WEBP", quality=quality, method=6, optimize=True)
    elif output_format == "JPEG":
        assert quality is not None
        img.save(buffer, "JPEG", quality=quality, optimize=True, progressive=True)
    elif output_format == "PNG":
        img.save(buffer, "PNG", optimize=True, compress_level=9)
    else:  # pragma: no cover - guarded by output extension validation
        raise ValueError(f"unsupported output format: {output_format}")
    return buffer.getvalue()


def normalize_image(
    src: Path,
    dst: Path,
    *,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    quality: int = DEFAULT_QUALITY,
    min_quality: int = DEFAULT_MIN_QUALITY,
    target_bytes: int = DEFAULT_TARGET_BYTES,
    hard_max_bytes: int | None = None,
    crop: str = "strict",
    ratio_tolerance: float = DEFAULT_RATIO_TOLERANCE,
    max_upscale: float = DEFAULT_MAX_UPSCALE,
) -> dict:
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    if not (1 <= min_quality <= quality <= 100):
        raise ValueError("quality must satisfy 1 <= min_quality <= quality <= 100")
    if target_bytes <= 0:
        raise ValueError("target_bytes must be positive")
    if hard_max_bytes is not None and hard_max_bytes <= 0:
        raise ValueError("hard_max_bytes must be positive when set")
    if ratio_tolerance < 0:
        raise ValueError("ratio_tolerance must be >= 0")
    if max_upscale < 1:
        raise ValueError("max_upscale must be >= 1")
    if crop not in {"strict", "cover"}:
        raise ValueError(f"unsupported crop mode: {crop}")

    suffix = dst.suffix.lower()
    if suffix not in OUTPUT_FORMATS:
        allowed = ", ".join(sorted(OUTPUT_FORMATS))
        raise ValueError(f"output filename extension must be one of: {allowed}")
    output_format, mime_type = OUTPUT_FORMATS[suffix]

    if not src.is_file():
        raise FileNotFoundError(f"source file not found: {src}")

    try:
        with Image.open(src) as opened:
            detected_format = opened.format
            opened.load()
            oriented = ImageOps.exif_transpose(opened)
            source_size = oriented.size
            img, transparency_preserved = _prepare_mode(oriented, output_format)
    except Exception as exc:
        raise ValueError(f"source is not a decodable image: {src}: {exc}") from exc

    target_ratio = width / height
    source_ratio = img.width / img.height
    ratio_delta = _ratio_distance(source_ratio, target_ratio)
    crop_applied = False

    if crop == "strict":
        if ratio_delta > ratio_tolerance:
            raise ValueError(
                f"source ratio {source_ratio:.4f} differs from target {target_ratio:.4f} "
                f"by {ratio_delta:.2%}; explicit --crop cover is required after visual review"
            )
    else:
        img, crop_applied = center_crop_to_ratio(img, width, height)

    scale_factor = max(width / img.width, height / img.height)
    if scale_factor > max_upscale:
        raise ValueError(
            f"source is too small for {width}x{height}: required upscale {scale_factor:.3f}x "
            f"exceeds allowed {max_upscale:.3f}x"
        )

    normalized_from = img.size
    if img.size != (width, height):
        img = img.resize((width, height), Image.Resampling.LANCZOS)

    chosen_quality: int | None = quality if output_format in LOSSY_FORMATS else None
    payload = _encode(img, output_format, chosen_quality)
    while (
        output_format in LOSSY_FORMATS
        and len(payload) > target_bytes
        and chosen_quality is not None
        and chosen_quality - 2 >= min_quality
    ):
        chosen_quality -= 2
        payload = _encode(img, output_format, chosen_quality)

    size = len(payload)
    if hard_max_bytes is not None and size > hard_max_bytes:
        quality_context = (
            f" at quality {chosen_quality}" if chosen_quality is not None else ""
        )
        raise ValueError(
            f"normalized asset is {size} bytes{quality_context}; "
            f"hard maximum is {hard_max_bytes} bytes"
        )

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(payload)
    sha256 = hashlib.sha256(payload).hexdigest()

    return {
        "source_name": src.name,
        "source_format": detected_format,
        "source_width": source_size[0],
        "source_height": source_size[1],
        "output_name": dst.name,
        "output_format": output_format,
        "mime_type": mime_type,
        "output_width": width,
        "output_height": height,
        "output_bytes": size,
        "quality": chosen_quality,
        "sha256": sha256,
        "crop_mode": crop,
        "crop_applied": crop_applied,
        "ratio_delta": round(ratio_delta, 8),
        "ratio_tolerance": ratio_tolerance,
        "normalized_from_width": normalized_from[0],
        "normalized_from_height": normalized_from[1],
        "upscale_factor": round(scale_factor, 6),
        "max_upscale": max_upscale,
        "target_bytes": target_bytes,
        "target_bytes_met": size <= target_bytes,
        "hard_max_bytes": hard_max_bytes,
        "transparency_preserved": transparency_preserved,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and normalize a selected image for binary-safe GitHub ingestion."
    )
    parser.add_argument(
        "source", type=Path, help="Selected source image from Drive/runtime"
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Canonical output path (.webp, .jpg/.jpeg or .png); extension selects format",
    )
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument(
        "--quality",
        type=int,
        default=DEFAULT_QUALITY,
        help="Initial WEBP/JPEG quality; ignored for lossless PNG",
    )
    parser.add_argument(
        "--min-quality",
        type=int,
        default=DEFAULT_MIN_QUALITY,
        help="Minimum automatic WEBP/JPEG quality; ignored for PNG",
    )
    parser.add_argument(
        "--target-bytes",
        type=int,
        default=DEFAULT_TARGET_BYTES,
        help="Soft size target; lossy quality will not be reduced below --min-quality",
    )
    parser.add_argument(
        "--hard-max-bytes",
        type=int,
        default=0,
        help="Optional hard failure limit; 0 disables a universal hard cap",
    )
    parser.add_argument(
        "--crop",
        choices=["strict", "cover"],
        default="strict",
        help="strict rejects material ratio drift; cover permits explicit centered cropping",
    )
    parser.add_argument(
        "--ratio-tolerance", type=float, default=DEFAULT_RATIO_TOLERANCE
    )
    parser.add_argument("--max-upscale", type=float, default=DEFAULT_MAX_UPSCALE)
    parser.add_argument("--manifest", type=Path, help="Optional JSON manifest output")
    parser.add_argument(
        "--base64-output",
        type=Path,
        help="Optional base64 payload file for GitHub create_blob",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    hard_max = args.hard_max_bytes or None

    try:
        manifest = normalize_image(
            args.source,
            args.output,
            width=args.width,
            height=args.height,
            quality=args.quality,
            min_quality=args.min_quality,
            target_bytes=args.target_bytes,
            hard_max_bytes=hard_max,
            crop=args.crop,
            ratio_tolerance=args.ratio_tolerance,
            max_upscale=args.max_upscale,
        )
    except Exception as exc:
        print(f"asset-ingest: {exc}", file=sys.stderr)
        return 2

    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    if args.base64_output:
        args.base64_output.parent.mkdir(parents=True, exist_ok=True)
        args.base64_output.write_text(
            base64.b64encode(args.output.read_bytes()).decode("ascii"),
            encoding="ascii",
        )

    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
