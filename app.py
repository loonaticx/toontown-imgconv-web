from flask import Flask, request, send_file, render_template, jsonify
from PIL import Image
import numpy as np
import io
import base64

from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods = ['POST'])
def upload():
    try:
        rgb_file = request.files['rgb']
        alpha_file = request.files['alpha']
        original_filename = rgb_file.filename
        base_name = original_filename.rsplit('.', 1)[0]

        rgb_image = Image.open(rgb_file).convert('RGB')
        alpha_image = Image.open(alpha_file).convert('L')  # Grayscale for alpha

        if rgb_image.size != alpha_image.size:
            raise ValueError("Images do not match in size")

        rgba_image = rgb_image.copy()
        rgba_image.putalpha(alpha_image)

        output = io.BytesIO()
        rgba_image.save(output, format = 'PNG')
        output.seek(0)

        png_base64 = base64.b64encode(output.getvalue()).decode('utf-8')

        return jsonify({
            "png_data": png_base64,
            "png_filename": f"{base_name}.png"
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route('/process_rgba', methods = ['POST'])
def process_rgba():
    rgba_file = request.files['rgba']
    original_filename = rgba_file.filename
    base_name = original_filename.rsplit('.', 1)[0]

    rgba_image = Image.open(rgba_file).convert('RGBA')

    rgb_image = rgba_image.convert('RGB')
    alpha_channel = rgba_image.split()[-1]

    rgb_output = io.BytesIO()
    rgb_image.save(rgb_output, format = 'JPEG')
    rgb_output.seek(0)

    # the secret is that ".rgb" files are actually SGI images.
    # we will just refer to them as SGI to avoid confusion with the other RGB keyword being thrown around.
    alpha_array = np.array(alpha_channel)
    sgi_output = io.BytesIO()
    Image.fromarray(alpha_array).save(sgi_output, format = 'SGI')
    sgi_output.seek(0)

    # PNG preview of the alpha channel so that it can be visible to the end user
    alpha_preview = io.BytesIO()
    alpha_channel.save(alpha_preview, format = 'PNG')
    alpha_preview.seek(0)

    # Encode binary data to Base64 so that we can send it thru the wire
    rgb_base64 = base64.b64encode(rgb_output.getvalue()).decode('utf-8')
    alpha_preview_base64 = base64.b64encode(alpha_preview.getvalue()).decode('utf-8')
    alpha_sgi_base64 = base64.b64encode(sgi_output.getvalue()).decode('utf-8')

    return jsonify({
        "rgb_jpg": rgb_base64,
        "rgb_jpg_filename": f"{base_name}.jpg",
        "alpha_sgi": alpha_sgi_base64,
        "alpha_preview_png": alpha_preview_base64,
        "alpha_sgi_filename": f"{base_name}_a.rgb"
    })


if __name__ == '__main__':
    app.run(debug = True)
