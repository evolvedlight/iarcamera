# IAR Camera Timelapse System

An automated camera timelapse system that downloads images from a Yellow Camera API feed, organizes them by date, and creates timelapse videos that are automatically deployed to GitHub Pages.

## What This System Does

This repository implements an automated workflow that:

1. **Fetches Images**: Automatically downloads the latest images from a Yellow Camera API feed every 10 minutes
2. **Organizes Images**: Saves images in a date-organized directory structure (`photos/YYYY-MM-DD/`)
3. **Creates Timelapses**: Generates both GIF and MP4 timelapse videos with timestamp overlays
4. **Deploys Videos**: Automatically publishes timelapse videos to GitHub Pages for public viewing

## File Structure

```
iarcamera/
├── get_image.py              # Downloads latest image from camera API
├── create_timelapse.py       # Creates compressed GIF timelapse
├── create_timelapse_video.py # Creates high-quality MP4 timelapse
├── move.py                   # Utility to organize existing images by date
├── photos/                   # Directory containing all camera images
│   └── YYYY-MM-DD/          # Date-organized subdirectories
│       └── YYYY-MM-DD_HH-MM-SS.jpg  # Timestamped image files
├── _site/                    # Generated timelapse outputs
│   ├── timelapse.gif        # Compressed GIF timelapse
│   ├── timelapse.mp4        # High-quality MP4 timelapse
│   └── index.html           # Web page for viewing video
└── .github/workflows/        # GitHub Actions automation
    ├── main.yml             # Image fetching workflow
    └── timelapse.yml        # Timelapse creation and deployment
```

## Components

### Image Fetching (`get_image.py`)

- **Purpose**: Downloads the latest image from the Yellow Camera API
- **API Endpoint**: `https://api.yellow.camera/feed/content/YU20VJ7WP`
- **Features**:
  - Fetches the most recent image from the camera feed
  - Parses timestamp information from API response
  - Saves images with structured naming: `YYYY-MM-DD_HH-MM-SS.jpg`
  - Organizes images into date-based folders
  - Skips downloading if image already exists
  - Provides output for GitHub Actions integration

### Timelapse Creation

#### GIF Timelapse (`create_timelapse.py`)
- **Purpose**: Creates a highly compressed GIF timelapse
- **Features**:
  - Processes all images in the `photos` directory
  - Resizes images to 640px width for compression
  - Overlays timestamps from filenames onto each frame
  - Uses palette optimization for smaller file sizes
  - Outputs to `_site/timelapse.gif`

#### MP4 Timelapse (`create_timelapse_video.py`)
- **Purpose**: Creates a high-quality MP4 timelapse video
- **Features**:
  - Higher resolution (1280px width) for better quality
  - 10 FPS for smooth playback
  - Timestamp overlays with enhanced visibility
  - OpenCV-based video creation
  - Optional ffmpeg re-encoding for web compatibility
  - Outputs to `_site/timelapse.mp4`

### Utility Scripts

#### Image Organization (`move.py`)
- **Purpose**: Organizes existing images into date-based subdirectories
- **Usage**: Run once to restructure photos that aren't already organized
- **Function**: Moves images from `photos/` root into `photos/YYYY-MM-DD/` folders

## Automation Workflows

### Image Fetching Workflow (`main.yml`)
- **Trigger**: Runs every 10 minutes (except first 2 minutes of each hour)
- **Actions**:
  1. Fetches the latest image from the camera API
  2. Saves it to the appropriate date folder
  3. Commits and pushes new images to the repository

### Timelapse Workflow (`timelapse.yml`)
- **Trigger**: Runs daily at midnight (00:00 UTC)
- **Actions**:
  1. Creates a high-quality MP4 timelapse video
  2. Generates a simple HTML page for viewing
  3. Deploys the video to GitHub Pages

## Setup and Configuration

### Prerequisites
- GitHub repository with Actions enabled
- GitHub Pages enabled for the repository
- Python 3.x environment

### Dependencies
- `requests` - For API calls and image downloading
- `Pillow` - For image processing and GIF creation
- `opencv-python` - For MP4 video creation
- `numpy` - For image array manipulation
- `ffmpeg` - For high-quality video encoding (optional)

### Installation
1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install requests Pillow opencv-python numpy
   ```
3. For video creation, install ffmpeg:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   
   # macOS
   brew install ffmpeg
   ```

### Camera Configuration
The system is currently configured for a specific Yellow Camera feed:
- **API URL**: `https://api.yellow.camera/feed/content/YU20VJ7WP`

To use with a different camera:
1. Update the `api_url` variable in `get_image.py`
2. Adjust the JSON parsing logic if the API response format differs

## Usage

### Manual Operation
```bash
# Download latest image
python get_image.py

# Create GIF timelapse
python create_timelapse.py

# Create MP4 timelapse
python create_timelapse_video.py

# Organize existing images
python move.py
```

### Automated Operation
The system runs automatically via GitHub Actions:
- Images are fetched every 10 minutes
- Timelapse videos are created daily
- Videos are deployed to GitHub Pages

## Output

### Image Files
- **Location**: `photos/YYYY-MM-DD/`
- **Format**: `YYYY-MM-DD_HH-MM-SS.jpg`
- **Organization**: Automatically organized by date

### Timelapse Files
- **GIF**: `_site/timelapse.gif` - Compressed, web-friendly
- **MP4**: `_site/timelapse.mp4` - High-quality, web-compatible
- **Web Page**: `_site/index.html` - Simple HTML page for viewing

### GitHub Pages
The timelapse video is automatically deployed to GitHub Pages at:
`https://[username].github.io/iarcamera/`

## Customization

### Image Processing
- **Resolution**: Modify `max_width` in timelapse scripts
- **Frame Rate**: Adjust `fps` in `create_timelapse_video.py`
- **Compression**: Change `colors` and `duration` in `create_timelapse.py`

### Timestamp Overlay
- **Font**: Modify font loading in both timelapse scripts
- **Position**: Adjust `text_pos` coordinates
- **Style**: Change colors and outline effects

### Scheduling
- **Fetch Frequency**: Modify the cron schedule in `main.yml`
- **Timelapse Generation**: Adjust the schedule in `timelapse.yml`

## Troubleshooting

### Common Issues
1. **Missing Images**: Check API endpoint and network connectivity
2. **Video Creation Fails**: Ensure OpenCV and ffmpeg are installed
3. **GitHub Pages Not Updating**: Verify Pages settings and deployment permissions

### Debugging
- Check GitHub Actions logs for detailed error messages
- Test scripts locally with Python to isolate issues
- Verify API response format if changing camera feeds

## License

This project is open source. Please check the repository settings for specific license information.