import glob
from PIL import Image, ImageDraw, ImageFont
import os
import re
import cv2
import numpy as np

def create_timelapse_video():
    """
    Creates a high-quality web-compatible MP4 timelapse video from images in the 'photos' directory (including subfolders), overlaying the timestamp from the filename.
    """
    photos_dir = 'photos'
    output_dir = '_site'
    output_video = os.path.join(output_dir, 'timelapse.mp4')
    max_width = 1280  # Increase resolution for higher quality
    fps = 10         # Increase frame rate for smoother video
    bitrate = '5000k'  # Target bitrate for higher quality

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Find all image files in all subfolders and sort them by name
    image_files = sorted(glob.glob(f'{photos_dir}/**/*.jpg', recursive=True))

    # Only include files matching the expected filename pattern
    pattern = re.compile(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.jpg$')
    image_files = [f for f in image_files if pattern.search(os.path.basename(f))]

    if not image_files:
        print("No images found to create a timelapse video.")
        return

    print(f"Found {len(image_files)} images. Creating high-quality MP4 timelapse video with timestamps...")

    frames = []
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
            font = ImageFont.truetype("arial.ttf", 32)
        except:
            font = ImageFont.load_default()
        # Draw text with outline for visibility
        text_pos = (10, img.height - 40)
        outline_color = 'black'
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                draw.text((text_pos[0]+dx, text_pos[1]+dy), timestamp, font=font, fill=outline_color)
        draw.text(text_pos, timestamp, font=font, fill='white')
        # Convert to numpy array for OpenCV
        frame = np.array(img)
        # Convert RGB to BGR for OpenCV
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frames.append(frame)

    # Get frame size
    height, width, _ = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    for frame in frames:
        out.write(frame)
    out.release()
    print(f"Timelapse video saved to {output_video}")

    # Optionally, re-encode with ffmpeg for even higher quality and web compatibility
    try:
        import subprocess
        temp_video = os.path.join(output_dir, 'timelapse_temp.mp4')
        os.rename(output_video, temp_video)
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-i', temp_video,
            '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-b:v', bitrate,
            '-pix_fmt', 'yuv420p', output_video
        ]
        print('Running ffmpeg for final encoding...')
        subprocess.run(ffmpeg_cmd, check=True)
        os.remove(temp_video)
        print(f"Final high-quality timelapse video saved to {output_video}")
    except Exception as e:
        print(f"ffmpeg not available or failed: {e}")

if __name__ == "__main__":
    create_timelapse_video()
