#!/usr/bin/env python3
"""
Image Thumbnail Gallery Generator (patched)

"""

from __future__ import annotations

import argparse
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageOps


# ----------------------------
# Defaults
# ----------------------------

DEFAULT_OUTPUT_FOLDER_NAME = "gallery"
DEFAULT_THUMB_WIDTH = 600
DEFAULT_EXTENSIONS = (".jpg", ".jpeg")

DPI_THRESHOLD = 250  # consistent across orientations

# ----------------------------
# Data structures
# ----------------------------

@dataclass(frozen=True)
class ImageInfo:
    width: int
    height: int
    dpi: int  # integer DPI (x axis)


@dataclass
class Stats:
    landscape_high_dpi: int = 0
    landscape_low_dpi: int = 0
    landscape_other_dpi: int = 0
    portrait_high_dpi: int = 0
    portrait_low_dpi: int = 0
    portrait_other_dpi: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "landscape_high_dpi": self.landscape_high_dpi,
            "landscape_low_dpi": self.landscape_low_dpi,
            "landscape_other_dpi": self.landscape_other_dpi,
            "portrait_high_dpi": self.portrait_high_dpi,
            "portrait_low_dpi": self.portrait_low_dpi,
            "portrait_other_dpi": self.portrait_other_dpi,
        }


HEADERS = {
    "landscape_high_dpi": f"Landscape High DPI (>{DPI_THRESHOLD})",
    "landscape_low_dpi": f"Landscape Low DPI (<{DPI_THRESHOLD})",
    "landscape_other_dpi": f"Landscape Other DPI (={DPI_THRESHOLD})",
    "portrait_high_dpi": f"Portrait High DPI (>{DPI_THRESHOLD})",
    "portrait_low_dpi": f"Portrait Low DPI (<{DPI_THRESHOLD})",
    "portrait_other_dpi": f"Portrait Other DPI (={DPI_THRESHOLD})",
}


# ----------------------------
# Helpers
# ----------------------------

def sanitize_for_filename(text: str, max_len: int = 120) -> str:
    """
    Safer filenames for browsers/filesystems:
    - whitespace -> underscore
    - remove problematic characters
    - collapse repeats
    """
    text = text.strip()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text[:max_len].strip("-_.")


def parse_extensions(raw: str) -> tuple[str, ...]:
    """
    "--extensions .jpg,.jpeg,.png" -> (".jpg",".jpeg",".png")
    """
    parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
    exts = []
    for p in parts:
        if not p.startswith("."):
            p = "." + p
        exts.append(p)
    return tuple(exts) if exts else tuple(DEFAULT_EXTENSIONS)


def iter_images(base_folder: Path, output_folder: Path, extensions: Sequence[str]) -> Iterable[Path]:
    """
    Yield image paths under base_folder recursively, excluding output_folder subtree.
    """
    output_folder = output_folder.resolve()
    extensions_set = {e.lower() for e in extensions}

    # classic walk is fast and lets us prune
    for root, dirs, files in __import__("os").walk(base_folder):
        root_path = Path(root)

        # prune output folder
        if output_folder.name in dirs and (root_path / output_folder.name).resolve() == output_folder:
            dirs.remove(output_folder.name)

        for name in files:
            p = root_path / name
            if p.suffix.lower() in extensions_set:
                yield p


def dpi_from_img_info(img: Image.Image) -> int:
    """
    Read dpi from PIL info; default to 72 if missing/invalid.
    """
    dpi_tuple = img.info.get("dpi", (72, 72))
    try:
        return int(round(float(dpi_tuple[0])))
    except Exception:
        return 72


def classify_image(info: ImageInfo) -> str:
    """
    Returns a Stats field name.
    Uses consistent thresholds:
        high: > DPI_THRESHOLD
        low:  < DPI_THRESHOLD
        other: == DPI_THRESHOLD
    """
    is_landscape = info.width > info.height  # squares count as portrait bucket

    if is_landscape:
        if info.dpi > DPI_THRESHOLD:
            return "landscape_high_dpi"
        if info.dpi < DPI_THRESHOLD:
            return "landscape_low_dpi"
        return "landscape_other_dpi"

    # portrait / square
    if info.dpi > DPI_THRESHOLD:
        return "portrait_high_dpi"
    if info.dpi < DPI_THRESHOLD:
        return "portrait_low_dpi"
    return "portrait_other_dpi"


