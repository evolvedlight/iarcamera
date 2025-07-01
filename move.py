import os
import re
import shutil

# Directory containing your images
SOURCE_DIR = './photos'

# Regex to match filenames like 2025-06-17_13-00-05.jpg
pattern = re.compile(r'(\d{4}-\d{2}-\d{2})_\d{2}-\d{2}-\d{2}\.jpg$')

for filename in os.listdir(SOURCE_DIR):
    match = pattern.match(filename)
    if match:
        date_str = match.group(1)
        dest_dir = os.path.join(SOURCE_DIR, date_str)
        os.makedirs(dest_dir, exist_ok=True)
        src_path = os.path.join(SOURCE_DIR, filename)
        dest_path = os.path.join(dest_dir, filename)
        shutil.move(src_path, dest_path)
        print(f"Moved {filename} to {dest_dir}/")