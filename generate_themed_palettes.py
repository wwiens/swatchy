#!/usr/bin/env python3
"""
Generate themed color palettes using color harmony rules.
Uses HSV color space for harmony calculations.
"""

import json
import colorsys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import random

@dataclass
class Color:
    name: str
    code: str
    hex: str
    hsv: Tuple[float, float, float]

    @property
    def hue(self) -> float:
        return self.hsv[0]

    @property
    def saturation(self) -> float:
        return self.hsv[1]

    @property
    def value(self) -> float:
        return self.hsv[2]


def hex_to_hsv(hex_color: str) -> Tuple[float, float, float]:
    """Convert hex color to HSV tuple (hue: 0-360, saturation: 0-1, value: 0-1)."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return (h * 360, s, v)


def hue_distance(h1: float, h2: float) -> float:
    """Calculate the shortest distance between two hues on the color wheel."""
    diff = abs(h1 - h2)
    return min(diff, 360 - diff)


def normalize_hue(hue: float) -> float:
    """Normalize hue to 0-360 range."""
    while hue < 0:
        hue += 360
    while hue >= 360:
        hue -= 360
    return hue


def is_warm_hue(hue: float) -> bool:
    """Check if a hue is warm (reds, oranges, yellows, magentas)."""
    # Warm: 330-360, 0-60 (reds, oranges, yellows)
    # Also include 300-330 as warm (magentas/purples)
    return hue >= 300 or hue <= 60


def is_cool_hue(hue: float) -> bool:
    """Check if a hue is cool (greens, cyans, blues, purples)."""
    return 60 < hue < 300


def load_colors(filepath: str) -> List[Color]:
    """Load colors from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    colors = []
    for item in data['data']:
        hex_val = item.get('Hex', '')
        if not hex_val or hex_val == '#ffffff':  # Skip colorless blender
            continue

        # Ensure hex starts with #
        if not hex_val.startswith('#'):
            hex_val = '#' + hex_val

        try:
            hsv = hex_to_hsv(hex_val)
            color = Color(
                name=item.get('Color Name', 'Unknown'),
                code=item.get('New', ''),
                hex=hex_val,
                hsv=hsv
            )
            colors.append(color)
        except (ValueError, KeyError):
            continue

    return colors


def find_colors_by_hue_range(
    colors: List[Color],
    target_hue: float,
    tolerance: float,
    exclude: Optional[List[Color]] = None,
    min_saturation: float = 0.05,
    count: int = 5
) -> List[Color]:
    """Find colors within a hue range of the target, sorted by proximity."""
    exclude_codes = {c.code for c in (exclude or [])}

    candidates = []
    for c in colors:
        if c.code in exclude_codes:
            continue
        if c.saturation < min_saturation:
            continue

        dist = hue_distance(c.hue, target_hue)
        if dist <= tolerance:
            candidates.append((dist, c))

    # Sort by distance and return top matches
    candidates.sort(key=lambda x: x[0])
    return [c for _, c in candidates[:count]]


def score_color_for_palette(
    color: Color,
    target_hue: float,
    existing_colors: List[Color],
    target_saturation: Optional[float] = None
) -> float:
    """Score a color for inclusion in a palette. Higher is better."""
    score = 0.0

    # Hue proximity (closer is better)
    hue_dist = hue_distance(color.hue, target_hue)
    score += (1.0 - hue_dist / 180) * 30

    # Saturation balance
    if existing_colors:
        avg_sat = sum(c.saturation for c in existing_colors) / len(existing_colors)
        if target_saturation:
            avg_sat = target_saturation
        sat_diff = abs(color.saturation - avg_sat)
        score += (1.0 - min(sat_diff * 2, 1.0)) * 20

    # Value contrast with existing colors
    if existing_colors:
        min_value_diff = min(abs(color.value - c.value) for c in existing_colors)
        if min_value_diff > 0.1:  # Good contrast
            score += 25
        elif min_value_diff > 0.05:
            score += 10

    # Avoid very low saturation (grays)
    if color.saturation < 0.1:
        score -= 30

    # Slight preference for medium-high saturation
    if 0.3 <= color.saturation <= 0.8:
        score += 10

    return score


