import glob
from PIL import Image, ImageDraw, ImageFont
import os
import re

def create_timelapse():
    """
    Creates a highly compressed timelapse GIF from images in the 'photos' directory (including subfolders), overlaying the timestamp from the filename.
    """
    photos_dir = 'photos'
    output_dir = '_site'
    output_gif = os.path.join(output_dir, 'timelapse.gif')
    max_width = 640
    colors = 256
    duration = 200  # ms per frame

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Find all image files in all subfolders and sort them by name
    image_files = sorted(glob.glob(f'{photos_dir}/**/*.jpg', recursive=True))

    # Only include files matching the expected filename pattern
    pattern = re.compile(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.jpg$')
    image_files = [f for f in image_files if pattern.search(os.path.basename(f))]

    if not image_files:
        print("No images found to create a timelapse.")
        return

    print(f"Found {len(image_files)} images. Creating highly compressed GIF with timestamps...")

    images = []
    for f in image_files:
        img = Image.open(f).convert('RGB')
        # Resize to max_width, preserving aspect ratio
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        draw = ImageDraw.Draw(img)
        # Extract timestamp from filename (e.g., 2025-06-16_17-10-05.jpg)
        base = os.path.basename(f)
        timestamp = base.replace('.jpg', '').replace('_', ' ')
        # Use a default font
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        # Draw text with outline for visibility
        text_pos = (10, img.height - 32)
        outline_color = 'black'
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                draw.text((text_pos[0]+dx, text_pos[1]+dy), timestamp, font=font, fill=outline_color)
        draw.text(text_pos, timestamp, font=font, fill='white')
        # Convert to palette for GIF compression, no dithering
        img = img.convert('P', palette=Image.ADAPTIVE, colors=colors, dither=Image.NONE)
        images.append(img)

    if images:
        images[0].save(
            output_gif,
            save_all=True,
            append_images=images[1:],
            duration=duration,  # Milliseconds between frames
            loop=0,        # Loop forever
            optimize=True  # Optimize/compress GIF
        )
        print(f"Highly compressed timelapse with timestamps saved to {output_gif}")

if __name__ == "__main__":
    create_timelapse()
