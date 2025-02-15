import json
import requests
import os
import subprocess
import re

# Configuration
json_file = "Art_images.json"
download_folder = "./midjourney_images"
framed_folder = "./framed_images"
downloaded_log = "./downloaded_images.log"
discord_exporter_path = "./DiscordChatExporter.CLI"  # Adjust if needed
discord_token = "MTI0ODE2ODk1NjQwNjAwOTg2Mg.GjxWzl.X4sKqTbVLM1OVSfl3RHxEMOUb9dmbjHQqIBE2M"  # Replace with your actual token
channel_id = "1303033879506059347"

# Step 1: Run DiscordChatExporter to get the latest JSON
print("🚀 Running DiscordChatExporter...")
export_command = [
    discord_exporter_path, "export",
    "-t", discord_token,
    "-c", channel_id,
    "-f", "Json"
]
subprocess.run(export_command)
print("✅ JSON file updated.")

# Step 2: Rename the JSON file automatically
json_found = False
for file in os.listdir("."):
    if re.match(r".*art_channel.*\.json", file):
        os.rename(file, json_file)
        json_found = True

if not json_found:
    print("❌ JSON file not found after export. Check DiscordChatExporter.")
    exit(1)

# Step 3: Download New Images
os.makedirs(download_folder, exist_ok=True)
os.makedirs(framed_folder, exist_ok=True)

# Load already downloaded images
if os.path.exists(downloaded_log):
    with open(downloaded_log, "r") as f:
        downloaded_images = set(f.read().splitlines())
else:
    downloaded_images = set()

# Load the JSON file
new_images = 0
with open(json_file, "r", encoding="utf-8") as file:
    data = json.load(file)

for message in data.get("messages", []):
    for attachment in message.get("attachments", []):
        url = attachment.get("url", "")
        filename = attachment.get("fileName", "")

        # Download only if not already downloaded
        if filename in downloaded_images:
            continue

        if url.endswith((".png", ".jpg", ".jpeg", ".webp")):
            file_path = os.path.join(download_folder, filename)
            try:
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    with open(file_path, "wb") as img_file:
                        for chunk in response.iter_content(1024):
                            img_file.write(chunk)
                    downloaded_images.add(filename)
                    new_images += 1
                else:
                    print(f"❌ Failed to download {url}")

            except Exception as e:
                print(f"⚠️ Error downloading {url}: {e}")

# Update the log file
with open(downloaded_log, "w") as f:
    for img in downloaded_images:
        f.write(img + "\n")

print(f"🎯 {new_images} new images downloaded.")

# Step 4: Frame Images Only If New Ones Were Found
if new_images > 0:
    print("🖼️ Framing new images...")
    for filename in os.listdir(download_folder):
        if filename.endswith((".png", ".jpg", ".jpeg")):
            input_path = os.path.join(download_folder, filename)
            output_path = os.path.join(framed_folder, filename)

            # Apply black frame
            os.system(f'magick "{input_path}" -bordercolor black -border 30x30 "{output_path}"')

    print("✅ Image processing complete!")
else:
    print("🚫 No new images to process. Skipping framing.")

print("🎉 Automation workflow completed successfully!")
