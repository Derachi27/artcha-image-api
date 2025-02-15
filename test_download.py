import requests

url = "https://cdn.discordapp.com/attachments/1303033879506059347/1303320170034495559/maducollins_77087_31570_In_a_Vertical_Rectangular_composition_c_1ea9bc9e-1fb8-4151-bbe8-c606f1e88e78.png?ex=67af28ff&is=67add77f&hm=df2a0f4a30e33570086cf35c75b04a39d0a7ec373986b0cfcf474cc782afab72&"
file_name = "test_image.png"

try:
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(file_name, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"✅ Downloaded {file_name}")
    else:
        print(f"❌ Failed to download image: HTTP {response.status_code}")

except Exception as e:
    print(f"⚠️ Error: {e}")
