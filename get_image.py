import requests
import os
import json
import base64
from datetime import datetime

def set_output(name, value):
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"{name}={value}\n")

def get_github_status(github_token, github_repository, branch, github_api_url):
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "iarcamera-updater"
    }
    url = f"{github_api_url}/repos/{github_repository}/contents/status.json?ref={branch}"
    try:
        print(f"Fetching status.json from GitHub: {url}")
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            content_b64 = data.get("content", "")
            content = base64.b64decode(content_b64).decode("utf-8")
            return json.loads(content)
        elif response.status_code == 404:
            print("status.json not found in repository (404).")
            return None
        else:
            print(f"Failed to fetch status.json. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching status.json from GitHub: {e}")
        return None

def get_local_status():
    if os.path.exists("status.json"):
        try:
            with open("status.json", "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading local status.json: {e}")
    return None

def commit_files_to_github(github_token, github_repository, branch, github_api_url, files_to_commit, commit_message):
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "iarcamera-updater"
    }
    
    # 1. Get the current commit SHA of the branch
    ref_url = f"{github_api_url}/repos/{github_repository}/git/ref/heads/{branch}"
    print(f"Getting current ref SHA: {ref_url}")
    ref_res = requests.get(ref_url, headers=headers)
    ref_res.raise_for_status()
    parent_sha = ref_res.json()["object"]["sha"]
    
    # 2. Get the tree SHA of that commit
    commit_url = f"{github_api_url}/repos/{github_repository}/git/commits/{parent_sha}"
    print(f"Getting base tree SHA for commit: {parent_sha}")
    commit_res = requests.get(commit_url, headers=headers)
    commit_res.raise_for_status()
    base_tree_sha = commit_res.json()["tree"]["sha"]
    
    # 3. Create blobs for each file
    tree_items = []
    for path, content_bytes in files_to_commit.items():
        blob_url = f"{github_api_url}/repos/{github_repository}/git/blobs"
        print(f"Creating blob for: {path}")
        blob_data = {
            "content": base64.b64encode(content_bytes).decode("utf-8"),
            "encoding": "base64"
        }
        blob_res = requests.post(blob_url, json=blob_data, headers=headers)
        blob_res.raise_for_status()
        blob_sha = blob_res.json()["sha"]
        
        tree_items.append({
            "path": path,
            "mode": "100644",
            "type": "blob",
            "sha": blob_sha
        })
    
    # 4. Create new tree
    tree_url = f"{github_api_url}/repos/{github_repository}/git/trees"
    print("Creating new tree...")
    tree_data = {
        "base_tree": base_tree_sha,
        "tree": tree_items
    }
    tree_res = requests.post(tree_url, json=tree_data, headers=headers)
    tree_res.raise_for_status()
    new_tree_sha = tree_res.json()["sha"]
    
    # 5. Create commit
    create_commit_url = f"{github_api_url}/repos/{github_repository}/git/commits"
    print("Creating commit...")
    commit_data = {
        "message": commit_message,
        "tree": new_tree_sha,
        "parents": [parent_sha]
    }
    commit_res = requests.post(create_commit_url, json=commit_data, headers=headers)
    commit_res.raise_for_status()
    new_commit_sha = commit_res.json()["sha"]
    
    # 6. Update reference
    update_ref_url = f"{github_api_url}/repos/{github_repository}/git/refs/heads/{branch}"
    print(f"Updating ref to new commit SHA: {new_commit_sha}")
    update_ref_data = {
        "sha": new_commit_sha,
        "force": False
    }
    update_ref_res = requests.patch(update_ref_url, json=update_ref_data, headers=headers)
    update_ref_res.raise_for_status()
    print("Successfully committed files directly to GitHub!")

