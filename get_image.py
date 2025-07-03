import requests
import os
import json
from datetime import datetime

def set_output(name, value):
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"{name}={value}\n")

# The URL of the API
api_url = "https://api.yellow.camera/feed/content/YU20VJ7WP"

# The headers to mimic a browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}

# Create the photos directory if it doesn't exist
if not os.path.exists("photos"):
    os.makedirs("photos")

# Get the feed content
print(f"Fetching feed content from: {api_url}")
try:
    response = requests.get(api_url, headers=headers)
except Exception as e:
    print(f"Failed to fetch feed content due to network error: {e}")
    set_output("status", "error")
    exit(1)

if response.status_code == 200:
    try:
        feed_data = response.json()
        if not feed_data:
            print("Feed is empty.")
            set_output("status", "success")
        else:
            latest_item = feed_data[0]
            image_url = latest_item.get("image")
            time_str = latest_item.get("time")

            if image_url and time_str:
                # Parse the timestamp and format it for the filename and folder
                dt_object = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                date_str = dt_object.strftime("%Y-%m-%d")
                filename = dt_object.strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
                folder_path = os.path.join("photos", date_str)
                filepath = os.path.join(folder_path, filename)

                # Create the date folder if it doesn't exist
                os.makedirs(folder_path, exist_ok=True)

                # Check if the file already exists
                if os.path.exists(filepath):
                    print(f"Image {filename} already exists. Skipping download.")
                    
                    # Still update latest.jpg with the existing image
                    latest_filepath = "latest.jpg"
                    if os.path.exists(filepath):
                        with open(filepath, "rb") as src, open(latest_filepath, "wb") as dst:
                            dst.write(src.read())
                        print(f"Latest image copy updated to {latest_filepath}")
                        set_output("latest_image_path", latest_filepath)
                    
                    set_output("skipped_image_path", filepath)
                    set_output("status", "success")
                else:
                    # Download the image
                    print(f"Downloading image from: {image_url}")
                    try:
                        image_response = requests.get(image_url, headers=headers)
                    except Exception as e:
                        print(f"Failed to download image due to network error: {e}")
                        set_output("status", "error")
                        exit(1)

                    # Save the image
                    if image_response.status_code == 200:
                        with open(filepath, "wb") as f:
                            f.write(image_response.content)
                        print(f"Image saved to {filepath}")
                        
                        # Also save a copy as latest.jpg for static linking in README
                        latest_filepath = "latest.jpg"
                        with open(latest_filepath, "wb") as f:
                            f.write(image_response.content)
                        print(f"Latest image copy saved to {latest_filepath}")
                        
                        set_output("new_image_path", filepath)
                        set_output("latest_image_path", latest_filepath)
                        set_output("status", "success")
                    else:
                        print(f"Failed to download image. Status code: {image_response.status_code}")
                        set_output("status", "error")
                        exit(1)
            else:
                print("Could not find image URL or time in the response.")
                set_output("status", "error")
                exit(1)
    except json.JSONDecodeError:
        print("Failed to decode JSON from the response.")
        set_output("status", "error")
        exit(1)
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        set_output("status", "error")
        exit(1)
else:
    print(f"Failed to fetch feed content. Status code: {response.status_code}")
    set_output("status", "error")
    exit(1)
