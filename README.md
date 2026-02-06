# Swatchy

A Flask-based web application providing a suite of color tools for Ohuhu marker artists. Find the perfect colors, generate harmonious palettes, and extract colors from reference images.

## Features

Swatchy includes five interactive tools to help artists work with Ohuhu marker colors:

### 1. Color Wheel
Interactive color wheel with harmony modes. Visualize color relationships and find complementary, triadic, and analogous color combinations. Markers are positioned using HSV color space (hue = angle, saturation = distance from center).

### 2. Palette Generator
Generate random color palettes with the ability to lock colors you like. Includes a color picker modal to manually select from the full marker set. Automatically calculates text contrast (black/white) based on color brightness.

### 3. Theme Library
Browse pre-defined curated themes organized by category: warm, cool, nature, vibrant, and pastel. Each theme shows color swatches with their closest Ohuhu marker matches.

### 4. Image Picker
Upload images and extract dominant colors using canvas pixel sampling and color quantization. Automatically finds the closest Ohuhu marker matches using RGB distance calculations.

### 5. Color Picker
Browse all 100+ marker colors in a searchable, filterable grid. Search by color name or code, filter by product line (Honolulu/Oahu/Kaala), and sort by name, code, or hue.

## Tech Stack

- **Backend**: Flask 3.0+ (Python)
- **Frontend**: HTML, Tailwind CSS (via CDN), Vanilla JavaScript
- **Data**: JSON file with Ohuhu marker color database
- **Images**: 500+ PNG color swatch images

## Installation & Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd swatchy
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and visit:
```
http://localhost:5001
```

## Project Structure

```
swatchy/
├── app.py                    # Flask application entry point
├── requirements.txt          # Python dependencies
├── static/
│   ├── css/                  # Custom styles (if needed)
│   ├── js/                   # JavaScript modules (if needed)
│   └── data/
│       └── colors.json       # Ohuhu marker color database (100+ colors)
├── templates/
│   ├── base.html             # Base layout with Tailwind CDN, navigation
│   ├── index.html            # Main landing page with tool grid
│   ├── color-wheel.html      # Interactive color wheel with harmony modes
│   ├── palette-generator.html # Random palette generator with locking
│   ├── theme-library.html    # Pre-defined palette themes
│   ├── image-picker.html     # Extract colors from uploaded images
│   └── color-picker.html     # Standalone color picker/browser
└── images/swatches/          # 500+ PNG color swatch images
```

## Data Format

Colors are stored in `static/data/colors.json` with the following structure:

```json
{
  "Color Name": {
    "Honolulu": "BG4",      // Old code for Honolulu line (may be empty)
    "Oahu": "",             // Old code for Oahu line (may be empty)
    "Kaala": "",            // Old code for Kaala line (may be empty)
    "New": "B02",           // New unified color code
    "URL": "...",           // CDN URL for swatch image
    "Image": "...",         // Local path to swatch image
    "Hex": "#bee5e8"        // Hex color value
  }
}
```

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

## Development

The application uses several shared utilities defined in `base.html`:

- `hexToHSV()` - Converts hex to HSV color space
- `calculateBrightness()` - Uses YIQ formula for perceptual brightness
- `loadColorData()` - Fetches color data and initializes markers array
- `hsvToWheelPosition()` - Positions markers on the color wheel

## License

[Your License Here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

