import argparse
import sys
from crawler import Crawler

def main():
    parser = argparse.ArgumentParser(description="Website Crawler Tool")
    parser.add_argument("url", help="The starting URL to crawl")
    parser.add_argument("--output", "-o", default="output", help="Output directory")
    parser.add_argument("--depth", "-d", type=int, default=1, help="Max recursion depth (default: 1)")

    args = parser.parse_args()

    # Normalize output path
    output_dir = args.output
    if not os.path.isabs(output_dir):
        output_dir = os.path.abspath(output_dir)

    print(f"Output Directory: {output_dir}")
    
    crawler = Crawler(args.url, output_dir, args.depth)
    crawler.run()

if __name__ == "__main__":
    import os
    main()
