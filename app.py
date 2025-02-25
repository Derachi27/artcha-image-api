import streamlit as st
import requests
import os
from PIL import Image

# ✅ FastAPI Backend URL (Update to your deployed API URL)
API_URL = "https://artcha-image-api-production.up.railway.app"

st.title("🎨 Artcha Image Processing Automation")
st.write("Automates downloading, framing, and packaging MidJourney images.")

# 🎨 **User Inputs**
frame_color = st.color_picker("Select Frame Color", "#000000")
frame_size = st.slider("Select Frame Size", 10, 100, 30)
force_download = st.checkbox("Force Re-Download All Images")

# ✅ **Progress UI**
progress_bar = st.progress(0)  # Progress bar
status_text = st.empty()  # Status updates (Downloading 1/10, Framing 2/10)
image_preview = st.empty()  # Placeholder for processed image preview

# 🚀 **Run Automation**
if st.button("Run Automation"):
    st.write("🚀 Running automation...")
    progress_bar.progress(0)  # Start Progress at 0%
    image_preview.empty()  # Clear old image preview

    try:
        response = requests.get(
            f"{API_URL}/run?frame_color={frame_color[1:]}&frame_size={frame_size}&force_download={force_download}",
            stream=True
        )

        if response.status_code == 200:
            total_steps = None
            completed_steps = 0

            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8").strip()

                    # ✅ Extract total images to process
                    if decoded_line.startswith("🔄 Processing"):
                        try:
                            total_steps = int(decoded_line.split()[2])  # Extract total image count
                            progress_bar.progress(0)  # Reset Progress Bar
                        except ValueError:
                            total_steps = None

                    # ✅ **Only show "Downloading X/Y" or "Framing X/Y"**
                    if "Downloading" in decoded_line or "Framing" in decoded_line:
                        completed_steps += 1
                        status_text.text(decoded_line)  # Update displayed text

                        if total_steps:
                            progress_value = completed_steps / total_steps
                            progress_bar.progress(progress_value)  # ✅ **Move Progress Bar Smoothly**

            progress_bar.progress(1.0)  # ✅ Ensure bar reaches 100%
            st.success("✅ Automation completed.")

        else:
            st.error(f"❌ API Error: {response.status_code} - {response.text}")

    except Exception as e:
        st.error(f"❌ Error: {e}")

# 📷 **Show Image Preview AFTER Processing**
processed_folder = "./framed_images"
if os.path.exists(processed_folder) and os.listdir(processed_folder):
    st.subheader("📷 Processed Image Preview")
    images = [file for file in os.listdir(processed_folder) if file.endswith((".png", ".jpg", ".jpeg"))]

    if images:
        latest_image = os.path.join(processed_folder, sorted(images)[-1])  # Sort & get latest
        image_preview.image(Image.open(latest_image), caption="Latest Processed Image", use_container_width=True)

# 📦 **Download Processed Images**
if st.button("Download Processed Images"):
    with st.spinner("Zipping images..."):
        response = requests.get(f"{API_URL}/download")
        if response.status_code == 200:
            zip_url = response.json().get("download_url")
            if zip_url and os.path.exists(zip_url):  # Check if ZIP exists
                with open(zip_url, "rb") as file:
                    st.download_button("📥 Download ZIP", file, file_name="framed_images.zip", mime="application/zip")
            else:
                st.error("⚠️ No processed images found. Try running automation first.")
        else:
            st.error(f"❌ API Error: {response.status_code}")
