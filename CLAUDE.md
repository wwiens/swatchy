# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is "Swatchy" - a Flask-based web application providing a suite of color tools for Ohuhu marker artists. It includes an interactive color wheel, palette generator, theme library, image color picker, and standalone color browser.

## Project Structure

```
/Users/wiens/dev/swatchy/
├── app.py                    # Flask application entry point
├── requirements.txt          # Python dependencies (flask)
├── static/
│   ├── css/                  # Custom styles (if needed)
│   ├── js/                   # JavaScript modules (if needed)
│   └── data/
│       └── colors.json       # Ohuhu marker color database
├── templates/
│   ├── base.html             # Base layout with Tailwind CDN, navigation
│   ├── index.html            # Main landing page with tool grid
│   ├── color-wheel.html      # Interactive color wheel with harmony modes
│   ├── palette-generator.html # Random palette generator with locking
│   ├── theme-library.html    # Pre-defined palette themes
│   ├── image-picker.html     # Extract colors from uploaded images
│   └── color-picker.html     # Standalone color picker/browser
└── images/swatches/          # PNG color swatch images
```

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, Tailwind CSS (via CDN), Vanilla JavaScript
- **Data**: JSON file with 100 Ohuhu marker colors

## Development

To run the application:

```bash
pip install -r requirements.txt
python app.py
```

Then visit `http://localhost:5000`

## Data Format

`static/data/colors.json` entries follow this structure:
```json
{
  "Color Name": {
    "Honolulu": "BG4",    // Old code for Honolulu line (may be empty)
    "Oahu": "",           // Old code for Oahu line (may be empty)
    "Kaala": "",          // Old code for Kaala line (may be empty)
    "New": "B02",         // New unified color code
    "URL": "...",         // CDN URL for swatch image
    "Image": "...",       // Local path to swatch image
    "Hex": "#bee5e8"      // Hex color value
  }
}
```

## Architecture Notes

**Color Wheel (`/color-wheel`)**:
- Uses HSV color space for positioning markers on the wheel (hue = angle, saturation = distance from center)
- Harmony calculations use hue angle offsets (e.g., complementary = 180° offset)
- Markers are rendered as SVG circles positioned via `hsvToWheelPosition()`
- The wheel background is a CSS conic-gradient with a radial gradient overlay for the white center

**Palette Generator (`/palette-generator`)**:
- Supports locking colors to preserve them during regeneration
- Uses brightness calculation to determine text color (black/white) for contrast
- Color picker modal allows manual color selection from the full marker set

**Theme Library (`/theme-library`)**:
- Pre-defined themes with curated color combinations
- Categories: warm, cool, nature, vibrant, pastel
- Each theme shows color swatches and closest marker matches

**Image Picker (`/image-picker`)**:
- Extracts dominant colors from uploaded images
- Uses canvas pixel sampling and color quantization
- Finds closest Ohuhu marker matches using RGB distance

**Color Picker (`/color-picker`)**:
- Grid view of all available colors
- Search by name or code
- Filter by product line (Honolulu/Oahu/Kaala)
- Sort by name, code, or hue

**Shared Utilities** (in base.html):
- `hexToHSV()` - Converts hex to HSV color space
- `calculateBrightness()` - Uses YIQ formula for perceptual brightness
- `loadColorData()` - Fetches color data and initializes markers array

## Routes

| Route | Template | Description |
|-------|----------|-------------|
| `/` | index.html | Main landing page with tool grid |
| `/color-wheel` | color-wheel.html | Interactive color wheel |
| `/palette-generator` | palette-generator.html | Random palette generator |
| `/theme-library` | theme-library.html | Pre-defined palette themes |
| `/image-picker` | image-picker.html | Extract colors from images |
| `/color-picker` | color-picker.html | Standalone color picker |

## Adding New Colors

To add new marker colors:
1. Add entries to `static/data/colors.json` following the existing format
2. Add corresponding swatch images to `images/swatches/`
3. Restart the Flask server

## Design System

- **Primary accent**: Vibrant purple/coral gradient
- **Background**: Light gradient with multiple pastel hues
- **Cards**: White with subtle shadows and hover lift effects
- **Typography**: Inter font family via Google Fonts
- **Responsive**: Mobile-first with breakpoints at md (768px) and lg (1024px)
