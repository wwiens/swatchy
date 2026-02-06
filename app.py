from flask import Flask, render_template, send_from_directory, jsonify, request
import os
import urllib.request
import json
import urllib.parse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/color-wheel')
def color_wheel():
    return render_template('color-wheel.html')

@app.route('/palette-generator')
def palette_generator():
    return render_template('palette-generator.html')

@app.route('/theme-library')
def theme_library():
    return render_template('theme-library.html')

@app.route('/image-picker')
def image_picker():
    return render_template('image-picker.html')

@app.route('/color-picker')
def color_picker():
    return render_template('color-picker.html')

@app.route('/generated_themes.json')
def generated_themes():
    return send_from_directory('.', 'generated_themes.json')

@app.route('/api/save-theme', methods=['POST'])
def save_theme():
    """Save a new theme to the generated_themes.json file."""
    try:
        new_theme = request.get_json()
        if not new_theme:
            return jsonify({"success": False, "error": "No theme data provided"}), 400

        # Read existing themes
        themes_path = os.path.join(os.path.dirname(__file__), 'generated_themes.json')
        with open(themes_path, 'r') as f:
            data = json.load(f)

        # Ensure themes list exists
        if 'themes' not in data:
            data['themes'] = []

        # Add new theme to the beginning of the list
        data['themes'].insert(0, new_theme)

        # Write back to file
        with open(themes_path, 'w') as f:
            json.dump(data, f, indent=2)

        return jsonify({"success": True, "message": "Theme saved successfully"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/generate-theme-name', methods=['POST'])
def generate_theme_name():
    """Generate a creative theme name using OpenAI based on the colors."""
    try:
        data = request.get_json()
        if not data or 'colors' not in data:
            return jsonify({"success": False, "error": "No color data provided"}), 400

        colors = data['colors']
        if not colors:
            return jsonify({"success": False, "error": "Empty color list"}), 400

        # Get API key from environment
        api_key = os.environ.get('OPENAI_API_KEY')

        if not api_key:
            # Fallback: generate a name using simple logic
            color_names = [c.get('name', '').split()[0] for c in colors[:2]]
            fallback_name = f"{' '.join(color_names)} Blend" if len(color_names) > 1 else f"{color_names[0]} Dream" if color_names else "Custom Palette"
            return jsonify({
                "success": True,
                "name": fallback_name,
                "note": "Using fallback name generation (no OPENAI_API_KEY set)"
            })

        # Call OpenAI API
        hex_list = [c.get('hex', '') for c in colors if c.get('hex')]

        # Build palette with ordering info (light to dark)
        hex_with_info = []
        for i, hex_code in enumerate(hex_list):
            position = "lightest" if i == 0 else "darkest" if i == len(hex_list) - 1 else f"color {i+1}"
            hex_with_info.append(f"{hex_code} ({position})")
        hex_formatted = '\n'.join(hex_with_info)

        prompt = f"""Generate a single evocative theme name for this color palette.

Palette (ordered, light → dark):
{hex_formatted}

Constraints:
- Abstract but grounded, not cute, not generic
- 1–3 words max
- Draw from geography, atmosphere, material, or time-of-day metaphors
- Avoid obvious color words (pink, beige, rose, blue, green, etc.)
- No overused words: Whisper, Dream, Harmony, Symphony, Serenity, Essence
- Suitable for a professional design system

Analyze the HEX codes precisely — they encode hue, saturation, and luminance. Use this data to infer warmth vs neutrality, softness vs density, and atmospheric coherence.

Respond with ONLY the theme name, nothing else."""

        req = urllib.request.Request(
            'https://api.openai.com/v1/chat/completions',
            data=json.dumps({
                'model': 'gpt-4o',
                'messages': [
                    {'role': 'system', 'content': 'You are a creative naming expert for art color palettes. You excel at evocative, unique names that capture the essence of color combinations. Never use generic words like Whisper, Dream, Harmony, Symphony, Serenity, Essence. Be specific and surprising.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 50,
                'temperature': 1.2,
                'presence_penalty': 0.6,
                'frequency_penalty': 0.6
            }).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))

        generated_name = result['choices'][0]['message']['content'].strip().strip('"')

        return jsonify({
            "success": True,
            "name": generated_name
        })

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return jsonify({
            "success": False,
            "error": f"AI service error: {error_body}"
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/images/<path:filename>')
def images(filename):
    return send_from_directory('images', filename)

@app.route('/api/search-product')
def search_product():
    """Search for Ohuhu products by color code."""
    code = request.args.get('code', '').strip()

    if not code:
        return jsonify({
            "found": False,
            "count": 0,
            "products": [],
            "error": "No code provided"
        })

    try:
        # Make request to Ohuhu Shopify search API
        url = f"https://ohuhu.com/search/suggest.json?q={code}"

        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        products = []

        # Filter products for exact matches
        if 'resources' in data and 'results' in data['resources']:
            results = data['resources']['results']

            if 'products' in results:
                for product in results['products']:
                    title = product.get('title', '')
                    handle = product.get('handle', '')

                    # Check if code appears in title or handle (exact match)
                    code_in_title = code.upper() in title.upper()
                    code_in_handle = code.lower() in handle.lower()

                    if code_in_title or code_in_handle:
                        # Extract price from product or variants
                        price = "0.00"

                        if 'price' in product:
                            price = str(product['price'])
                        elif 'variants' in product and product['variants']:
                            variant = product['variants'][0]
                            if 'price' in variant:
                                price = str(variant['price'])
                            elif 'compare_at_price' in variant:
                                price = str(variant['compare_at_price'])

                        products.append({
                            "title": title,
                            "price": price,
                            "image": product.get('image', ''),
                            "url": f"https://ohuhu.com/products/{handle}"
                        })

        return jsonify({
            "found": len(products) > 0,
            "count": len(products),
            "products": products
        })

    except urllib.error.HTTPError as e:
        return jsonify({
            "found": False,
            "count": 0,
            "products": [],
            "error": f"HTTP error: {e.code}"
        })
    except urllib.error.URLError as e:
        return jsonify({
            "found": False,
            "count": 0,
            "products": [],
            "error": "Network error"
        })
    except Exception as e:
        return jsonify({
            "found": False,
            "count": 0,
            "products": [],
            "error": "Unable to load product information"
        })

if __name__ == '__main__':
    app.run(debug=True, port=5001)
