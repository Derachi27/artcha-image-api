import cv2
import os
from PIL import Image

# Directories
framed_folder = "./framed_images"
background_folder = "./room_backgrounds"
output_folder = "./staged_images"

# Create output folder if not exist
os.makedirs(output_folder, exist_ok=True)

# Get list of framed images and background images
framed_images = [img for img in os.listdir(framed_folder) if img.endswith(('.png', '.jpg'))]
backgrounds = [bg for bg in os.listdir(background_folder) if bg.endswith(('.png', '.jpg'))]

# Overlay each framed image on each background
for framed_img in framed_images:
    framed_path = os.path.join(framed_folder, framed_img)
    framed = cv2.imread(framed_path)

    # Resize framed image for consistency
    framed_resized = cv2.resize(framed, (600, 800))

    # Overlay on each background
    for bg_img in backgrounds:
        bg_path = os.path.join(background_folder, bg_img)
        background = cv2.imread(bg_path)

        # Ensure backgrounds are large enough
        bg_height, bg_width = background.shape[:2]
        if bg_height < 800 or bg_width < 600:
            print(f"Skipping {bg_img} - too small for overlay.")
            continue

        # Calculate top-left position for placing the framed image
        x_offset = (bg_width - 600) // 2
        y_offset = (bg_height - 800) // 2

        # Place the framed image onto the background
        background[y_offset:y_offset+800, x_offset:x_offset+600] = framed_resized

        # Save the result
        output_path = os.path.join(output_folder, f"{os.path.splitext(framed_img)[0]}_on_{bg_img}")
        cv2.imwrite(output_path, background)

        print(f"🖼️ Created: {output_path}")

print("🎉 All framed artworks have been placed in room settings!")
