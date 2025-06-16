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
response = requests.get(api_url, headers=headers)

if response.status_code == 200:
    try:
        feed_data = response.json()
        if not feed_data:
            print("Feed is empty.")
        else:
            latest_item = feed_data[0]
            image_url = latest_item.get("image")
            time_str = latest_item.get("time")

            if image_url and time_str:
                # Parse the timestamp and format it for the filename
                dt_object = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                filename = dt_object.strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
                filepath = os.path.join("photos", filename)

                # Check if the file already exists
                if os.path.exists(filepath):
                    print(f"Image {filename} already exists. Skipping download.")
                    set_output("skipped_image_path", filepath)
                else:
                    # Download the image
                    print(f"Downloading image from: {image_url}")
                    image_response = requests.get(image_url, headers=headers)

                    # Save the image
                    if image_response.status_code == 200:
                        with open(filepath, "wb") as f:
                            f.write(image_response.content)
                        print(f"Image saved to {filepath}")
                        set_output("new_image_path", filepath)
                    else:
                        print(f"Failed to download image. Status code: {image_response.status_code}")
                        set_output("status", "error")
            else:
                print("Could not find image URL or time in the response.")
                set_output("status", "error")
    except json.JSONDecodeError:
        print("Failed to decode JSON from the response.")
        set_output("status", "error")
else:
    print(f"Failed to fetch feed content. Status code: {response.status_code}")
    set_output("status", "error")
