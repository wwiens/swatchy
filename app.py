from flask import Flask, render_template, send_from_directory
import os

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

if __name__ == '__main__':
    app.run(debug=True, port=5001)
