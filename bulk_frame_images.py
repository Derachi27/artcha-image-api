import os
import subprocess

# Paths
input_folder = "./midjourney_images"
output_folder = "./framed_imagess"

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Apply frames to each image
for filename in os.listdir(input_folder):
    if filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        # Apply a black frame using ImageMagick
        command = [
            "magick", input_path,
            "-bordercolor", "black",
            "-border", "30x30",  # Adjust frame size as needed
            output_path
        ]

        subprocess.run(command)
        print(f"🖼️ Framed: {filename}")

print("✅ All images have been framed!")
