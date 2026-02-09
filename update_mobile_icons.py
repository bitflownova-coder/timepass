import os
from PIL import Image, ImageDraw, ImageOps

logo_path = "Bitflownova.Final.Logo.jpeg"
res_path = "bitflow_nova_app/app/src/main/res"

sizes = {
    "mipmap-mdpi": (48, 48),
    "mipmap-hdpi": (72, 72),
    "mipmap-xhdpi": (96, 96),
    "mipmap-xxhdpi": (144, 144),
    "mipmap-xxxhdpi": (192, 192)
}

def make_round(img):
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + img.size, fill=255)
    output = ImageOps.fit(img, img.size, centering=(0.5, 0.5))
    output.putalpha(mask)
    return output

if not os.path.exists(logo_path):
    print(f"Error: {logo_path} not found")
    exit(1)

img = Image.open(logo_path)

# Ensure drawable folder exists
os.makedirs(f"{res_path}/drawable", exist_ok=True)
img.save(f"{res_path}/drawable/logo.jpg")

for folder, size in sizes.items():
    folder_path = f"{res_path}/{folder}"
    os.makedirs(folder_path, exist_ok=True)
    
    # Square Icon
    resized = img.resize(size, Image.Resampling.LANCZOS)
    resized.save(f"{folder_path}/ic_launcher.png")
    
    # Round Icon
    rounded = make_round(resized)
    rounded.save(f"{folder_path}/ic_launcher_round.png")
    
    print(f"Updated {folder}")

print("Mobile icons updated successfully!")
