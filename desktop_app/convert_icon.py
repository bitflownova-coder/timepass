from PIL import Image

img = Image.open("logo.jpeg")
img.save("logo.ico", format='ICO', sizes=[(256, 256)])
print("Converted logo.jpeg to logo.ico")