def select_best_colors(
    candidates: List[Color],
    target_hue: float,
    count: int,
    existing: List[Color],
    target_saturation: Optional[float] = None
) -> List[Color]:
    """Select the best colors from candidates based on scoring."""
    if len(candidates) <= count:
        return candidates

    scored = [(score_color_for_palette(c, target_hue, existing, target_saturation), c) for c in candidates]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:count]]


def generate_analogous(seed: Color, count: int, colors: List[Color]) -> Optional[List[Color]]:
    """Generate analogous palette: colors within ±30-60° of seed."""
    if count < 2:
        return [seed]

    palette = [seed]
    remaining = count - 1

    # Split remaining between lower and higher hues
    lower_count = remaining // 2
    higher_count = remaining - lower_count

    # Find colors with lower hue (counter-clockwise)
    for i in range(lower_count):
        target_hue = normalize_hue(seed.hue - (30 + i * 20))
        candidates = find_colors_by_hue_range(colors, target_hue, 35, exclude=palette, count=10)
        best = select_best_colors(candidates, target_hue, 1, palette)
        if best:
            palette.insert(1, best[0])  # Insert after seed

    # Find colors with higher hue (clockwise)
    for i in range(higher_count):
        target_hue = normalize_hue(seed.hue + (30 + i * 20))
        candidates = find_colors_by_hue_range(colors, target_hue, 35, exclude=palette, count=10)
        best = select_best_colors(candidates, target_hue, 1, palette)
        if best:
            palette.append(best[0])

    if len(palette) < count:
        return None

    return palette[:count]


def generate_complementary(seed: Color, count: int, colors: List[Color]) -> Optional[List[Color]]:
    """Generate complementary palette: seed + colors around 180° offset."""
    if count < 2:
        return [seed]

    palette = [seed]
    complement_hue = normalize_hue(seed.hue + 180)

    # Add complement
    candidates = find_colors_by_hue_range(colors, complement_hue, 30, exclude=palette, count=10)
    best = select_best_colors(candidates, complement_hue, 1, palette)
    if best:
        palette.append(best[0])

    # Add bridge colors if needed
    remaining = count - len(palette)
    for i in range(remaining):
        # Alternate between sides of the complement
        offset = 30 + i * 15
        if i % 2 == 0:
            target_hue = normalize_hue(complement_hue + offset)
        else:
            target_hue = normalize_hue(seed.hue + offset)

        candidates = find_colors_by_hue_range(colors, target_hue, 25, exclude=palette, count=10)
        best = select_best_colors(candidates, target_hue, 1, palette)
        if best:
            palette.append(best[0])

    if len(palette) < count:
        return None

    return palette[:count]


def generate_split_complementary(seed: Color, count: int, colors: List[Color]) -> Optional[List[Color]]:
    """Generate split complementary: seed + two colors adjacent to complement (~150° and ~210°)."""
    if count < 2:
        return [seed]

    palette = [seed]

    # Split complement hues
    split1_hue = normalize_hue(seed.hue + 150)
    split2_hue = normalize_hue(seed.hue + 210)

    # Add split complements
    for target_hue in [split1_hue, split2_hue]:
        candidates = find_colors_by_hue_range(colors, target_hue, 30, exclude=palette, count=10)
        best = select_best_colors(candidates, target_hue, 1, palette)
        if best:
            palette.append(best[0])

    # Add accent colors if needed
    remaining = count - len(palette)
    for i in range(remaining):
        # Add colors that bridge the gaps
        if i % 2 == 0:
            target_hue = normalize_hue(seed.hue + 60 + i * 10)
        else:
            target_hue = normalize_hue(seed.hue - 60 - i * 10)

        candidates = find_colors_by_hue_range(colors, target_hue, 30, exclude=palette, count=10)
        best = select_best_colors(candidates, target_hue, 1, palette)
        if best:
            palette.append(best[0])

    if len(palette) < count:
        return None

    return palette[:count]


