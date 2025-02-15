from fastapi import FastAPI, Query, HTTPException
import os
import json
import requests
import subprocess
import glob
import sys
from zipfile import ZipFile
import cv2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Configuration
json_file = "Art_images.json"
download_folder = "./midjourney_images"
framed_folder = "./framed_images"
downloaded_log = "./downloaded_images.log"
zip_output = "./framed_images.zip"

# Securely load Discord credentials from .env file
discord_exporter_path = "./DiscordChatExporter.CLI"
discord_token = os.getenv("DISCORD_TOKEN")
channel_id = os.getenv("DISCORD_CHANNEL_ID")

# Ensure folders exist
os.makedirs(download_folder, exist_ok=True)
os.makedirs(framed_folder, exist_ok=True)

# ✅ Ensure log file exists
if not os.path.exists(downloaded_log):
    with open(downloaded_log, "w") as f:
        f.write("")  # Create an empty file if it doesn't exist

@app.get("/")
def home():
    return {"message": "Artcha Automation API is running"}

# ✅ Function to load downloaded images from the log file
def load_downloaded_images():
    """ Load the list of already downloaded images from log file """
    if os.path.exists(downloaded_log):
        with open(downloaded_log, "r") as f:
            return set(f.read().splitlines())  # Read file names line by line
    return set()

# ✅ Function to convert HEX to BGR for OpenCV
def hex_to_bgr(hex_color):
    """ Convert HEX color to BGR format for OpenCV """
    hex_color = hex_color.lstrip("#")
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return (rgb[2], rgb[1], rgb[0])  # Convert RGB to BGR (OpenCV format)

@app.get("/run")
def run_automation(frame_color: str = Query(default="000000"), frame_size: int = Query(default=30), force_download: bool = Query(default=False)):
    """ Runs the full automation: Downloads images, applies frames, and zips the output """

    if not discord_token or not channel_id:
        raise HTTPException(status_code=500, detail="Missing Discord credentials. Ensure DISCORD_TOKEN and DISCORD_CHANNEL_ID are set.")

    downloaded_images = load_downloaded_images()
    new_images = 0  # Counter for new images

    # Step 1: Run DiscordChatExporter
    export_command = [
        discord_exporter_path, "export",
        "-t", discord_token,
        "-c", channel_id,
        "-f", "Json"
    ]
    subprocess.run(export_command)

    # Step 2: Rename the JSON file automatically
    json_files = glob.glob("*art_channel*.json")
    if json_files:
        old_json_file = json_files[0]
        os.rename(old_json_file, json_file)
        print(f"✅ Found JSON: {old_json_file} → Renamed to {json_file}")
    else:
        return {"error": "JSON file not found after export. Make sure DiscordChatExporter is saving the file in the correct location."}

    # Step 3: Load and download new images
    try:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as e:
        return {"error": f"Failed to read JSON file: {e}"}

    image_downloaded = False  # Track if new images are downloaded
    for message in data.get("messages", []):
        for attachment in message.get("attachments", []):
            url = attachment.get("url", "")
            filename = attachment.get("fileName", "")

            if not url or filename in downloaded_images:
                print(f"⏭️ Skipping (Already Downloaded): {filename}")
                continue  # Skip already downloaded images

            file_path = os.path.join(download_folder, filename)
            try:
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    with open(file_path, "wb") as img_file:
                        for chunk in response.iter_content(1024):
                            img_file.write(chunk)
                    downloaded_images.add(filename)  # Add to set
                    new_images += 1
                    image_downloaded = True
                    print(f"✅ Downloaded: {filename}")

                    # ✅ **Immediately save new downloads to log**
                    with open(downloaded_log, "a") as log_file:
                        log_file.write(filename + "\n")

                else:
                    print(f"⚠️ Failed to download {url}: HTTP {response.status_code}")
            except Exception as e:
                print(f"⚠️ Error downloading {url}: {e}")

    # Step 4: Apply frames to new images
    framed_images = 0
    border_color = hex_to_bgr(frame_color)

    if new_images > 0:
        for filename in os.listdir(download_folder):
            if filename.endswith((".png", ".jpg", ".jpeg")):
                input_path = os.path.join(download_folder, filename)
                output_path = os.path.join(framed_folder, filename)

                try:
                    img = cv2.imread(input_path)
                    if img is None:
                        print(f"⚠️ Skipping {filename}: Unable to read image.")
                        continue

                    print(f"🖼️ Applying Frame: Size={frame_size}, Color={border_color}")

                    img_with_border = cv2.copyMakeBorder(
                        img, frame_size, frame_size, frame_size, frame_size,
                        cv2.BORDER_CONSTANT, value=border_color
                    )
                    cv2.imwrite(output_path, img_with_border)
                    framed_images += 1
                    print(f"✅ Framed Image: {output_path}")
                except Exception as e:
                    print(f"⚠️ Error framing {filename}: {e}")

        print(f"✅ Total Framed Images: {framed_images}")

    # Step 5: Create a ZIP file for download
    if framed_images > 0:
        with ZipFile(zip_output, 'w') as zipf:
            for root, _, files in os.walk(framed_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, framed_folder))
                    print(f"📦 Added to ZIP: {file_path}")

        print(f"✅ ZIP file created: {zip_output}")
    else:
        print("⚠️ No images were framed, skipping ZIP creation.")

    return {
        "message": f"Processed {new_images} new images, framed {framed_images}. Download the ZIP file from /download"
    }

@app.get("/download")
def download_zip():
    """ Allows the user to download the ZIP file of framed images """
    if os.path.exists(zip_output):
        return {"download_url": zip_output}
    return {"error": "No ZIP file found"}
