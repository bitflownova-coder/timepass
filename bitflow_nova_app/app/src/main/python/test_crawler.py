#!/usr/bin/env python3
"""
Test script for crawler_engine.py
Tests performance, output, and what scans are executed
"""

import os
import sys
import time
import json
import tempfile

# Add current dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler_engine import start_crawl, get_status, SECURITY_MODULES_AVAILABLE

def test_crawl(url, scan_mode="quick"):
    """
    Test crawl with timing
    
    scan_mode options:
    - quick: ssl_analysis,security_headers only 
    - full: all scans
    - custom: specify categories
    """
    
    print("="*60)
    print(f"CRAWLER TEST - {url}")
    print("="*60)
    print(f"\nSecurity Modules Available: {SECURITY_MODULES_AVAILABLE}")
    
    # Create temp output dir
    output_dir = tempfile.mkdtemp(prefix="crawler_test_")
    print(f"Output directory: {output_dir}")
    
    # Set scan categories based on mode
    if scan_mode == "quick":
        scan_categories = "ssl_analysis,security_headers"
    elif scan_mode == "full":
        scan_categories = "all"
    else:
        scan_categories = scan_mode  # custom categories
    
    print(f"\nScan Mode: {scan_mode}")
    print(f"Categories: {scan_categories}")
    print("\n" + "-"*60)
    
    # Start timing
    start_time = time.time()
    
    # Start crawl
    print("\n[Starting crawl...]\n")
    crawl_id = start_crawl(
        url=url,
        depth=2,
        output_dir=output_dir,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        scan_categories=scan_categories
    )
    
    print(f"Crawl ID: {crawl_id}")
    print("\n[Waiting for crawl to complete...]\n")
    
    # Poll for completion
    last_status = ""
    while True:
        status_json = get_status(crawl_id)
        status = json.loads(status_json)
        
        current_status = status.get('status', 'unknown')
        pages = status.get('pages_crawled', 0)
        current_url = status.get('current_url', '')[:50]
        
        status_line = f"Status: {current_status} | Pages: {pages} | Current: {current_url}"
        if status_line != last_status:
            print(f"  {status_line}")
            last_status = status_line
        
        if current_status in ('completed', 'error', 'not_found'):
            break
        
        time.sleep(1)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Get final result
    result_json = get_status(crawl_id)
    try:
        result = json.loads(result_json)
    except json.JSONDecodeError as e:
        print(f"ERROR parsing JSON: {e}")
        print(f"Raw result: {result_json[:500]}...")
        return
    
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    
    # Timing
    print(f"\n⏱️  Total Duration: {duration:.2f} seconds ({duration/60:.1f} minutes)")
    
    # Check for errors
    if result.get('error'):
        print(f"\n❌ ERROR: {result['error']}")
        return
    
    # Basic stats
    print(f"\n📊 Basic Stats:")
    print(f"   - Pages Crawled: {result.get('pages_crawled', 'N/A')}")
    print(f"   - Total Pages Found: {result.get('pages_total', 'N/A')}")
    
    # What was scanned
    print(f"\n🔍 Scans Enabled: {result.get('enabled_scans', [])}")
    
    # Check what data we got
    print(f"\n📦 Data Collected:")
    
    # Pre-crawl scans
    pre_crawl_scans = [
        ('dns_recon', 'DNS Analysis'),
        ('ssl_analysis', 'SSL/TLS Analysis'),
        ('hidden_paths', 'Hidden Paths'),
        ('subdomains', 'Subdomains'),
        ('subdomain_takeover', 'Subdomain Takeover'),
        ('robots_analysis', 'Robots.txt Analysis'),
        ('email_security', 'Email Security (DMARC/SPF)'),
        ('waf_detection', 'WAF Detection'),
        ('cors_findings', 'CORS Check'),
        ('http_methods', 'HTTP Methods'),
        ('clickjacking', 'Clickjacking Check'),
        ('security_headers', 'Security Headers'),
        ('error_pages', 'Error Pages'),
        ('cloud_scanner', 'Cloud Buckets'),
        ('api_discovery', 'API Discovery'),
        ('osint_summary', 'OSINT Summary'),
    ]
    
    for key, name in pre_crawl_scans:
        value = result.get(key)
        if value is not None:
            if isinstance(value, list):
                count = len(value)
                status = f"✅ {count} items" if count > 0 else "⚪ Empty"
            elif isinstance(value, dict):
                status = f"✅ Present ({len(value)} keys)"
            else:
                status = f"✅ Present"
        else:
            status = "⛔ Not run"
        print(f"   {name}: {status}")
    
    # Page-level data
    pages = result.get('pages', [])
    if pages:
        print(f"\n📄 Page Analysis ({len(pages)} pages):")
        
        # Sample first page for what was collected
        sample = pages[0] if pages else {}
        page_fields = [
            ('security', 'Security Analysis'),
            ('seo', 'SEO Analysis'),
            ('tech', 'Technology Detection'),
            ('js_analysis', 'JavaScript Analysis'),
            ('forms', 'Form Mapping'),
            ('cookies', 'Cookie Audit'),
            ('osint', 'OSINT'),
            ('versions', 'Version Detection'),
            ('page_vulnerabilities', 'Page Vulnerabilities'),
        ]
        
        for key, name in page_fields:
            if key in sample and sample[key]:
                status = "✅ Collected"
            else:
                status = "⛔ Not collected"
            print(f"   {name}: {status}")
    
    # Vulnerabilities
    vulns = result.get('vulnerabilities', [])
    print(f"\n⚠️  Vulnerabilities Found: {len(vulns)}")
    if vulns:
        for v in vulns[:5]:  # Show first 5
            print(f"   - [{v.get('severity', 'N/A')}] {v.get('issue', v.get('vulnerability', 'Unknown'))}")
        if len(vulns) > 5:
            print(f"   ... and {len(vulns) - 5} more")
    
    # Technologies
    techs = result.get('technologies', [])
    print(f"\n🔧 Technologies Detected: {len(techs)}")
    if techs:
        for t in techs[:5]:
            if isinstance(t, dict):
                print(f"   - {t.get('name', t.get('tech', 'Unknown'))}")
            else:
                print(f"   - {t}")
        if len(techs) > 5:
            print(f"   ... and {len(techs) - 5} more")
    
    # Forms
    forms = result.get('forms', [])
    print(f"\n📝 Forms Found: {len(forms)}")
    
    # Cookies
    cookies = result.get('cookies', [])
    print(f"\n🍪 Cookies Found: {len(cookies)}")
    
    # Secrets
    secrets = result.get('secrets', [])
    print(f"\n🔑 Secrets/Keys Found: {len(secrets)}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    
    # Save full result
    result_file = os.path.join(output_dir, "test_result.json")
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n📁 Full results saved to: {result_file}")
    
    return result


if __name__ == "__main__":
    # Test website - use a simple site for testing
    test_url = "https://example.com"  # Safe test target
    
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    
    scan_mode = "quick"  # Default to quick
    if len(sys.argv) > 2:
        scan_mode = sys.argv[2]
    
    print(f"\nUsage: python test_crawler.py <url> <mode>")
    print(f"  Modes: quick, full, or comma-separated categories")
    print(f"  Example: python test_crawler.py https://example.com quick")
    print(f"  Example: python test_crawler.py https://example.com ssl_analysis,dns_recon")
    print()
    
    test_crawl(test_url, scan_mode)