def main():
    api_url = "https://api.yellow.camera/feed/content/YU20VJ7WP"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    github_token = os.environ.get("GITHUB_TOKEN")
    github_repository = os.environ.get("GITHUB_REPOSITORY")
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    github_api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")

    is_github = bool(github_token and github_repository)

    if is_github:
        print("Running in GitHub Action environment. Using GitHub API for checks.")
        status = get_github_status(github_token, github_repository, branch, github_api_url)
    else:
        print("Running in local environment. Using local files for checks.")
        status = get_local_status()

    # Get the feed content
    print(f"Fetching feed content from: {api_url}")
    try:
        response = requests.get(api_url, headers=headers)
    except Exception as e:
        print(f"Failed to fetch feed content: {e}")
        set_output("status", "error")
        return

    if response.status_code != 200:
        print(f"Failed to fetch feed content. Status code: {response.status_code}")
        set_output("status", "error")
        return

    try:
        feed_data = response.json()
    except json.JSONDecodeError:
        print("Failed to decode JSON from the response.")
        set_output("status", "error")
        return

    if not feed_data:
        print("Feed is empty.")
        set_output("status", "error")
        return

    latest_item = feed_data[0]
    image_url = latest_item.get("image")
    time_str = latest_item.get("time")

    if not image_url or not time_str:
        print("Could not find image URL or time in the response.")
        set_output("status", "error")
        return

    # Check if this image has already been downloaded
    last_image_time = status.get("last_image_time") if status else None
    if last_image_time == time_str:
        print(f"Image from {time_str} already processed. Skipping download.")
        set_output("status", "skipped")
        if status:
            set_output("latest_image_path", "latest.jpg")
            set_output("skipped_image_path", status.get("last_image_path", ""))
        return

    # Parse the timestamp and format it for the filename and folder
    dt_object = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
    date_str = dt_object.strftime("%Y-%m-%d")
    filename = dt_object.strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
    folder_path = os.path.join("photos", date_str)
    filepath = os.path.join(folder_path, filename)
    github_filepath = filepath.replace("\\", "/")

    # Download the image
    print(f"Downloading image from: {image_url}")
    try:
        image_response = requests.get(image_url, headers=headers)
    except Exception as e:
        print(f"Failed to download image: {e}")
        set_output("status", "error")
        return

    if image_response.status_code != 200:
        print(f"Failed to download image. Status code: {image_response.status_code}")
        set_output("status", "error")
        return

    image_bytes = image_response.content

    # Construct status content
    new_status = {
        "last_image_time": time_str,
        "last_image_path": github_filepath
    }
    status_bytes = json.dumps(new_status, indent=2).encode("utf-8")

    if is_github:
        try:
            files_to_commit = {
                github_filepath: image_bytes,
                "latest.jpg": image_bytes,
                "status.json": status_bytes
            }
            commit_message = f"Update latest image: {filename}"
            commit_files_to_github(
                github_token=github_token,
                github_repository=github_repository,
                branch=branch,
                github_api_url=github_api_url,
                files_to_commit=files_to_commit,
                commit_message=commit_message
            )
            set_output("new_image_path", filepath)
            set_output("latest_image_path", "latest.jpg")
            set_output("status", "success")
        except Exception as e:
            print(f"Failed to commit changes to GitHub: {e}")
            set_output("status", "error")
    else:
        # Save files locally
        os.makedirs(folder_path, exist_ok=True)
        
        # Check if the file already exists locally
        if os.path.exists(filepath):
            print(f"Image {filename} already exists locally. Skipping local write.")
        else:
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            print(f"Image saved to {filepath}")
        
        # Update latest.jpg
        with open("latest.jpg", "wb") as f:
            f.write(image_bytes)
        print("Latest image copy saved to latest.jpg")
        
        # Save local status.json
        with open("status.json", "w") as f:
            json.dump(new_status, f, indent=2)
        print("Status saved locally to status.json")

        set_output("new_image_path", filepath)
        set_output("latest_image_path", "latest.jpg")
        set_output("status", "success")

if __name__ == "__main__":
    main()