def generate_triadic(seed: Color, count: int, colors: List[Color]) -> Optional[List[Color]]:
    """Generate triadic palette: three colors evenly spaced (0°, 120°, 240°)."""
    if count < 2:
        return [seed]

    palette = [seed]

    # Triadic hues
    triad1_hue = normalize_hue(seed.hue + 120)
    triad2_hue = normalize_hue(seed.hue + 240)

    # Add triadic colors
    for target_hue in [triad1_hue, triad2_hue]:
        candidates = find_colors_by_hue_range(colors, target_hue, 35, exclude=palette, count=10)
        best = select_best_colors(candidates, target_hue, 1, palette)
        if best:
            palette.append(best[0])

    # Add bridge colors if needed
    remaining = count - len(palette)
    triadic_hues = [seed.hue, triad1_hue, triad2_hue]

    for i in range(remaining):
        # Add colors between triadic points
        base_idx = i % 3
        next_idx = (base_idx + 1) % 3
        target_hue = normalize_hue((triadic_hues[base_idx] + triadic_hues[next_idx]) / 2)

        candidates = find_colors_by_hue_range(colors, target_hue, 25, exclude=palette, count=10)
        best = select_best_colors(candidates, target_hue, 1, palette)
        if best:
            palette.append(best[0])

    if len(palette) < count:
        return None

    return palette[:count]


def generate_monochromatic(seed: Color, count: int, colors: List[Color]) -> Optional[List[Color]]:
    """Generate monochromatic palette: same hue, varying saturation/value."""
    if count < 2:
        return [seed]

    palette = [seed]

    # Find colors with similar hue but different saturation/value
    # Use a wider tolerance to find more candidates
    hue_tolerance = 25
    candidates = []

    for c in colors:
        if c.code == seed.code:
            continue
        if hue_distance(c.hue, seed.hue) <= hue_tolerance:
            # Score by value difference for variety
            value_diff = abs(c.value - seed.value)
            sat_diff = abs(c.saturation - seed.saturation)
            score = value_diff + sat_diff * 0.5
            candidates.append((score, c))

    # Sort by variation (higher score = more different)
    candidates.sort(key=lambda x: x[0], reverse=True)

    for _, c in candidates[:count-1]:
        palette.append(c)

    # If we don't have enough, try expanding the hue tolerance
    if len(palette) < count:
        for c in colors:
            if c.code == seed.code or c in palette:
                continue
            if hue_distance(c.hue, seed.hue) <= 40:  # Wider tolerance
                palette.append(c)
                if len(palette) >= count:
                    break

    if len(palette) < count:
        return None

    return palette[:count]


def generate_warm_cool_mix(seed: Color, count: int, colors: List[Color]) -> Optional[List[Color]]:
    """Generate warm/cool mix palette: combines warm and cool tones."""
    if count < 2:
        return [seed]

    palette = [seed]
    seed_is_warm = is_warm_hue(seed.hue)

    # Determine how many warm and cool colors we need
    if seed_is_warm:
        warm_count = count // 2 + 1
        cool_count = count - warm_count
    else:
        cool_count = count // 2 + 1
        warm_count = count - cool_count

    # Add warm colors
    warm_added = 0
    if seed_is_warm:
        warm_added = 1

    while warm_added < warm_count:
        # Pick a warm hue
        warm_hues = list(range(330, 361)) + list(range(0, 61))
        target_hue = random.choice(warm_hues)
        candidates = find_colors_by_hue_range(colors, target_hue, 40, exclude=palette, count=10)
        best = select_best_colors(candidates, target_hue, 1, palette)
        if best:
            palette.append(best[0])
            warm_added += 1
        else:
            break

    # Add cool colors
    cool_added = 0 if seed_is_warm else 1

    while cool_added < cool_count:
        # Pick a cool hue
        cool_hues = list(range(70, 291))
        target_hue = random.choice(cool_hues)
        candidates = find_colors_by_hue_range(colors, target_hue, 40, exclude=palette, count=10)
        best = select_best_colors(candidates, target_hue, 1, palette)
        if best:
            palette.append(best[0])
            cool_added += 1
        else:
            break

    if len(palette) < count:
        return None

    return palette[:count]


