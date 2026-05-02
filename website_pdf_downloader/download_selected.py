#!/usr/bin/env python3
"""Download PDFs only from selected pages"""

import json
import os
import requests
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import re
import logging

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Selected pages to download
SELECTED_PAGES = [
    "Pg_Curricula_2",
    "Download_Application_Forms_Nmc",
    "National_Faculty_Development_Programme",
    "Ug_Curriculum",
    "Activities_In_Ugmeb",
    "Under_Graduate",
    "Honble_Supreme_Court_Mandated_Oversight_Committee_On_Mci",
    "Post_Graduate",
    "Online_Research_Methods_Course",
    "E_Compendium_Of_Nmc_2024",
    "Rules_Regulations_Nmc",
    "For_Students_To_Study_In_Abroad",
    "Imr",
    "E_Compendium_Of_Nmc_2020_2023",
    "Annual_Disclosure_Report",
    "Indian_Medical_Register",
    "List_Of_College_Teaching_Pg_Courses",
    "E_Gazette",
    "College_Assessment_Reports",
    "Online_Application_Submit",
    "National_Faculty_Development_Programme_New",
    "Circulars_And_Public_Notices_Nmc",
    "Procedure_To_Start_New_College",
]

def sanitize_filename(name):
    """Remove invalid characters from filename"""
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name)
    return name[:200]

def download_pdf(pdf_info, output_dir, session):
    """Download a single PDF"""
    try:
        url = pdf_info['url']
        page = sanitize_filename(pdf_info['page'])
        heading = sanitize_filename(pdf_info['heading'])
        name = sanitize_filename(pdf_info['name'])
        
        # Create directory structure
        save_dir = output_dir / page / heading
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename
        filename = f"{name}.pdf"
        filepath = save_dir / filename
        
        # Skip if already exists
        if filepath.exists():
            return f"SKIP: {filename} (already exists)"
        
        # Download
        response = session.get(url, timeout=60, verify=False)
        response.raise_for_status()
        
        # Check if it's actually a PDF
        content_type = response.headers.get('content-type', '')
        if 'pdf' not in content_type.lower() and not response.content[:4] == b'%PDF':
            return f"SKIP: {filename} (not a PDF)"
        
        # Save file
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return f"OK: {filename}"
    
    except Exception as e:
        return f"ERROR: {pdf_info.get('name', 'unknown')} - {str(e)[:50]}"

def main():
    # Load index
    script_dir = Path(__file__).parent
    with open(script_dir / 'NMC_PDFs/pdf_index.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Collect PDFs from selected pages only
    pdfs_to_download = []
    for page_name, headings in data['pages'].items():
        if page_name in SELECTED_PAGES:
            for heading, pdfs in headings.items():
                for pdf in pdfs:
                    pdf['page'] = page_name
                    pdf['heading'] = heading
                    pdfs_to_download.append(pdf)
    
    # Remove duplicates by URL
    seen_urls = set()
    unique_pdfs = []
    for pdf in pdfs_to_download:
        if pdf['url'] not in seen_urls:
            seen_urls.add(pdf['url'])
            unique_pdfs.append(pdf)
    
    print(f"\n{'='*60}")
    print(f"Selected Pages PDF Downloader")
    print(f"{'='*60}")
    print(f"Pages selected: {len(SELECTED_PAGES)}")
    print(f"Total PDFs to download: {len(unique_pdfs)} (unique)")
    print(f"{'='*60}\n")
    
    # Create output directory
    output_dir = script_dir / 'NMC_PDFs/downloads'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # Download with thread pool
    success = 0
    failed = 0
    skipped = 0
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(download_pdf, pdf, output_dir, session): pdf for pdf in unique_pdfs}
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result.startswith("OK"):
                success += 1
                logger.info(f"[{i}/{len(unique_pdfs)}] {result}")
            elif result.startswith("SKIP"):
                skipped += 1
                logger.debug(f"[{i}/{len(unique_pdfs)}] {result}")
            else:
                failed += 1
                logger.warning(f"[{i}/{len(unique_pdfs)}] {result}")
    
    print(f"\n{'='*60}")
    print(f"Download Complete!")
    print(f"{'='*60}")
    print(f"Success: {success}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print(f"Output: {output_dir.absolute()}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
