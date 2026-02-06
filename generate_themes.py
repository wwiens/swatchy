#!/usr/bin/env python3
"""
Theme Generator Script for Swatchy

Generates random color palettes in bulk for each color in the dataset.
For each color, generates multiple random palettes of varying sizes (3, 4, 5, and 6 colors).
"""

import json
import random
from pathlib import Path


def load_colors(filepath: str) -> list[dict]:
    """Load and parse colors.json into a list of color dictionaries."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    colors = []
    for name, attrs in data.items():
        colors.append({
            'name': name,
            'code': attrs['New'],
            'hex': attrs['Hex']
        })

    return colors


def generate_palette(seed_color: dict, palette_size: int, all_colors: list[dict]) -> list[dict]:
    """
    Generate a random palette with the seed color and random unique colors.

    Args:
        seed_color: The seed color dict with name, code, hex
        palette_size: Total number of colors in the palette (including seed)
        all_colors: List of all available colors

    Returns:
        List of color dictionaries forming the palette
    """
    # Exclude seed color from pool, then randomly sample without replacement
    available = [c for c in all_colors if c['name'] != seed_color['name']]

    # Need enough colors available
    if len(available) < palette_size - 1:
        raise ValueError(f"Not enough colors available. Need {palette_size - 1}, have {len(available)}")

    selected = random.sample(available, palette_size - 1)
    palette = [seed_color] + selected

    return palette


def main():
    """Orchestrate theme generation and save to JSON."""
    # Configuration
    colors_file = Path('static/data/colors.json')
    output_file = Path('generated_themes.json')

    # Palettes per size configuration
    palettes_per_size = 5
    palette_sizes = [3, 4, 5, 6]

    # Colors to exclude from being seed colors
    seed_exclusions = {'Black', 'Colorless Blender'}

    # Load color data
    print(f"Loading colors from {colors_file}...")
    all_colors = load_colors(colors_file)
    print(f"Loaded {len(all_colors)} colors")

    # Filter seed candidates
    seed_candidates = [c for c in all_colors if c['name'] not in seed_exclusions]
    print(f"Seed candidates: {len(seed_candidates)} (excluded: {seed_exclusions})")

    # Generate themes
    themes = []
    total_palettes = len(seed_candidates) * len(palette_sizes) * palettes_per_size
    print(f"Generating {total_palettes} total palettes...")

    for seed_color in seed_candidates:
        for size in palette_sizes:
            for _ in range(palettes_per_size):
                palette = generate_palette(seed_color, size, all_colors)

                theme = {
                    'seed_color': seed_color['name'],
                    'seed_code': seed_color['code'],
                    'seed_hex': seed_color['hex'],
                    'palette_size': size,
                    'colors': palette
                }
                themes.append(theme)

    # Save to JSON
    output = {'themes': themes}
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nGenerated {len(themes)} themes")
    print(f"Saved to {output_file}")

    # Print some statistics
    print("\nStatistics:")
    print(f"  Total themes: {len(themes)}")
    print(f"  Seeds used: {len(seed_candidates)}")
    print(f"  Palettes per seed: {len(palette_sizes) * palettes_per_size}")
    for size in palette_sizes:
        count = len([t for t in themes if t['palette_size'] == size])
        print(f"  Size {size} palettes: {count}")


if __name__ == '__main__':
    main()