def generate_tetradic(seed: Color, count: int, colors: List[Color]) -> Optional[List[Color]]:
    """Generate tetradic (double complementary) palette: four colors forming rectangle on wheel."""
    if count < 2:
        return [seed]

    palette = [seed]

    # Tetradic hues (rectangle on color wheel)
    # Using 60° offset for one pair
    offset = 60
    tetrad_hues = [
        normalize_hue(seed.hue + offset),
        normalize_hue(seed.hue + 180),
        normalize_hue(seed.hue + 180 + offset)
    ]

    for target_hue in tetrad_hues:
        candidates = find_colors_by_hue_range(colors, target_hue, 30, exclude=palette, count=10)
        best = select_best_colors(candidates, target_hue, 1, palette)
        if best:
            palette.append(best[0])

    # Add bridge colors if needed
    remaining = count - len(palette)
    for i in range(remaining):
        # Add colors between existing ones
        if len(palette) >= 2:
            target_hue = normalize_hue((palette[i % len(palette)].hue + palette[(i + 1) % len(palette)].hue) / 2)
        else:
            target_hue = normalize_hue(seed.hue + 90 + i * 45)

        candidates = find_colors_by_hue_range(colors, target_hue, 25, exclude=palette, count=10)
        best = select_best_colors(candidates, target_hue, 1, palette)
        if best:
            palette.append(best[0])

    if len(palette) < count:
        return None

    return palette[:count]


# Theme naming data
ADJECTIVES = {
    'warm': ['Sunny', 'Golden', 'Fiery', 'Warm', 'Tropical', 'Sunset', 'Desert', 'Autumn', 'Spicy', 'Cozy'],
    'cool': ['Icy', 'Cool', 'Fresh', 'Crisp', 'Arctic', 'Ocean', 'Winter', 'Breezy', 'Calm', 'Serene'],
    'neutral': ['Soft', 'Gentle', 'Dreamy', 'Elegant', 'Subtle', 'Delicate', 'Smooth', 'Muted', 'Pastel', 'Light'],
    'vibrant': ['Vibrant', 'Bold', 'Bright', 'Electric', 'Neon', 'Intense', 'Lively', 'Radiant', 'Dynamic', 'Vivid'],
    'deep': ['Deep', 'Rich', 'Dark', 'Midnight', 'Shadow', 'Mystic', 'Royal', 'Luxurious', 'Velvet', 'Dramatic']
}

HARMONY_NAMES = {
    'analogous': 'Blend',
    'complementary': 'Contrast',
    'split_complementary': 'Harmony',
    'triadic': 'Trio',
    'monochromatic': 'Shades',
    'warm_cool': 'Fusion',
    'tetradic': 'Quartet'
}


def get_color_temperature(hue: float, saturation: float) -> str:
    """Determine color temperature category."""
    if saturation < 0.2:
        return 'neutral'
    if is_warm_hue(hue):
        return 'warm'
    return 'cool'


def get_palette_temperature(palette: List[Color]) -> str:
    """Determine overall palette temperature."""
    temps = [get_color_temperature(c.hue, c.saturation) for c in palette]
    warm_count = temps.count('warm')
    cool_count = temps.count('cool')

    if warm_count > cool_count + 1:
        return 'warm'
    elif cool_count > warm_count + 1:
        return 'cool'

    # Check average saturation for vibrant vs neutral
    avg_sat = sum(c.saturation for c in palette) / len(palette)
    if avg_sat > 0.6:
        return 'vibrant'
    elif avg_sat < 0.3:
        return 'neutral'

    return 'neutral'


def generate_theme_name(seed: Color, harmony_type: str, palette: List[Color]) -> str:
    """Generate a descriptive theme name."""
    temp = get_palette_temperature(palette)
    adj = random.choice(ADJECTIVES[temp])
    harmony = HARMONY_NAMES.get(harmony_type, 'Mix')

    # Use seed name (first word if multi-word)
    seed_short = seed.name.split()[0]

    # Occasionally use different patterns
    pattern = random.choice([
        f"{adj} {seed_short} {harmony}",
        f"{seed_short} {harmony}",
        f"{adj} {harmony}",
        f"{seed_short} {adj} Mix"
    ])

    return pattern


def color_to_dict(color: Color) -> Dict:
    """Convert Color object to dictionary."""
    return {
        'name': color.name,
        'code': color.code,
        'hex': color.hex
    }


