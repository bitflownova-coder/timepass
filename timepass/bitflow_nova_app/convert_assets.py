import base64
import os

def convert_to_base64(file_path, output_path):
    with open(file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        with open(output_path, "w") as text_file:
            text_file.write(encoded_string)

convert_to_base64("d:/Bitflow/finance_app/invoice_generator/assets/logo.png", "d:/Bitflow/finance_app/logo_b64.txt")
convert_to_base64("d:/Bitflow/finance_app/invoice_generator/assets/qr_code.jpg", "d:/Bitflow/finance_app/qr_b64.txt")
