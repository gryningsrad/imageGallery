# Image Gallery & Photo Vote Generator

A Python CLI tool that scans image folders, generates **print-friendly thumbnails**, and produces a **photo voting sheet** as a single HTML file.  
Designed for situations where images and vote boxes must appear **together on printed pages**, with controlled page breaks.

Typical use cases:

- Photo competitions
- Jury or committee voting
- Classroom or club photo reviews
- Offline / paper-based voting

---

## Features

- Recursively scans folders for images
- Generates **JPEG thumbnails** with EXIF orientation applied
- Safe, sanitized filenames with metadata (`WxH@DPI`)
- Prints **image statistics** (portrait/landscape + DPI buckets)
- Generates a **print-optimized HTML vote sheet**
- Forces **page breaks after every 4 images** when printing
- Portable output (relative paths, inline CSS)
- Non-interactive CLI (automation-friendly)

---

## Requirements

- Python **3.11+**
- Pillow

All dependencies are declared in `pyproject.toml`.

---

## Installation

### Clone the repository

    git clone https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO>.git
    cd <YOUR_REPO>

## Create and activate a virtual environment

    python -m venv .venv
## Windows

    .venv\Scripts\activate
## macOS / Linux

    source .venv/bin/activate

## Install the project (editable mode recommended)

    python -m pip install -e .

This installs the CLI command:
    image-gallery

## basic usage

### Generate thumbnails only

    python gallery_generator.py

### or, if installed as a CLI

    image-gallery

### This

scans the input folder
generates thumbnails in ./gallery/
prints image statistics
does not generate HTML

## Generate a Photo Vote HTML Sheet (recommended)

    image-gallery --html --vote-box --skip-existing

### This will

generate thumbnails
create gallery/ImageGallery.html
include a vote box under every image
insert a page break after every 4 images when printing

Open ImageGallery.html in a browser and print.

## Common Options

### Set thumbnail width

    image-gallery --thumb-width 800

### Scan a specific input folder

    image-gallery --input "C:\Photos\Contest"

### Choose output folder

    image-gallery --output "C:\Photos\Contest\gallery"

### Skip already-generated thumbnails

    image-gallery --skip-existing

### Limit processing (useful for testing)

    image-gallery --max-images 10

### Include additional file types

    image-gallery --extensions .jpg,.jpeg,.png

## Print Layout Behavior (Important)

Images are displayed in a 2-column grid
Each image + vote box is treated as a single “card”
CSS rules ensure:

- cards are never split across pages
- page breaks occur after every 4 cards
- Implemented using:
- break-after: page
- break-inside: avoid

This makes the output reliable for real-world printing.

## Output Structure

project/
  gallery_generator.py
  pyproject.toml
  README.md
  gallery/
    001-Subfolder-image-4000x3000@300.jpg
    002-Subfolder-image-3000x4000@72.jpg
    ImageGallery.html

The HTML file references images using relative paths and is fully portable.

## Image Statistics

Before generating thumbnails, the script prints counts for:

- Landscape / Portrait
- High DPI (>250)
- Low DPI (<250)
- Other (=250)

Note: DPI metadata is often unreliable; these statistics are informational only.

## CLI Reference

### Argument Description

    --input PATH  // Folder to scan (default: script folder)
    --output PATH // Output folder (default: gallery)
    --thumb-width N // Thumbnail width in pixels
    --extensions .a,.b // File extensions to include
    --skip-existing // Skip thumbnails that already exist
    --max-images N // Process at most N images
    --html // Generate ImageGallery.html
    --vote-box // Include vote boxes in HTML
    --log-level LEVEL // DEBUG / INFO / WARNING / ERROR

## Notes & Design Decisions

- Thumbnails are always saved as JPEG for consistency
- EXIF orientation is applied before resizing
- Filenames are sanitized to be filesystem- and browser-safe
- HTML uses inline CSS to avoid external dependencies
- Designed for offline and print-first workflows

## License
MIT License.