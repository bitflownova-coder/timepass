
import base64
import os

file_path = r"d:\Bitflow_softwares\timepass\logofinal (1).png"
output_path = r"d:\Bitflow_softwares\timepass\logo_base64.txt"

if os.path.exists(file_path):
    with open(file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        with open(output_path, "w") as text_file:
            text_file.write(encoded_string)
    print(f"Successfully converted {file_path} to base64 and saved to {output_path}")
else:
    print(f"File not found: {file_path}")