def generate_palettes_for_seed(
    seed: Color,
    colors: List[Color],
    palette_sizes: List[int]
) -> List[Dict]:
    """Generate all palettes for a seed color."""
    themes = []

    generators = [
        ('analogous', generate_analogous),
        ('complementary', generate_complementary),
        ('split_complementary', generate_split_complementary),
        ('triadic', generate_triadic),
        ('monochromatic', generate_monochromatic),
        ('warm_cool', generate_warm_cool_mix),
        ('tetradic', generate_tetradic)
    ]

    for size in palette_sizes:
        # Select appropriate generators for this size
        # Generate 3 palettes per size to ensure variety
        # Reordered to ensure monochromatic gets included
        if size == 3:
            size_generators = [
                ('monochromatic', generate_monochromatic),
                ('analogous', generate_analogous),
                ('complementary', generate_complementary),
                ('triadic', generate_triadic),
                ('split_complementary', generate_split_complementary)
            ]
        elif size == 4:
            size_generators = [
                ('monochromatic', generate_monochromatic),
                ('split_complementary', generate_split_complementary),
                ('analogous', generate_analogous),
                ('tetradic', generate_tetradic),
                ('warm_cool', generate_warm_cool_mix)
            ]
        elif size == 5:
            size_generators = [
                ('monochromatic', generate_monochromatic),
                ('triadic', generate_triadic),
                ('warm_cool', generate_warm_cool_mix),
                ('split_complementary', generate_split_complementary),
                ('analogous', generate_analogous)
            ]
        else:  # size == 6
            size_generators = [
                ('tetradic', generate_tetradic),
                ('warm_cool', generate_warm_cool_mix),
                ('triadic', generate_triadic),
                ('analogous', generate_analogous),
                ('split_complementary', generate_split_complementary)
            ]

        # Generate 3 palettes of this size for more variety
        palettes_created = 0
        for harmony_type, generator in size_generators:
            if palettes_created >= 3:
                break

            palette = generator(seed, size, colors)
            if palette and len(palette) >= size:
                theme = {
                    'seed_color': seed.name,
                    'seed_code': seed.code,
                    'seed_hex': seed.hex,
                    'palette_size': size,
                    'colors': [color_to_dict(c) for c in palette[:size]],
                    'theme_name': generate_theme_name(seed, harmony_type, palette[:size]),
                    'harmony_type': harmony_type
                }
                themes.append(theme)
                palettes_created += 1

    return themes


def main():
    """Main function to generate themed palettes."""
    # Paths
    input_path = Path('/Users/wiens/dev/swatchy/static/data/ColorData.json')
    output_path = Path('/Users/wiens/dev/swatchy/generated_themes_new.json')

    print(f"Loading colors from {input_path}...")
    colors = load_colors(str(input_path))
    print(f"Loaded {len(colors)} colors")

    # Filter out very low saturation colors as seeds
    seed_colors = [c for c in colors if c.saturation > 0.1 and c.value > 0.15]
    print(f"Using {len(seed_colors)} colors as seeds")

    all_themes = []
    palette_sizes = [3, 4, 5, 6]

    print("Generating palettes...")
    for i, seed in enumerate(seed_colors):
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(seed_colors)} seeds...")

        themes = generate_palettes_for_seed(seed, colors, palette_sizes)
        all_themes.extend(themes)

    print(f"\nGenerated {len(all_themes)} themes")

    # Count by size
    size_counts = {}
    for theme in all_themes:
        size = theme['palette_size']
        size_counts[size] = size_counts.get(size, 0) + 1

    print("Themes by size:")
    for size in sorted(size_counts.keys()):
        print(f"  Size {size}: {size_counts[size]} themes")

    # Count by harmony type
    harmony_counts = {}
    for theme in all_themes:
        harmony = theme.get('harmony_type', 'unknown')
        harmony_counts[harmony] = harmony_counts.get(harmony, 0) + 1

    print("\nThemes by harmony type:")
    for harmony in sorted(harmony_counts.keys()):
        print(f"  {harmony}: {harmony_counts[harmony]} themes")

    # Save output
    output = {'themes': all_themes}
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved to {output_path}")


if __name__ == '__main__':
    main()
