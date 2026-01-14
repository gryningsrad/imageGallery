# Image Thumbnail Gallery Generator

A small Python script that scans all subfolders under the script directory for `.jpg/.jpeg` images, generates **thumbnails**, and writes a simple **HTML gallery** to browse them.

It also prints basic statistics about the images (landscape/portrait + DPI categories).

## What it does

- Recursively searches for `.jpg` / `.jpeg` under the folder where the script lives
- Skips the output folder named `gallery/` to avoid re-processing generated files
- For every image found:
  - Reads width/height and DPI metadata (defaults to 72 if missing)
  - Corrects image orientation using EXIF `Orientation` tag (if present)
  - Generates a thumbnail (default width: `600px`, height scaled by aspect ratio)
  - Saves the thumbnail into `./gallery/` with a renamed filename that includes:
    - a running serial number
    - the source subfolder name
    - original filename
    - `WIDTHxHEIGHT@DPI`

- Optionally generates `gallery/ImageGallery.html` that lists images (grouped by DPI suffix in filename)

## Requirements

- Python 3.10+ recommended
- Pillow (PIL)

## Installation

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install pillow
