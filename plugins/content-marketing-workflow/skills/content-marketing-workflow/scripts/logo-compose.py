#!/usr/bin/env python3
"""Deterministically compose one verified official logo onto a base visual.

The helper never generates, redraws, recolors or rearranges the logo. It verifies
the exact source-logo SHA-256 supplied by durable project state, resizes only
proportionally, alpha-composites the verified asset at an explicit position, and
writes a separate derivative output plus a machine-readable manifest.

Pillow is required, matching the existing asset-ingest helper dependency.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover
    raise SystemExit("logo-compose requires Pillow in the execution environment.") from exc

OUTPUT_FORMATS = {
    ".png": ("PNG", "image/png"),
    ".jpg": ("JPEG", "image/jpeg"),
    ".jpeg": ("JPEG", "image/jpeg"),
    ".webp": ("WEBP", "image/webp"),
}
POSITIONS = {
    "top-left",
    "top-center",
    "top-right",
    "center-left",
    "center",
    "center-right",
    "bottom-left",
    "bottom-center",
    "bottom-right",
}


class LogoComposeError(ValueError):
    """Raised when deterministic logo composition cannot be performed safely."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _position_box(
    base_size: tuple[int, int],
    logo_size: tuple[int, int],
    position: str,
    margin_px: int,
) -> tuple[int, int]:
    bw, bh = base_size
    lw, lh = logo_size

    if position not in POSITIONS:
        raise LogoComposeError(f"unsupported position: {position}")
    if margin_px < 0:
        raise LogoComposeError("margin_px must be >= 0")
    if lw + 2 * margin_px > bw or lh + 2 * margin_px > bh:
        raise LogoComposeError("logo plus margins does not fit inside base image")

    if position.endswith("left"):
        x = margin_px
    elif position.endswith("right"):
        x = bw - margin_px - lw
    else:
        x = (bw - lw) // 2

    if position.startswith("top"):
        y = margin_px
    elif position.startswith("bottom"):
        y = bh - margin_px - lh
    else:
        y = (bh - lh) // 2

    return x, y


def _save_image(image: Image.Image, output: Path) -> tuple[str, str]:
    suffix = output.suffix.lower()
    if suffix not in OUTPUT_FORMATS:
        raise LogoComposeError(
            "output extension must be .png, .jpg/.jpeg or .webp"
        )
    fmt, mime = OUTPUT_FORMATS[suffix]

    if fmt == "JPEG":
        image.convert("RGB").save(
            output,
            format="JPEG",
            quality=95,
            optimize=True,
            progressive=False,
            exif=b"",
        )
    elif fmt == "WEBP":
        image.save(
            output,
            format="WEBP",
            quality=95,
            method=6,
            exact=True,
        )
    else:
        image.save(
            output,
            format="PNG",
            optimize=True,
        )
    return fmt, mime


def compose_logo(
    base_path: Path,
    logo_path: Path,
    output_path: Path,
    *,
    expected_logo_sha256: str,
    position: str,
    margin_px: int,
    logo_width_px: int | None = None,
    logo_width_ratio: float | None = None,
    expected_base_sha256: str | None = None,
) -> dict[str, object]:
    if base_path.resolve() == output_path.resolve():
        raise LogoComposeError("output must not overwrite the base image")
    if logo_path.resolve() == output_path.resolve():
        raise LogoComposeError("output must not overwrite the official logo")
    if not base_path.is_file():
        raise LogoComposeError("base image does not exist")
    if not logo_path.is_file():
        raise LogoComposeError("official logo does not exist")

    actual_logo_sha = sha256_file(logo_path)
    expected_logo_sha256 = expected_logo_sha256.lower()
    if actual_logo_sha != expected_logo_sha256:
        raise LogoComposeError(
            f"official logo SHA-256 mismatch: expected {expected_logo_sha256}, "
            f"got {actual_logo_sha}"
        )

    actual_base_sha = sha256_file(base_path)
    if expected_base_sha256 is not None and actual_base_sha != expected_base_sha256.lower():
        raise LogoComposeError(
            f"base image SHA-256 mismatch: expected {expected_base_sha256.lower()}, "
            f"got {actual_base_sha}"
        )

    if (logo_width_px is None) == (logo_width_ratio is None):
        raise LogoComposeError(
            "specify exactly one of logo_width_px or logo_width_ratio"
        )

    with Image.open(base_path) as base_src, Image.open(logo_path) as logo_src:
        base_src.load()
        logo_src.load()
        base = base_src.convert("RGBA")
        logo = logo_src.convert("RGBA")
        original_logo_size = logo.size

        if logo_width_ratio is not None:
            if not 0 < logo_width_ratio <= 1:
                raise LogoComposeError("logo_width_ratio must be > 0 and <= 1")
            target_w = max(1, round(base.width * logo_width_ratio))
        else:
            assert logo_width_px is not None
            if logo_width_px <= 0:
                raise LogoComposeError("logo_width_px must be > 0")
            target_w = logo_width_px

        target_h = max(1, round(logo.height * target_w / logo.width))
        if target_w > base.width or target_h > base.height:
            raise LogoComposeError("rendered logo does not fit inside base image")

        if logo.size != (target_w, target_h):
            logo = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)

        x, y = _position_box(base.size, logo.size, position, margin_px)
        composed = base.copy()
        composed.alpha_composite(logo, dest=(x, y))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        fmt, mime = _save_image(composed, output_path)

    return {
        "base": {
            "path": str(base_path),
            "sha256": actual_base_sha,
        },
        "official_logo": {
            "path": str(logo_path),
            "sha256": actual_logo_sha,
            "source_width": original_logo_size[0],
            "source_height": original_logo_size[1],
        },
        "composition": {
            "position": position,
            "margin_px": margin_px,
            "x": x,
            "y": y,
            "rendered_width": target_w,
            "rendered_height": target_h,
        },
        "output": {
            "path": str(output_path),
            "sha256": sha256_file(output_path),
            "mime_type": mime,
            "format": fmt,
            "width": base.width,
            "height": base.height,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--logo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-logo-sha256", required=True)
    parser.add_argument("--expected-base-sha256")
    parser.add_argument("--position", choices=sorted(POSITIONS), required=True)
    parser.add_argument("--margin-px", type=int, required=True)

    width = parser.add_mutually_exclusive_group(required=True)
    width.add_argument("--logo-width-px", type=int)
    width.add_argument("--logo-width-ratio", type=float)

    args = parser.parse_args()
    manifest = compose_logo(
        args.base,
        args.logo,
        args.output,
        expected_logo_sha256=args.expected_logo_sha256,
        expected_base_sha256=args.expected_base_sha256,
        position=args.position,
        margin_px=args.margin_px,
        logo_width_px=args.logo_width_px,
        logo_width_ratio=args.logo_width_ratio,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
