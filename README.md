# IAR Camera 📸

[![Build Status](https://github.com/evolvedlight/iarcamera/workflows/Fetch%20Latest%20Image/badge.svg)](https://github.com/evolvedlight/iarcamera/actions/workflows/main.yml)
[![Timelapse Status](https://github.com/evolvedlight/iarcamera/workflows/Create%20and%20Deploy%20Timelapse%20Video/badge.svg)](https://github.com/evolvedlight/iarcamera/actions/workflows/timelapse.yml)
[![GitHub last commit](https://img.shields.io/github/last-commit/evolvedlight/iarcamera)](https://github.com/evolvedlight/iarcamera/commits/main)
[![GitHub repo size](https://img.shields.io/github/repo-size/evolvedlight/iarcamera)](https://github.com/evolvedlight/iarcamera)
[![License](https://img.shields.io/github/license/evolvedlight/iarcamera)](LICENSE)

An automated camera monitoring system that captures and archives images from a live camera feed, creating beautiful timelapse videos and GIFs.

## 🖼️ Latest Image

![Latest Image](https://raw.githubusercontent.com/evolvedlight/iarcamera/main/latest.jpg)

*Image automatically updated every 10 minutes*

## 🎬 Live Timelapse Video

View the latest timelapse video: [**Watch Timelapse**](https://evolvedlight.github.io/iarcamera/)

## ✨ Features

- **Automated Image Capture**: Fetches the latest image from the camera API every 10 minutes
- **Smart Organization**: Images are automatically organized by date in folders
- **Timelapse Creation**: Daily timelapse videos are created and deployed to GitHub Pages
- **GIF Generation**: Compressed timelapse GIFs for easy sharing
- **Duplicate Prevention**: Skips downloading images that already exist
- **High-Quality Output**: Creates web-compatible MP4 videos with timestamp overlays

## 🔧 How It Works

### Image Fetching
The system uses a Python script (`get_image.py`) that:
1. Fetches data from the camera API endpoint
2. Downloads the latest image if it's new
3. Organizes images by date in the `photos/` directory
4. Saves a copy as `latest.jpg` for static linking

### Timelapse Generation
Two types of timelapse media are created:
- **Video**: High-quality MP4 files with timestamp overlays (`create_timelapse_video.py`)
  - Default: All weekday images (Monday-Friday) - created only on weekends
  - `last2days`: Images from the last 2 days (including weekends) - created daily
  - `lastXdays`: Images from the last X days (including weekends)
- **GIF**: Compressed animated GIFs for quick viewing (`create_timelapse.py`)
- **Last 3 Days**: Dedicated script for recent activity (`create_timelapse_last3days.py`)

### Automation
GitHub Actions workflows handle:
- **Image Fetching**: Runs every 10 minutes (configurable cron schedule)
- **Daily Timelapse Creation**: Runs daily at midnight to create 2-day timelapse videos
- **Weekend Timelapse Creation**: Runs on weekends at midnight to create full timelapse videos

## 📁 Repository Structure

```
iarcamera/
├── get_image.py                  # Main image fetching script
├── create_timelapse.py           # GIF timelapse generator
├── create_timelapse_video.py     # Video timelapse generator (with date filtering)
├── create_timelapse_last3days.py # Dedicated 3-day timelapse script
├── move.py                       # Image organization utility
├── photos/                       # Image archive organized by date
│   ├── 2025-06-16/
│   ├── 2025-06-17/
│   └── ...
├── latest.jpg               # Most recent image (static link)
└── .github/workflows/       # GitHub Actions automation
    ├── main.yml            # Image fetching workflow
    └── timelapse.yml       # Timelapse creation workflow
```

## 🚀 Setup and Configuration

### Prerequisites
- Python 3.x
- Required packages: `requests`, `Pillow`, `opencv-python`, `numpy`
- FFmpeg (for video creation)

### Running Locally
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install requests Pillow opencv-python numpy
   ```
3. Run the image fetcher:
   ```bash
   python get_image.py
   ```
4. Create a timelapse:
   ```bash
   python create_timelapse.py        # For GIF
   python create_timelapse_video.py  # For MP4 (all weekdays)
   python create_timelapse_video.py last2days  # For MP4 (last 2 days)
   python create_timelapse_video.py last7days  # For MP4 (last 7 days)
   python create_timelapse_last3days.py        # Dedicated last 3 days script
   ```

### GitHub Actions Configuration
The workflows are configured to run automatically:
- **Image fetching**: Every 10 minutes between 02-59 minutes past the hour
- **Daily timelapse creation**: Daily at midnight (UTC) - creates 2-day timelapse
- **Weekend timelapse creation**: Weekends at midnight (UTC) - creates full timelapse

## 📊 Statistics

- **Update Frequency**: Every 10 minutes
- **Archive Start**: June 16, 2025
- **Total Images**: Growing daily
- **Daily Timelapse Videos**: Updated daily (2-day timelapses)
- **Full Timelapse Videos**: Updated on weekends

## 🛠️ Technical Details

### Image Processing
- Images are downloaded as JPEG files
- Filenames include timestamps for easy sorting
- Duplicate detection prevents redundant downloads
- Images are resized and optimized for timelapse creation

### Video Creation
- Uses FFmpeg for high-quality encoding
- Timestamps are overlaid on each frame
- Output format: MP4 with H.264 codec
- Optimized for web playback

### GIF Creation
- Palette-based compression for smaller file sizes
- Configurable frame duration and color depth
- Optimized for quick loading and sharing

## 🔗 Links

- [Live Timelapse Video](https://evolvedlight.github.io/iarcamera/)
- [GitHub Actions](https://github.com/evolvedlight/iarcamera/actions)
- [Latest Workflow Run](https://github.com/evolvedlight/iarcamera/actions/workflows/main.yml)

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

---

*Automatically updated by GitHub Actions* 🤖