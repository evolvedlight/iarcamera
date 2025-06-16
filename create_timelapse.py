import glob
from PIL import Image
import os

def create_timelapse():
    """
    Creates a timelapse GIF from images in the 'photos' directory.
    """
    photos_dir = 'photos'
    output_dir = '_site'
    output_gif = os.path.join(output_dir, 'timelapse.gif')
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Find all image files and sort them by name
    image_files = sorted(glob.glob(f'{photos_dir}/*.jpg'))

    if not image_files:
        print("No images found to create a timelapse.")
        return

    print(f"Found {len(image_files)} images. Creating GIF...")

    # Open images
    images = [Image.open(f) for f in image_files]

    # Create the GIF
    if images:
        images[0].save(
            output_gif,
            save_all=True,
            append_images=images[1:],
            duration=500,  # Milliseconds between frames
            loop=0         # Loop forever
        )
        print(f"Timelapse saved to {output_gif}")

if __name__ == "__main__":
    create_timelapse()
