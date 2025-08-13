"""
Data processing utilities for Donizo Material Scraper
Handles data validation, transformation, and standardization
"""

import re
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse


class DataProcessor:
    """Handles data processing, validation, and standardization"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.price_currency = self.config.get('data_processing', {}).get('price_currency', 'EUR')
        self.measurement_unit = self.config.get('data_processing', {}).get('measurement_unit', 'cm')
        
    def generate_product_id(self, supplier: str, product_url: str, sku_id: str = "") -> str:
        """Generate a unique product ID"""
        if sku_id:
            return f"{supplier}_{sku_id}"
        
        # Use URL hash as fallback
        url_hash = hashlib.md5(product_url.encode()).hexdigest()[:8]
        return f"{supplier}_{url_hash}"
    
    def normalize_price(self, price: str, currency: str = "EUR") -> Dict[str, str]:
        """Normalize price data"""
        if not price:
            return {"price": "", "price_currency": currency}
        
        # Remove currency symbols and whitespace
        clean_price = re.sub(r'[^\d.,]', '', str(price))
        
        # Handle different decimal separators
        if ',' in clean_price and '.' in clean_price:
            # Format: 1,234.56 or 1.234,56
            if clean_price.rfind(',') > clean_price.rfind('.'):
                clean_price = clean_price.replace('.', '').replace(',', '.')
            else:
                clean_price = clean_price.replace(',', '')
        elif ',' in clean_price:
            # Check if comma is decimal separator
            parts = clean_price.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                clean_price = clean_price.replace(',', '.')
            else:
                clean_price = clean_price.replace(',', '')
        
        return {
            "price": clean_price,
            "price_currency": currency
        }
    
    def normalize_measurement(self, measurement: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize measurement data"""
        if not measurement:
            return {}
        
        normalized = {}
        
        for key, value in measurement.items():
            if not value:
                continue
                
            # Extract numeric value
            numeric_value = re.search(r'(\d+(?:\.\d+)?)', str(value))
            if numeric_value:
                normalized[key] = numeric_value.group(1)
        
        if normalized:
            normalized["unit"] = self.measurement_unit
            
        return normalized
    
    def validate_url(self, url: str) -> bool:
        """Validate if URL is properly formatted"""
        if not url:
            return False
        
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def normalize_brand(self, brand: str) -> str:
        """Normalize brand names"""
        if not brand:
            return ""
        
        # Remove common prefixes/suffixes
        brand = re.sub(r'^(marque|brand):\s*', '', brand, flags=re.IGNORECASE)
        brand = brand.strip()
        
        # Capitalize properly
        if brand:
            brand = brand.title()
            
        return brand
    
    def determine_availability(self, product_data: Dict[str, Any]) -> str:
        """Determine product availability status"""
        # Check for availability indicators in product data
        availability_indicators = {
            "in_stock": ["en stock", "disponible", "available", "in stock"],
            "out_of_stock": ["rupture", "indisponible", "out of stock", "épuisé"],
            "limited": ["limité", "limited", "dernières pièces"]
        }
        
        # Check product name and description for availability clues
        text_to_check = f"{product_data.get('product_name', '')} {product_data.get('description', '')}".lower()
        
        for status, indicators in availability_indicators.items():
            if any(indicator in text_to_check for indicator in indicators):
                return status
        
        return "unknown"
    
    def process_product(self, product_data: Dict[str, Any], supplier: str) -> Dict[str, Any]:
        """Process and standardize a single product"""
        processed = {
            "id": self.generate_product_id(
                supplier, 
                product_data.get("product_url", ""), 
                product_data.get("sku_id", "")
            ),
            "supplier": supplier,
            "category": product_data.get("category", ""),
            "product_name": product_data.get("product_name", ""),
            "brand": self.normalize_brand(product_data.get("brand", "")),
            "product_url": product_data.get("product_url", ""),
            "sku_id": product_data.get("sku_id", ""),
            "description": product_data.get("description", ""),
            "rating": product_data.get("rating", ""),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Process price
        price_data = self.normalize_price(
            product_data.get("price", ""), 
            product_data.get("price_currency", self.price_currency)
        )
        processed.update(price_data)
        
        # Add original price if available
        if product_data.get("original_price"):
            original_price_data = self.normalize_price(
                product_data.get("original_price"), 
                product_data.get("price_currency", self.price_currency)
            )
            processed["original_price"] = original_price_data["price"]
        
        # Add discount rate if available
        if product_data.get("discount_rate"):
            processed["discount_rate"] = product_data["discount_rate"]
        
        # Process measurements
        processed["measurement"] = self.normalize_measurement(
            product_data.get("measurement", {})
        )
        
        # Process image URLs
        image_urls = product_data.get("image_urls", []) or product_data.get("image_url", [])
        if isinstance(image_urls, str):
            image_urls = [image_urls]
        
        # Validate and deduplicate image URLs
        valid_images = []
        seen_images = set()
        for img_url in image_urls:
            if img_url and self.validate_url(img_url) and img_url not in seen_images:
                valid_images.append(img_url)
                seen_images.add(img_url)
        
        processed["image_urls"] = valid_images
        
        # Determine availability
        processed["availability"] = self.determine_availability(product_data)
        
        # Add metadata
        processed["metadata"] = {
            "scraped_at": processed["timestamp"],
            "supplier_id": f"{supplier}_{processed['id']}",
            "data_version": "1.0"
        }
        
        return processed
    
    def remove_duplicates(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate products based on URL and name"""
        seen_products = set()
        unique_products = []
        
        for product in products:
            # Create a unique key based on URL and name
            product_key = f"{product.get('product_url', '')}_{product.get('product_name', '')}"
            
            if product_key not in seen_products:
                seen_products.add(product_key)
                unique_products.append(product)
        
        return unique_products
    
    def validate_product(self, product: Dict[str, Any]) -> bool:
        """Validate if product has required fields"""
        required_fields = ["product_name", "product_url", "price"]
        
        for field in required_fields:
            if not product.get(field):
                return False
        
        return True
    
    def process_products_batch(self, products: List[Dict[str, Any]], supplier: str) -> List[Dict[str, Any]]:
        """Process a batch of products"""
        processed_products = []
        
        for product in products:
            try:
                processed_product = self.process_product(product, supplier)
                if self.validate_product(processed_product):
                    processed_products.append(processed_product)
            except Exception as e:
                print(f"Error processing product {product.get('product_name', 'Unknown')}: {e}")
                continue
        
        # Remove duplicates if configured
        if self.config.get('data_processing', {}).get('remove_duplicates', True):
            processed_products = self.remove_duplicates(processed_products)
        
        return processed_products
    
    def save_to_json(self, products: List[Dict[str, Any]], file_path: str) -> None:
        """Save products to JSON file with backup"""
        import os
        
        # Create backup if configured
        if self.config.get('output', {}).get('backup_previous', True) and os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            try:
                os.rename(file_path, backup_path)
            except Exception as e:
                print(f"Warning: Could not create backup: {e}")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save to JSON
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            print(f"✅ Saved {len(products)} products to {file_path}")
        except Exception as e:
            print(f"❌ Error saving to JSON: {e}")
    
    def load_from_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Load products from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"❌ Error loading from JSON: {e}")
            return []
