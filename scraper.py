#!/usr/bin/env python3
"""
Donizo Material Scraper - Main Orchestrator
Scrapes renovation material pricing data from multiple French suppliers
and structures it in a developer- and product-friendly format.
"""

import argparse
import json
import logging
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path

# Import scrapers
from scrapers.castorama_scraper import CastoramaScraper
from scrapers.leroymerlin_scraper import LeroymerlinScraper
from scrapers.manomano_scraper import ManomanoScraper

# Import utilities
from utils.data_processor import DataProcessor
from utils.logger import get_logger, get_output_manager

# Get main logger
logger = get_logger("main")

class DonizoMaterialScraper:
    """Main orchestrator for the Donizo Material Scraper."""
    
    def __init__(self, config_path='config/scraper_config.yaml'):
        """Initialize the scraper with configuration."""
        self.config = self._load_config(config_path)
        self.data_processor = DataProcessor(self.config)
        self.output_manager = get_output_manager()
        self.main_logger = get_logger("main")
        
        self.stats = {
            'start_time': datetime.now(),
            'total_products': 0,
            'suppliers': {},
            'categories': {},
            'errors': []
        }
        
        # Create output directories
        os.makedirs('output/data', exist_ok=True)
        os.makedirs('output/logs', exist_ok=True)
        os.makedirs('output/reports', exist_ok=True)
        
    def _load_config(self, config_path):
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            self.main_logger.log_info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            self.main_logger.log_error(Exception(f"Configuration file not found: {config_path}"), "config loading")
            sys.exit(1)
        except yaml.YAMLError as e:
            self.main_logger.log_error(e, "config parsing")
            sys.exit(1)
    
    def _get_scraper_instance(self, supplier_name):
        """Get scraper instance based on supplier name."""
        scrapers = {
            'castorama': CastoramaScraper,
            'leroymerlin': LeroymerlinScraper,
            'manomano': ManomanoScraper
        }
        
        scraper_class = scrapers.get(supplier_name.lower())
        if not scraper_class:
            raise ValueError(f"Unknown supplier: {supplier_name}")
            
        return scraper_class()
    
    def _process_scraper_output(self, scraper, supplier_name):
        """Process the output from a scraper and structure it."""
        try:
            # Get the raw products from the scraper
            raw_products = scraper.all_products
            
            if not raw_products:
                self.main_logger.log_warning(f"No products found for {supplier_name}")
                return []
            
            # Process and structure the data
            structured_products = []
            for product in raw_products:
                try:
                    # Use the process_product method to handle all processing
                    processed_product = self.data_processor.process_product(product, supplier_name)
                    
                    # Add additional fields for the structured output
                    structured_product = {
                        'id': processed_product['id'],
                        'name': processed_product.get('product_name', ''),
                        'category': processed_product.get('category', ''),
                        'supplier': supplier_name.title(),
                        'price': {
                            'amount': processed_product.get('price', ''),
                            'currency': processed_product.get('price_currency', 'EUR'),
                            'unit': 'piece'  # Default unit
                        },
                        'url': processed_product.get('product_url', ''),
                        'brand': processed_product.get('brand', ''),
                        'measurements': processed_product.get('measurement', {}),
                        'availability': processed_product.get('availability', 'unknown'),
                        'image_url': processed_product.get('image_urls', []),
                        'scraped_at': processed_product.get('timestamp', datetime.now().isoformat()),
                        'raw_data': product  # Keep original data for reference
                    }
                    
                    structured_products.append(structured_product)
                    
                except Exception as e:
                    self.main_logger.log_error(e, f"processing product {product.get('name', 'Unknown')}")
                    self.stats['errors'].append({
                        'supplier': supplier_name,
                        'product': product.get('name', 'Unknown'),
                        'error': str(e)
                    })
                    continue
            
            # Remove duplicates
            structured_products = self.data_processor.remove_duplicates(structured_products)
            
            self.main_logger.log_success(f"Processed {len(structured_products)} products from {supplier_name}")
            return structured_products
            
        except Exception as e:
            self.main_logger.log_error(e, f"processing {supplier_name} output")
            self.stats['errors'].append({
                'supplier': supplier_name,
                'error': str(e)
            })
            return []
    
    def scrape_supplier(self, supplier_name, categories):
        """Scrape a specific supplier for given categories."""
        self.main_logger.log_info(f"Starting scrape for {supplier_name}")
        
        try:
            # Get scraper instance
            scraper = self._get_scraper_instance(supplier_name)
            
            # Run the scraper with the original logic
            if supplier_name.lower() == 'castorama':
                scraper.run(categories)
            elif supplier_name.lower() == 'leroymerlin':
                scraper.run(categories)
            elif supplier_name.lower() == 'manomano':
                scraper.run(categories)
            
            # Process the output
            structured_products = self._process_scraper_output(scraper, supplier_name)
            
            # Update stats
            self.stats['suppliers'][supplier_name] = {
                'products_scraped': len(structured_products),
                'categories': list(set(p['category'] for p in structured_products))
            }
            
            return structured_products
            
        except Exception as e:
            self.main_logger.log_error(e, f"scraping {supplier_name}")
            self.stats['errors'].append({
                'supplier': supplier_name,
                'error': str(e)
            })
            return []
    
    def run(self, suppliers=None, categories=None):
        """Run the scraper for specified suppliers and categories."""
        if suppliers is None:
            suppliers = self.config.get('suppliers', ['castorama', 'leroymerlin', 'manomano'])
        
        if categories is None:
            categories = self.config.get('categories', [
                'Peinture', 'Lavabos', 'Toilettes', 'Meubles-lavabos', 
                'Douches', 'Carrelage', 'Éviers', 'Vanités'
            ])
        
        self.main_logger.log_scraping_start(categories)
        self.main_logger.log_info(f"Suppliers: {suppliers}")
        self.main_logger.log_info(f"Categories: {categories}")
        
        all_products = []
        all_data_by_supplier = {}
        
        # Scrape each supplier
        for supplier in suppliers:
            try:
                products = self.scrape_supplier(supplier, categories)
                all_products.extend(products)
                all_data_by_supplier[supplier] = products
                
                # Update category stats
                for product in products:
                    category = product['category']
                    if category not in self.stats['categories']:
                        self.stats['categories'][category] = 0
                    self.stats['categories'][category] += 1
                    
            except Exception as e:
                self.main_logger.log_error(e, f"Failed to scrape {supplier}")
                continue
        
        # Final processing
        all_products = self.data_processor.remove_duplicates(all_products)
        self.stats['total_products'] = len(all_products)
        self.stats['end_time'] = datetime.now()
        self.stats['duration'] = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        # Save results
        self._save_results(all_products, all_data_by_supplier)
        
        # Log summary
        self._log_summary()
        
        return all_products
    
    def _save_results(self, products, all_data_by_supplier):
        """Save scraped data to organized output files."""
        try:
            # Save consolidated data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            consolidated_file = self.output_manager.save_consolidated_data(all_data_by_supplier, timestamp)
            self.main_logger.log_success(f"Consolidated data saved to {consolidated_file}")
            
            # Generate and save report
            report_file = self.output_manager.generate_scraping_report(self.stats, timestamp)
            self.main_logger.log_success(f"Scraping report saved to {report_file}")
            
        except Exception as e:
            self.main_logger.log_error(e, "saving results")
    
    def _log_summary(self):
        """Log scraping summary."""
        self.main_logger.log_info("=" * 60)
        self.main_logger.log_info("SCRAPING SUMMARY")
        self.main_logger.log_info("=" * 60)
        self.main_logger.log_info(f"Total products scraped: {self.stats['total_products']}")
        self.main_logger.log_info(f"Duration: {self.stats['duration']:.2f} seconds")
        self.main_logger.log_info(f"Suppliers processed: {len(self.stats['suppliers'])}")
        self.main_logger.log_info(f"Categories found: {len(self.stats['categories'])}")
        
        if self.stats['errors']:
            self.main_logger.log_warning(f"Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:  # Show first 5 errors
                self.main_logger.log_warning(f"  - {error}")
        
        self.main_logger.log_info("=" * 60)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Donizo Material Scraper')
    parser.add_argument('--config', default='config/scraper_config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--suppliers', nargs='+',
                       help='Specific suppliers to scrape')
    parser.add_argument('--categories', nargs='+',
                       help='Specific categories to scrape')
    parser.add_argument('--output', default='output/data/materials.json',
                       help='Output file path')
    
    args = parser.parse_args()
    
    try:
        # Initialize scraper
        scraper = DonizoMaterialScraper(args.config)
        
        # Run scraping
        products = scraper.run(
            suppliers=args.suppliers,
            categories=args.categories
        )
        
        print(f"\n✅ Scraping completed successfully!")
        print(f"📊 Total products: {len(products)}")
        print(f"💾 Results saved to: output/data/")
        print(f"📋 Reports saved to: output/reports/")
        print(f"📝 Logs saved to: output/logs/")
        
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Scraping failed: {e}")
        logger.log_error(e, "main execution")
        sys.exit(1)

if __name__ == "__main__":
    main()