def build_output_filename(serial: int, source_subfolder: str, original_name: str, info: ImageInfo) -> str:
    """
    Serial + subfolder + original stem + WxH@DPI
    Output is always JPG.
    """
    sub = sanitize_for_filename(source_subfolder)
    orig = sanitize_for_filename(Path(original_name).stem)
    return f"{serial:03d}-{sub}-{orig}-{info.width}x{info.height}@{info.dpi}.jpg"


def thumb_size_for_width(img: Image.Image, thumb_width: int) -> tuple[int, int]:
    """
    Compute (thumb_width, proportional_height) from current image size.
    """
    w, h = img.size
    if w <= 0 or h <= 0:
        raise ValueError("Invalid image dimensions")
    new_h = round(thumb_width * (h / w))
    return thumb_width, max(1, new_h)


# ----------------------------
# Core operations (single-pass)
# ----------------------------

def collect_stats(base_folder: Path, output_folder: Path, extensions: Sequence[str]) -> Stats:
    stats = Stats()

    for image_path in iter_images(base_folder, output_folder, extensions):
        try:
            with Image.open(image_path) as img:
                img = ImageOps.exif_transpose(img)
                info = ImageInfo(width=img.size[0], height=img.size[1], dpi=dpi_from_img_info(img))
        except Exception as e:
            logging.warning("Skipping unreadable image for stats: %s (%s)", image_path, e)
            continue

        field = classify_image(info)
        setattr(stats, field, getattr(stats, field) + 1)

    return stats


def generate_thumbnails(
    base_folder: Path,
    output_folder: Path,
    thumb_width: int,
    extensions: Sequence[str],
    skip_existing: bool,
    max_images: int | None,
) -> int:
    output_folder.mkdir(parents=True, exist_ok=True)

    serial = 1
    created = 0

    for image_path in iter_images(base_folder, output_folder, extensions):
        if max_images is not None and created >= max_images:
            break

        try:
            with Image.open(image_path) as img:
                # Apply EXIF orientation first so W/H reflect how it should display
                img = ImageOps.exif_transpose(img)

                info = ImageInfo(width=img.size[0], height=img.size[1], dpi=dpi_from_img_info(img))

                source_subfolder = image_path.parent.name
                out_name = build_output_filename(serial, source_subfolder, image_path.name, info)
                out_path = output_folder / out_name

                if skip_existing and out_path.exists():
                    logging.info("Skipping existing: %s", out_path.name)
                    serial += 1
                    continue

                tw, th = thumb_size_for_width(img, thumb_width)
                img.thumbnail((tw, th), resample=Image.Resampling.LANCZOS)

                # Ensure JPEG-compatible mode
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                img.save(out_path, format="JPEG", quality=85, optimize=True, progressive=True)

        except Exception as e:
            logging.warning("Failed processing image: %s (%s)", image_path, e)
            serial += 1
            continue

        logging.info("Thumbnail created: %s -> %s", image_path.name, out_path.name)
        serial += 1
        created += 1

    return created


