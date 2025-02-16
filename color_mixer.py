import matplotlib
matplotlib.use('Agg')  # Use the 'Agg' backend which is non-GUI
import re
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from flask import Flask, render_template, request, send_file
from io import BytesIO
from base64 import b64encode



app = Flask(__name__)


def combine_hex_colors(hex1, hex2, weight1, weight2):
    """
    Combines two hex colors with given weights, applying gamma correction.

    Args:
        hex1: The first hex color string (e.g., "#FF0000" or "FF0000").
        hex2: The second hex color string.
        weight1: The weight of the first color.
        weight2: The weight of the second color.

    Returns:
        The combined hex color string.  Returns None if input is invalid.
    """

    def hex_to_rgb(hex_color):
        """Converts a hex color string to an RGB tuple."""
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        if not re.match(r'^[0-9a-fA-F]{6}$', hex_color):  # Validate hex format
            print(f"Invalid hex code: {hex_color}")
            return None  # Return None for invalid hex

        try:
            bigint = int(hex_color, 16)
            return (bigint >> 16) & 255, (bigint >> 8) & 255, bigint & 255
        except ValueError:
            print(f"Invalid hex code: {hex_color}")
            return None

    def rgb_to_hex(r, g, b):
        """Converts an RGB tuple to a hex color string."""
        return "#{:02X}{:02X}{:02X}".format(r, g, b)

    rgb1 = hex_to_rgb(hex1)
    rgb2 = hex_to_rgb(hex2)
    if rgb1 is None or rgb2 is None:
        return None  # Return None if hex conversion failed

    total_weight = weight1 + weight2
    if total_weight == 0:  # Prevent division by zero
        return None

    # Normalize weights.
    w1 = weight1 / total_weight
    w2 = weight2 / total_weight
    gamma = 1.8
    combined_r = round(((rgb1[0] ** gamma) * w1 + (rgb2[0] ** gamma) * w2) ** (1 / gamma))
    combined_g = round(((rgb1[1] ** gamma) * w1 + (rgb2[1] ** gamma) * w2) ** (1 / gamma))
    combined_b = round(((rgb1[2] ** gamma) * w1 + (rgb2[2] ** gamma) * w2) ** (1 / gamma))

    return rgb_to_hex(combined_r, combined_g, combined_b)


def visualize_color(hex_color, title="Color"):
    """Visualizes a single hex color using matplotlib and returns image as bytes."""
    if hex_color is None:  # Handle potential None return from combine_hex_colors
        print("Cannot visualize an invalid color.")
        return None

    fig, ax = plt.subplots()
    ax.add_patch(patches.Rectangle((0, 0), 1, 1, color=hex_color))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(f"{title}: {hex_color}")
    ax.axis('off')  # Hide axes

    img_buf = BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)
    plt.close(fig)
    return img_buf


@app.route('/', methods=['GET', 'POST'])
def index():
    mixed_color_hex = None
    image_data = None
    error_message = None

    if request.method == 'POST':
        color1_hex = request.form['color1']
        color2_hex = request.form['color2']
        weight1_str = request.form['weight1']
        weight2_str = request.form['weight2']

        if weight1_str not in ('1', '2') or weight2_str not in ('1', '2'):
            error_message = "Weights must be either 1 or 2."
            return render_template('index.html', error=error_message, mixed_color=None, color_image=None)  # Clear previous results

        weight1 = int(weight1_str)
        weight2 = int(weight2_str)


        # Add '#' if it's not there and validate format
        if not color1_hex.startswith("#") and len(color1_hex) == 6:
            color1_hex = "#" + color1_hex
        if not color2_hex.startswith("#") and len(color2_hex) == 6:
            color2_hex = "#" + color2_hex

        if not re.match(r'^#[0-9a-fA-F]{6}$', color1_hex):
            error_message = "Invalid hex code format for Color 1."
        elif not re.match(r'^#[0-9a-fA-F]{6}$', color2_hex):
            error_message = "Invalid hex code format for Color 2."
        else:
            mixed_color_hex = combine_hex_colors(color1_hex, color2_hex, weight1, weight2)
            if mixed_color_hex:
                image_buf = visualize_color(mixed_color_hex, "Mixed Color")
                if image_buf:
                    image_data = "data:image/png;base64," + b64encode(image_buf.read()).decode('utf-8')
                else:
                    error_message = "Visualization failed."
            else:
                error_message = "Color mixing failed due to invalid input."

    return render_template('index.html', mixed_color=mixed_color_hex, color_image=image_data, error=error_message)


@app.route('/image')
def image():
    hex_color = request.args.get('hex_color')
    if hex_color:
        image_buf = visualize_color(hex_color, "Color")
        if image_buf:
            return send_file(image_buf, mimetype='image/png')
    return "Error generating image", 400

