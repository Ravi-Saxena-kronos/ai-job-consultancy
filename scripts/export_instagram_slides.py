#!/usr/bin/env python3
"""Export slide HTML to PNG/JPEG sequence for social carousel posts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HTML = ROOT / "public" / "instagram-slides.html"
DEFAULT_OUT = ROOT / "public" / "instagram-carousel"


def _maybe_jpeg(png_path: Path) -> None:
    try:
        from PIL import Image
    except ImportError:
        return
    jpg = png_path.with_suffix(".jpg")
    Image.open(png_path).convert("RGB").save(jpg, "JPEG", quality=92)
    print(f"Wrote {jpg}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export section.slide elements to PNG files")
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML, help="Slide HTML file")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output directory")
    parser.add_argument("--jpeg", action="store_true", help="Also write .jpg next to each PNG")
    args = parser.parse_args()

    html_path = args.html if args.html.is_absolute() else ROOT / args.html
    out_dir = args.out if args.out.is_absolute() else ROOT / args.out

    if not html_path.is_file():
        print(f"Missing {html_path}", file=sys.stderr)
        return 1
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Run: pip install playwright && playwright install chromium", file=sys.stderr)
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)
    url = html_path.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 1200}, device_scale_factor=2)
        page.goto(url, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(1500)
        slides = page.locator("section.slide")
        count = slides.count()
        if count == 0:
            print("No section.slide elements found", file=sys.stderr)
            browser.close()
            return 3
        paths: list[Path] = []
        for i in range(count):
            num = i + 1
            path = out_dir / f"{num:02d}-slide.png"
            slides.nth(i).screenshot(path=str(path), type="png")
            paths.append(path)
            print(f"Wrote {path}")
            if args.jpeg:
                _maybe_jpeg(path)
        browser.close()

    print(f"\nDone: {len(paths)} PNGs in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
