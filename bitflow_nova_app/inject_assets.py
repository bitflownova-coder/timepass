
import os

def inject_assets():
    base_dir = r"d:\Bitflow\finance_app"
    kotlin_file_path = os.path.join(base_dir, r"app\src\main\java\com\bitflow\finance\ui\screens\invoice\InvoiceHtmlTemplate.kt")
    logo_b64_path = os.path.join(base_dir, "logo_b64.txt")
    qr_b64_path = os.path.join(base_dir, "qr_b64.txt")

    # Read Base64 strings
    with open(logo_b64_path, "r") as f:
        logo_b64 = f.read().strip()
    
    with open(qr_b64_path, "r") as f:
        qr_b64 = f.read().strip()

    # Read Kotlin file
    with open(kotlin_file_path, "r", encoding="utf-8") as f:
        kotlin_code = f.read()

    # Define replacements
    
    # Logo Replacement
    logo_target = """            <svg width="250" height="64" viewBox="0 0 250 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="64" height="64" rx="12" fill="#3B82F6"/>
                <path d="M32 16L48 48H16L32 16Z" fill="white"/>
                <text x="80" y="42" fill="white" font-family="Inter, sans-serif" font-weight="bold" font-size="32">Bitflow Nova</text>
            </svg>"""
    
    logo_replacement = f"""            <img src="data:image/png;base64,{logo_b64}" alt="Bitflow Nova" style="height: 64px; width: auto;" />"""

    # QR Replacement
    qr_target = """                    <!-- Placeholder for QR Code -->
                    <div class="w-48 h-48 bg-gray-200 flex items-center justify-center text-gray-500 text-xs">QR Code</div>"""
    
    qr_replacement = f"""                    <img src="data:image/jpeg;base64,{qr_b64}" alt="Scan to Pay" class="w-48 h-48" />"""

    # Perform replacements
    new_kotlin_code = kotlin_code.replace(logo_target, logo_replacement)
    new_kotlin_code = new_kotlin_code.replace(qr_target, qr_replacement)

    # Verify replacements happened
    if logo_target not in kotlin_code:
        print("Warning: Logo target not found in file.")
    else:
        print("Logo target found.")

    if qr_target not in kotlin_code:
        print("Warning: QR target not found in file.")
    else:
        print("QR target found.")

    if new_kotlin_code == kotlin_code:
        print("No changes made to the file.")
    else:
        # Write back
        with open(kotlin_file_path, "w", encoding="utf-8") as f:
            f.write(new_kotlin_code)
        print("Successfully injected assets into InvoiceHtmlTemplate.kt")

if __name__ == "__main__":
    inject_assets()
