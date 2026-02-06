#!/usr/bin/env python3
"""
Extract hex colors from swatch images and add them to consolidated_colors.json
"""

import json
import os
from pathlib import Path
from PIL import Image


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to hex string format."""
    return f"#{r:02x}{g:02x}{b:02x}"


def extract_color_from_image(image_path: Path) -> str:
    """
    Extract the dominant color from a swatch image.
    Samples a 10x10 region around the center for robustness.
    """
    with Image.open(image_path) as img:
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')

        width, height = img.size
        center_x = width // 2
        center_y = height // 2

        # Sample a 10x10 region around the center for robustness
        region_size = 10
        half_size = region_size // 2

        # Calculate bounds, ensuring we stay within image
        left = max(0, center_x - half_size)
        top = max(0, center_y - half_size)
        right = min(width, center_x + half_size)
        bottom = min(height, center_y + half_size)

        # Crop the region and calculate average color
        region = img.crop((left, top, right, bottom))
        pixels = list(region.getdata())

        # Calculate average RGB
        avg_r = sum(p[0] for p in pixels) // len(pixels)
        avg_g = sum(p[1] for p in pixels) // len(pixels)
        avg_b = sum(p[2] for p in pixels) // len(pixels)

        return rgb_to_hex(avg_r, avg_g, avg_b)


def main():
    # Configuration
    json_path = Path("consolidated_colors.json")
    swatches_dir = Path("images/swatches")

    # Load the consolidated colors JSON
    print(f"Loading {json_path}...")
    with open(json_path, 'r') as f:
        data = json.load(f)

    records = data['data']
    total_records = len(records)

    print(f"Processing {total_records} records from {json_path}\n")

    # Statistics
    processed = 0
    missing_images = 0
    errors = 0

    # Process each record
    for i, record in enumerate(records, 1):
        new_code = record.get('New', '')

        if not new_code:
            print(f"[{i}/{total_records}] SKIP: No 'New' code for record")
            missing_images += 1
            continue

        # Construct image path
        image_filename = f"{new_code}.png"
        image_path = swatches_dir / image_filename

        try:
            if image_path.exists():
                hex_color = extract_color_from_image(image_path)
                record['Hex'] = hex_color
                processed += 1

                # Print progress every 50 records or for the first/last few
                if i <= 5 or i % 50 == 0 or i == total_records:
                    color_name = record.get('Color Name', 'Unknown')
                    print(f"[{i}/{total_records}] {image_filename} - {color_name} - Hex: {hex_color}")
            else:
                print(f"[{i}/{total_records}] MISSING: {image_path}")
                missing_images += 1

        except Exception as e:
            print(f"[{i}/{total_records}] ERROR processing {image_path}: {e}")
            errors += 1

    # Save the updated JSON
    print(f"\nSaving updated data to {json_path}...")
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)

    # Print summary
    print("\n" + "=" * 50)
    print("Processing complete!")
    print("=" * 50)
    print(f"Total records: {total_records}")
    print(f"Processed: {processed}")
    print(f"Missing images: {missing_images}")
    print(f"Errors: {errors}")
    print(f"\nUpdated {json_path} with Hex values")


if __name__ == "__main__":
    main()