def generate_html_gallery(output_folder: Path, vote_box: bool) -> Path:
    """
    Photo-vote HTML:
    - Image + vote box as one "card"
    - Page break after every 4 cards when printing
    - Inline CSS so it's portable
    """
    images = sorted(
        [p.name for p in output_folder.iterdir()
            if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg"}]
    )

    # Inline CSS: screen grid + print paging
    css = """
    :root { --gap: 16px; --border: 1px solid #ddd; --radius: 12px; }
    body { font-family: Arial, sans-serif; margin: 16px; }
    h1 { margin: 0 0 16px 0; }

    .gallery {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: var(--gap);
        align-items: start;
    }

    .card {
        border: var(--border);
        border-radius: var(--radius);
        padding: 12px;
    }

    .card img {
        width: 100%;
        height: auto;
        display: block;
        border-radius: 10px;
    }

    .meta {
        margin: 10px 0 8px 0;
        font-size: 14px;
    }

    .vote {
    border: 2px dashed #333;
    border-radius: 10px;
    height: 90px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    letter-spacing: 1px;
    user-select: none;
    }

    /* Printing rules */
    @media print {
        body { margin: 10mm; }
        .gallery { gap: 10mm; }
        .card { break-inside: avoid; page-break-inside: avoid; }
        .page-break { break-after: page; page-break-after: always; }

      /* Optional: remove borders for cleaner print, uncomment if desired */
      /* .card { border: none; padding: 0; } */
    }
    """

    cards_html = []
    for idx, name in enumerate(images, start=1):
        serial = name.split("-", 1)[0] if "-" in name else str(idx)
        # add page-break after every 4th card
        extra_class = " page-break" if (idx % 4 == 0) else ""

        vote_html = "<div class='vote'>VOTE HERE</div>" if vote_box else ""
        cards_html.append(
            f"""
            <div class="card{extra_class}">
                <img src="./{name}" alt="{name}" title="{name}">
                <div class="meta">Image nr # {serial}</div>
                {vote_html}
            </div>
            """
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Photo Vote Sheet</title>
    <style>
    {css}
</style>
</head>
<body>
<h1>Photo Vote Sheet</h1>
<div class="gallery">
    {''.join(cards_html)}
    </div>
</body>
</html>
"""

    out_file = output_folder / "ImageGallery.html"
    out_file.write_text(html, encoding="utf-8")
    logging.info("HTML gallery written: %s", out_file)
    return out_file



# ----------------------------
# CLI / main
# ----------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate thumbnails and an optional HTML gallery.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Base folder to scan (default: folder of this script).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"Output folder (default: <input>/{DEFAULT_OUTPUT_FOLDER_NAME}).",
    )
    parser.add_argument(
        "--thumb-width",
        type=int,
        default=DEFAULT_THUMB_WIDTH,
        help=f"Thumbnail width in pixels (default: {DEFAULT_THUMB_WIDTH}).",
    )
    parser.add_argument(
        "--extensions",
        type=str,
        default=",".join(DEFAULT_EXTENSIONS),
        help='Comma-separated extensions, e.g. ".jpg,.jpeg" (default: ".jpg,.jpeg").',
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip creating a thumbnail if the output file already exists.",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        help="Process at most N images (useful for quick tests).",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate ImageGallery.html in the output folder.",
    )
    parser.add_argument(
        "--vote-box",
        action="store_true",
        help="Include a 'VOTE HERE' box under each image in the HTML gallery (only with --html).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s: %(message)s",
    )

    base_folder: Path = args.input.resolve()
    output_folder: Path = (args.output.resolve() if args.output else (base_folder / DEFAULT_OUTPUT_FOLDER_NAME))
    extensions = parse_extensions(args.extensions)

    logging.info("Input folder:   %s", base_folder)
    logging.info("Output folder:  %s", output_folder)
    logging.info("Thumb width:    %s px", args.thumb_width)
    logging.info("Extensions:     %s", ", ".join(extensions))
    logging.info("Skip existing:  %s", args.skip_existing)
    if args.max_images is not None:
        logging.info("Max images:     %s", args.max_images)

    stats = collect_stats(base_folder, output_folder, extensions)
    logging.info("Image statistics:")
    for key, value in stats.as_dict().items():
        print(f"{HEADERS.get(key, key)}: {value}")

    created = generate_thumbnails(
        base_folder=base_folder,
        output_folder=output_folder,
        thumb_width=args.thumb_width,
        extensions=extensions,
        skip_existing=args.skip_existing,
        max_images=args.max_images,
    )
    logging.info("Thumbnails created: %d", created)

    if args.html:
        generate_html_gallery(output_folder, vote_box=args.vote_box)

    logging.info("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
