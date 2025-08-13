#!/usr/bin/env python3
"""
Parallel Scraper Runner
Runs Castorama, ManoMano, and Leroy Merlin scrapers simultaneously
"""

import threading
import time
from datetime import datetime
from scrapers.castorama_scraper import CastoramaScraper
from scrapers.manomano_scraper import ManomanoScraper
from scrapers.leroymerlin_scraper import LeroymerlinScraper
from utils.logger import get_logger

def run_castorama():
    """Run Castorama scraper in a separate thread."""
    try:
        print("🚀 Starting Castorama scraper...")
        scraper = CastoramaScraper()
        keywords = ["Peinture", "Lavabos", "Toilettes", "Meubles-lavabos", "Douches", "Carrelage"]
        scraper.run(keywords)
        print("✅ Castorama scraper completed!")
    except Exception as e:
        print(f"❌ Castorama scraper failed: {e}")

def run_manomano():
    """Run ManoMano scraper in a separate thread."""
    try:
        print("🚀 Starting ManoMano scraper...")
        scraper = ManomanoScraper()
        categories = ["Carrelage", "Éviers", "Toilettes", "Peinture", "Vanités", "Douches"]
        scraper.run(categories)
        print("✅ ManoMano scraper completed!")
    except Exception as e:
        print(f"❌ ManoMano scraper failed: {e}")

def run_leroymerlin():
    """Run Leroy Merlin scraper in a separate thread."""
    try:
        print("🚀 Starting Leroy Merlin scraper...")
        scraper = LeroymerlinScraper()
        keywords = ["Peinture", "Lavabos", "Toilettes", "Meubles-lavabos", "Douches", "Carrelage"]
        scraper.run(keywords)
        print("✅ Leroy Merlin scraper completed!")
    except Exception as e:
        print(f"❌ Leroy Merlin scraper failed: {e}")

def main():
    """Run all three scrapers in parallel."""
    print("=" * 60)
    print("🎯 STARTING PARALLEL SCRAPING SESSION")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    start_time = time.time()
    
    # Create threads for each scraper
    castorama_thread = threading.Thread(target=run_castorama, name="CastoramaScraper")
    manomano_thread = threading.Thread(target=run_manomano, name="ManomanoScraper")
    leroymerlin_thread = threading.Thread(target=run_leroymerlin, name="LeroymerlinScraper")
    
    # Start all scrapers
    castorama_thread.start()
    manomano_thread.start()
    leroymerlin_thread.start()
    
    # Wait for all to complete
    castorama_thread.join()
    manomano_thread.join()
    leroymerlin_thread.join()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("=" * 60)
    print("✅ PARALLEL SCRAPING SESSION COMPLETED")
    print(f"⏱️  Total Duration: {duration:.2f} seconds")
    print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
