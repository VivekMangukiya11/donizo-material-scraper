#!/usr/bin/env python3
"""
Subprocess Scraper Runner
Runs Castorama and ManoMano scrapers as separate processes
"""

import subprocess
import sys
import time
from datetime import datetime

def main():
    """Run both scrapers as separate processes."""
    print("=" * 60)
    print("🎯 STARTING PARALLEL SCRAPING SESSION")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    start_time = time.time()
    
    # Start Castorama scraper
    print("🚀 Starting Castorama scraper...")
    castorama_process = subprocess.Popen([
        sys.executable, "scrapers/castorama_scraper.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Start ManoMano scraper
    print("🚀 Starting ManoMano scraper...")
    manomano_process = subprocess.Popen([
        sys.executable, "scrapers/manomano_scraper.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Start Leroy Merlin scraper
    print("🚀 Starting Leroy Merlin scraper...")
    leroymerlin_process = subprocess.Popen([
        sys.executable, "scrapers/leroymerlin_scraper.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for all processes to complete
    castorama_stdout, castorama_stderr = castorama_process.communicate()
    manomano_stdout, manomano_stderr = manomano_process.communicate()
    leroymerlin_stdout, leroymerlin_stderr = leroymerlin_process.communicate()
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Print results
    print("\n" + "=" * 60)
    print("📊 SCRAPING RESULTS")
    print("=" * 60)
    
    if castorama_process.returncode == 0:
        print("✅ Castorama scraper completed successfully")
    else:
        print(f"❌ Castorama scraper failed with return code: {castorama_process.returncode}")
        if castorama_stderr:
            print(f"Error: {castorama_stderr}")
    
    if manomano_process.returncode == 0:
        print("✅ ManoMano scraper completed successfully")
    else:
        print(f"❌ ManoMano scraper failed with return code: {manomano_process.returncode}")
        if manomano_stderr:
            print(f"Error: {manomano_stderr}")
    
    if leroymerlin_process.returncode == 0:
        print("✅ Leroy Merlin scraper completed successfully")
    else:
        print(f"❌ Leroy Merlin scraper failed with return code: {leroymerlin_process.returncode}")
        if leroymerlin_stderr:
            print(f"Error: {leroymerlin_stderr}")
    
    print("=" * 60)
    print("✅ PARALLEL SCRAPING SESSION COMPLETED")
    print(f"⏱️  Total Duration: {duration:.2f} seconds")
    print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
