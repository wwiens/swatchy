#!/usr/bin/env python3
"""
Download color swatch images from consolidated_colors.json.
Saves images to images/swatches/ directory using the 'New' code as filename.
"""

import json
import os
import urllib.request
import urllib.error
from pathlib import Path


def download_swatch(url: str, output_path: Path, timeout: int = 30) -> bool:
    """
    Download a single swatch image.

    Returns True if downloaded successfully, False otherwise.
    """
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.read())
                return True
            else:
                return False
    except urllib.error.HTTPError as e:
        raise Exception(f"HTTP {e.code}")
    except urllib.error.URLError as e:
        raise Exception(f"URL error: {e.reason}")
    except Exception as e:
        raise Exception(f"{e}")


def main():
    # Configuration
    input_file = Path("consolidated_colors.json")
    output_dir = Path("images/swatches")

    # Check input file exists
    if not input_file.exists():
        print(f"Error: {input_file} not found")
        return 1

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load color data
    with open(input_file, 'r') as f:
        data = json.load(f)

    records = data.get('data', [])
    total = len(records)

    print(f"Downloading {total} swatch images to {output_dir}/")
    print()

    # Statistics
    downloaded = 0
    skipped = 0
    errors = 0

    # Process each record
    for i, record in enumerate(records, 1):
        new_code = record.get('New', '')
        url = record.get('URL', '')

        if not new_code or not url:
            print(f"[{i}/{total}] SKIP - Missing 'New' code or URL")
            errors += 1
            continue

        # Determine output filename
        output_filename = f"{new_code}.png"
        output_path = output_dir / output_filename

        # Check if already exists
        if output_path.exists():
            print(f"[{i}/{total}] {output_filename} - Already exists, skipping")
            skipped += 1
            continue

        # Download the image
        try:
            download_swatch(url, output_path)
            print(f"[{i}/{total}] {output_filename} - Downloaded")
            downloaded += 1
        except Exception as e:
            print(f"[{i}/{total}] {output_filename} - Error: {e}")
            errors += 1

    # Print summary
    print()
    print("Download complete:")
    print(f"- Downloaded: {downloaded}")
    print(f"- Skipped: {skipped}")
    print(f"- Errors: {errors}")

    return 0


if __name__ == "__main__":
    exit(main())
