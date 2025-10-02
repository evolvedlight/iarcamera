import glob
from PIL import Image, ImageDraw, ImageFont
import os
import re
import cv2
import numpy as np

def create_timelapse_video(days_filter=None, weekdays_only=True):
    """
    Creates a high-quality web-compatible MP4 timelapse video from images in the 'photos' directory (including subfolders), overlaying the timestamp from the filename.
    
    Args:
        days_filter (int, optional): If specified, only include images from the last N days. If None, include all images.
        weekdays_only (bool): If True, only include weekday images (Mon-Fri). If False, include all days.
    """
    photos_dir = 'photos'
    output_dir = '_site'
    
    # Determine output filename based on filter
    if days_filter:
        output_video = os.path.join(output_dir, f'timelapse_last{days_filter}days.webm')
    else:
        output_video = os.path.join(output_dir, 'timelapse.webm')
        
    max_width = 960   # Reduced resolution for smaller file size
    fps = 10         # Increase frame rate for smoother video
    bitrate = '5000k'  # Target bitrate for higher quality

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Find all image files in all subfolders and sort them by name
    image_files = sorted(glob.glob(f'{photos_dir}/**/*.jpg', recursive=True))

    # Only include files matching the expected filename pattern
    import datetime
    pattern = re.compile(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.jpg$')
    
    # Calculate cutoff date if days_filter is specified
    cutoff_date = None
    if days_filter:
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days_filter)).date()
    
    filtered_files = []
    for f in image_files:
        if not pattern.search(os.path.basename(f)):
            continue
        # Get parent folder name (date)
        folder = os.path.basename(os.path.dirname(f))
        try:
            date_obj = datetime.datetime.strptime(folder, "%Y-%m-%d")
            
            # Apply days filter if specified
            if cutoff_date and date_obj.date() < cutoff_date:
                continue
                
            # Apply weekdays filter if enabled
            if weekdays_only and date_obj.weekday() >= 5:  # 0=Mon, ..., 5=Sat, 6=Sun
                continue
                
            filtered_files.append(f)
        except Exception:
            # If folder name is not a date, skip
            continue
    image_files = filtered_files

    if not image_files:
        filter_desc = ""
        if days_filter:
            filter_desc += f"from the last {days_filter} days "
        if weekdays_only:
            filter_desc += "(weekdays only) "
        print(f"No images found {filter_desc}to create a timelapse video.")
        return

    filter_desc = ""
    if days_filter:
        filter_desc += f"from the last {days_filter} days "
    if weekdays_only:
        filter_desc += "(weekdays only) "
    print(f"Found {len(image_files)} images {filter_desc}. Creating high-quality MP4 timelapse video with timestamps...")

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
    fourcc = cv2.VideoWriter_fourcc(*'VP80')  # VP8 codec for WebM
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    for frame in frames:
        out.write(frame)
    out.release()
    print(f"Timelapse video saved to {output_video}")

    # Optionally, re-encode with ffmpeg for even higher quality and web compatibility
    try:
        import subprocess
        temp_video_name = f'timelapse_last{days_filter}days_temp.webm' if days_filter else 'timelapse_temp.webm'
        temp_video = os.path.join(output_dir, temp_video_name)
        os.rename(output_video, temp_video)
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-i', temp_video,
            '-c:v', 'libvpx-vp9', '-crf', '35', '-b:v', '0',
            '-row-mt', '1', '-threads', '4',
            output_video
        ]
        print('Running ffmpeg for final encoding to WebM...')
        subprocess.run(ffmpeg_cmd, check=True)
        os.remove(temp_video)
        filter_desc = ""
        if days_filter:
            filter_desc += f"(last {days_filter} days) "
        if weekdays_only:
            filter_desc += "(weekdays only) "
        print(f"Final optimized WebM timelapse video {filter_desc}saved to {output_video}")
    except Exception as e:
        print(f"ffmpeg not available or failed: {e}")
        # If ffmpeg fails, rename the temp file back to the final name
        temp_video_name = f'timelapse_last{days_filter}days_temp.webm' if days_filter else 'timelapse_temp.webm'
        temp_video = os.path.join(output_dir, temp_video_name)
        if os.path.exists(temp_video):
            os.rename(temp_video, output_video)
            filter_desc = ""
            if days_filter:
                filter_desc += f"(last {days_filter} days) "
            if weekdays_only:
                filter_desc += "(weekdays only) "
            print(f"Basic timelapse video {filter_desc}saved to {output_video}")

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    days_filter = None
    weekdays_only = True
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "last3days":
            days_filter = 3
            weekdays_only = False
        elif sys.argv[1].startswith("last") and sys.argv[1].endswith("days"):
            try:
                days_filter = int(sys.argv[1][4:-4])  # Extract number from "lastXdays"
                weekdays_only = False
            except ValueError:
                print(f"Invalid argument: {sys.argv[1]}. Use 'last3days' or 'lastXdays' where X is a number.")
                sys.exit(1)
        else:
            print(f"Usage: {sys.argv[0]} [last3days|lastXdays]")
            print("  No arguments: Create timelapse from all weekday images")
            print("  last3days: Create timelapse from last 3 days (including weekends)")
            print("  lastXdays: Create timelapse from last X days (including weekends)")
            sys.exit(1)
    
    create_timelapse_video(days_filter, weekdays_only)
