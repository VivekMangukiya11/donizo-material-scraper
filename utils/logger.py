"""
Professional logging utility for Donizo Material Scraper
Provides consistent logging across all scrapers with proper formatting and file management.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
import json
import csv


class ScraperLogger:
    """Professional logger for scraper operations."""
    
    def __init__(self, scraper_name: str, log_dir: str = "output/logs"):
        """
        Initialize logger for a specific scraper.
        
        Args:
            scraper_name: Name of the scraper (e.g., 'castorama', 'leroymerlin')
            log_dir: Directory to store log files
        """
        self.scraper_name = scraper_name.lower()
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(f"scraper.{self.scraper_name}")
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        self._setup_formatters()
        
        # Setup handlers
        self._setup_handlers()
        
        # Log initialization
        self.logger.info(f"🚀 {self.scraper_name.title()} Scraper Logger initialized")
    
    def _setup_formatters(self):
        """Setup log formatters."""
        # Console formatter (colored and concise)
        self.console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File formatter (detailed)
        self.file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def _setup_handlers(self):
        """Setup log handlers."""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (rotating)
        log_file = self.log_dir / f"{self.scraper_name}_scraper.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self.file_formatter)
        self.logger.addHandler(file_handler)
        
        # Error file handler
        error_log_file = self.log_dir / f"{self.scraper_name}_errors.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self.file_formatter)
        self.logger.addHandler(error_handler)
    
    def log_scraping_start(self, categories: list):
        """Log scraping session start."""
        self.logger.info("=" * 60)
        self.logger.info(f"🎯 STARTING {self.scraper_name.upper()} SCRAPING SESSION")
        self.logger.info(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"📋 Categories: {', '.join(categories)}")
        self.logger.info("=" * 60)
    
    def log_scraping_end(self, total_products: int, duration: float):
        """Log scraping session end."""
        self.logger.info("=" * 60)
        self.logger.info(f"✅ {self.scraper_name.upper()} SCRAPING SESSION COMPLETED")
        self.logger.info(f"📊 Total Products: {total_products}")
        self.logger.info(f"⏱️  Duration: {duration:.2f} seconds")
        self.logger.info(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 60)
    
    def log_category_start(self, category: str):
        """Log category scraping start."""
        self.logger.info(f"🔍 Starting category: {category}")
    
    def log_category_end(self, category: str, products_count: int):
        """Log category scraping end."""
        self.logger.info(f"✅ Category '{category}' completed: {products_count} products")
    
    def log_page_scraping(self, page: int, url: str, products_found: int):
        """Log page scraping progress."""
        self.logger.info(f"📄 Page {page}: {products_found} products from {url}")
    
    def log_error(self, error: Exception, context: str = ""):
        """Log error with context."""
        error_msg = f"❌ Error in {context}: {str(error)}" if context else f"❌ Error: {str(error)}"
        self.logger.error(error_msg, exc_info=True)
    
    def log_warning(self, message: str):
        """Log warning message."""
        self.logger.warning(f"⚠️  {message}")
    
    def log_success(self, message: str):
        """Log success message."""
        self.logger.info(f"✅ {message}")
    
    def log_info(self, message: str):
        """Log info message."""
        self.logger.info(f"ℹ️  {message}")
    
    def log_debug(self, message: str):
        """Log debug message."""
        self.logger.debug(f"🔧 {message}")


class OutputManager:
    """Manages output files and reports."""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize output manager.
        
        Args:
            output_dir: Base output directory
        """
        self.output_dir = Path(output_dir)
        self.data_dir = self.output_dir / "data"
        self.reports_dir = self.output_dir / "reports"
        
        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def initialize_session_files(self, scraper_name: str, session_id: str = None):
        """
        Initialize JSON and CSV files for a scraping session.
        
        Args:
            scraper_name: Name of the scraper
            session_id: Optional session ID, if None uses current timestamp
            
        Returns:
            tuple: (json_filepath, csv_filepath)
        """
        if session_id is None:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        json_filename = f"{scraper_name}_products_{session_id}.json"
        csv_filename = f"{scraper_name}_products_{session_id}.csv"
        
        json_filepath = self.data_dir / json_filename
        csv_filepath = self.data_dir / csv_filename
        
        # Initialize JSON file with metadata
        json_metadata = {
            "metadata": {
                "scraper": scraper_name,
                "session_id": session_id,
                "scraped_at": datetime.now().isoformat(),
                "total_products": 0,
                "file_version": "1.0"
            },
            "products": []
        }
        
        try:
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(json_metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise Exception(f"Failed to initialize JSON file {json_filepath}: {e}")
        
        # Initialize CSV file with headers
        fieldnames = [
            'sku_id', 'product_name', 'category', 'price', 'price_currency', 
            'product_url', 'brand', 'measurement', 'image_url', 'rating',
            'description', 'initial_price', 'discount_rate', 'original_price',
            'price_m', 'url_path', 'image_urls'
        ]
        
        try:
            with open(csv_filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
        except Exception as e:
            raise Exception(f"Failed to initialize CSV file {csv_filepath}: {e}")
        
        return str(json_filepath), str(csv_filepath)
    
    def append_products_to_session(self, scraper_name: str, products: list, session_id: str):
        """
        Append products to existing session files.
        
        Args:
            scraper_name: Name of the scraper
            products: List of products to append
            session_id: Session ID for the files
        """
        if not products:
            return
        
        json_filename = f"{scraper_name}_products_{session_id}.json"
        csv_filename = f"{scraper_name}_products_{session_id}.csv"
        
        json_filepath = self.data_dir / json_filename
        csv_filepath = self.data_dir / csv_filename
        
        # Append to JSON file
        try:
            # Read existing data
            with open(json_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Append new products
            data["products"].extend(products)
            data["metadata"]["total_products"] = len(data["products"])
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Write back
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            raise Exception(f"Failed to append to JSON file {json_filepath}: {e}")
        
        # Append to CSV file
        try:
            # Get all possible field names from the new products
            fieldnames = set()
            for product in products:
                fieldnames.update(product.keys())
            
            # Read existing CSV to get all fieldnames
            if csv_filepath.exists():
                with open(csv_filepath, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    existing_fieldnames = reader.fieldnames or []
                    fieldnames.update(existing_fieldnames)
            
            # Convert to sorted list for consistent column order
            fieldnames = sorted(list(fieldnames))
            
            # Append new products
            with open(csv_filepath, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                for product in products:
                    # Handle nested dictionaries (like measurement)
                    row = {}
                    for key, value in product.items():
                        if isinstance(value, dict):
                            # Flatten nested dictionaries
                            for nested_key, nested_value in value.items():
                                row[f"{key}_{nested_key}"] = nested_value
                        elif isinstance(value, list):
                            # Join lists with semicolon
                            row[key] = '; '.join(str(item) for item in value)
                        else:
                            row[key] = value
                    
                    writer.writerow(row)
                    
        except Exception as e:
            raise Exception(f"Failed to append to CSV file {csv_filepath}: {e}")
    
    def save_scraper_data(self, scraper_name: str, data: list, timestamp: str = None):
        """
        Save scraper data to JSON file.
        
        Args:
            scraper_name: Name of the scraper
            data: List of scraped products
            timestamp: Optional timestamp for filename
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"{scraper_name}_products_{timestamp}.json"
        filepath = self.data_dir / filename
        
        output_data = {
            "metadata": {
                "scraper": scraper_name,
                "scraped_at": datetime.now().isoformat(),
                "total_products": len(data),
                "file_version": "1.0"
            },
            "products": data
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            return str(filepath)
        except Exception as e:
            raise Exception(f"Failed to save data to {filepath}: {e}")
    
    def save_scraper_data_session(self, scraper_name: str, data: list, session_id: str = None):
        """
        Save scraper data to a session-specific file (one file per scraper per session).
        
        Args:
            scraper_name: Name of the scraper
            data: List of scraped products
            session_id: Optional session ID, if None uses current timestamp
        """
        if session_id is None:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"{scraper_name}_products_{session_id}.json"
        filepath = self.data_dir / filename
        
        output_data = {
            "metadata": {
                "scraper": scraper_name,
                "session_id": session_id,
                "scraped_at": datetime.now().isoformat(),
                "total_products": len(data),
                "file_version": "1.0"
            },
            "products": data
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            return str(filepath)
        except Exception as e:
            raise Exception(f"Failed to save session data to {filepath}: {e}")
    
    def save_scraper_data_csv(self, scraper_name: str, data: list, session_id: str = None):
        """
        Save scraper data to a CSV file.
        
        Args:
            scraper_name: Name of the scraper
            data: List of scraped products
            session_id: Optional session ID, if None uses current timestamp
        """
        if session_id is None:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"{scraper_name}_products_{session_id}.csv"
        filepath = self.data_dir / filename
        
        if not data:
            # Create empty CSV with headers
            fieldnames = [
                'sku_id', 'product_name', 'category', 'price', 'price_currency', 
                'product_url', 'brand', 'measurement', 'image_url', 'rating',
                'description', 'initial_price', 'discount_rate', 'original_price',
                'price_m', 'url_path', 'image_urls'
            ]
            try:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                return str(filepath)
            except Exception as e:
                raise Exception(f"Failed to save empty CSV to {filepath}: {e}")
        
        # Get all possible field names from the data
        fieldnames = set()
        for product in data:
            fieldnames.update(product.keys())
        
        # Convert to sorted list for consistent column order
        fieldnames = sorted(list(fieldnames))
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for product in data:
                    # Handle nested dictionaries (like measurement)
                    row = {}
                    for key, value in product.items():
                        if isinstance(value, dict):
                            # Flatten nested dictionaries
                            for nested_key, nested_value in value.items():
                                row[f"{key}_{nested_key}"] = nested_value
                        elif isinstance(value, list):
                            # Join lists with semicolon
                            row[key] = '; '.join(str(item) for item in value)
                        else:
                            row[key] = value
                    
                    writer.writerow(row)
            
            return str(filepath)
        except Exception as e:
            raise Exception(f"Failed to save CSV data to {filepath}: {e}")
    
    def save_consolidated_data(self, all_data: dict, timestamp: str = None):
        """
        Save consolidated data from all scrapers.
        
        Args:
            all_data: Dictionary with scraper names as keys and product lists as values
            timestamp: Optional timestamp for filename
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"consolidated_materials_{timestamp}.json"
        filepath = self.data_dir / filename
        
        total_products = sum(len(products) for products in all_data.values())
        
        output_data = {
            "metadata": {
                "scraped_at": datetime.now().isoformat(),
                "total_products": total_products,
                "suppliers": list(all_data.keys()),
                "file_version": "1.0"
            },
            "products_by_supplier": all_data
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            return str(filepath)
        except Exception as e:
            raise Exception(f"Failed to save consolidated data to {filepath}: {e}")
    
    def generate_scraping_report(self, stats: dict, timestamp: str = None):
        """
        Generate a comprehensive scraping report.
        
        Args:
            stats: Dictionary containing scraping statistics
            timestamp: Optional timestamp for filename
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"scraping_report_{timestamp}.json"
        filepath = self.reports_dir / filename
        
        report_data = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_type": "scraping_summary",
                "version": "1.0"
            },
            "scraping_stats": stats
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            return str(filepath)
        except Exception as e:
            raise Exception(f"Failed to save report to {filepath}: {e}")


def get_logger(scraper_name: str) -> ScraperLogger:
    """
    Get a logger instance for a specific scraper.
    
    Args:
        scraper_name: Name of the scraper
        
    Returns:
        ScraperLogger instance
    """
    return ScraperLogger(scraper_name)


def get_output_manager() -> OutputManager:
    """
    Get an output manager instance.
    
    Returns:
        OutputManager instance
    """
    return OutputManager()
