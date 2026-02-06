from flask import Flask, render_template, send_from_directory, jsonify, request
import os
import urllib.request
import json

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
