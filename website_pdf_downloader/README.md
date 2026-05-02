# NMC Website PDF Downloader

Download all PDFs from the National Medical Commission website (https://www.nmc.org.in/) organized by page and heading.

## Requirements

Install the required packages:

```bash
pip install requests beautifulsoup4
```

## Usage

### Basic Usage (Download all PDFs)

```bash
python nmc_pdf_downloader.py
```

This will:
1. Crawl up to 150 pages on the NMC website
2. Find all PDF links
3. Download them to `NMC_PDFs/` folder organized by page and heading

### Custom Options

```bash
# Specify output directory
python nmc_pdf_downloader.py --output "My_NMC_Downloads"

# Crawl more pages (for thorough coverage)
python nmc_pdf_downloader.py --max-pages 300

# Scan only (create index without downloading)
python nmc_pdf_downloader.py --scan-only
```

## Output Structure

```
NMC_PDFs/
├── Home/
│   ├── General/
│   │   ├── document1.pdf
│   │   └── document2.pdf
│   └── What_s_New/
│       ├── UG_Apply_Extension.pdf
│       └── seat_matrix.pdf
├── Rules_Regulations/
│   ├── Graduate_Medical_Education/
│   │   └── GMER_1997.pdf
│   └── Prevention_Of_Ragging/
│       └── Ragging_Regulation_2009.pdf
├── About_Nmc/
│   └── Introduction/
│       └── nmc_overview.pdf
├── pdf_index.json         # Complete index in JSON format
├── pdf_summary.txt        # Human-readable summary
└── download_log.txt       # Download log
```

## Features

- **Page-wise organization**: PDFs are grouped by the page they were found on
- **Heading-wise subfolders**: Within each page, PDFs are grouped by section headings
- **Duplicate handling**: Skips already downloaded PDFs
- **Resume capability**: Re-run to download any missed files
- **Error logging**: Failed downloads are logged for retry
- **Polite crawling**: Includes delays to avoid overloading the server

## Files Generated

1. **pdf_index.json** - Complete structured index of all PDFs found
2. **pdf_summary.txt** - Human-readable summary of all PDFs
3. **download_log.txt** - Detailed log of the download process
4. **failed_downloads.json** - List of any PDFs that failed to download

## Tips

1. **First run with scan-only**: Use `--scan-only` first to see what will be downloaded
2. **Check the summary**: Review `pdf_summary.txt` before downloading
3. **Large website**: The NMC website has 100+ PDFs, download may take 10-20 minutes
4. **Stable internet**: Ensure stable connection for large downloads
