"""
Tests for Donizo Material Scraper components.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch

from utils.data_processor import DataProcessor
from scrapers.castorama_scraper import CastoramaScraper
from scrapers.leroymerlin_scraper import LeroymerlinScraper
from scrapers.manomano_scraper import ManomanoScraper


class TestDataProcessor:
    """Test cases for DataProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DataProcessor()
    
    def test_generate_product_id(self):
        """Test product ID generation."""
        supplier = 'test_supplier'
        product_url = 'https://example.com/product'
        sku_id = 'SKU123'
        
        product_id = self.processor.generate_product_id(supplier, product_url, sku_id)
        
        assert isinstance(product_id, str)
        assert len(product_id) > 0
        assert product_id == f"{supplier}_{sku_id}"
        
        # Test without SKU
        product_id_no_sku = self.processor.generate_product_id(supplier, product_url)
        assert product_id_no_sku.startswith(f"{supplier}_")
    
    def test_normalize_price(self):
        """Test price normalization."""
        # Test various price formats
        test_cases = [
            ('€25.99', {'price': '25.99', 'price_currency': 'EUR'}),
            ('25,99 €', {'price': '25.99', 'price_currency': 'EUR'}),
            ('19.99€/m²', {'price': '19.99', 'price_currency': 'EUR'}),
            ('15.50 EUR', {'price': '15.50', 'price_currency': 'EUR'}),
            ('Invalid', {'price': '', 'price_currency': 'EUR'})
        ]
        
        for price_input, expected in test_cases:
            result = self.processor.normalize_price(price_input)
            assert result['price'] == expected['price']
            assert result['price_currency'] == expected['price_currency']
    
    def test_normalize_measurement(self):
        """Test measurement normalization."""
        # Test various measurement formats
        test_cases = [
            ({'width': '30 cm', 'length': '60 cm'}, {'width': '30', 'length': '60', 'unit': 'cm'}),
            ({'width': '100mm', 'height': '200mm'}, {'width': '100', 'height': '200', 'unit': 'cm'}),
            ({}, {}),
            ({'invalid': 'data'}, {})
        ]
        
        for measurement, expected in test_cases:
            result = self.processor.normalize_measurement(measurement)
            if expected:
                assert result.get('unit') == expected.get('unit')
            else:
                assert result == {}
    
    def test_validate_url(self):
        """Test URL validation."""
        # Test valid URLs
        valid_urls = [
            'https://www.castorama.fr/product',
            'https://www.leroymerlin.fr/product',
            'https://www.manomano.fr/product'
        ]
        
        for url in valid_urls:
            result = self.processor.validate_url(url)
            assert result == True
        
        # Test invalid URLs
        invalid_urls = [
            'not_a_url',
            'ftp://example.com',
            'http://invalid-domain.com'
        ]
        
        for url in invalid_urls:
            result = self.processor.validate_url(url)
            assert result == False
    
    def test_normalize_brand(self):
        """Test brand normalization."""
        test_cases = [
            ('BRAND NAME', 'Brand Name'),
            ('brand name', 'Brand Name'),
            ('bRaNd NaMe', 'Brand Name'),
            ('', 'Unknown'),
            ('N/A', 'Unknown')
        ]
        
        for input_brand, expected in test_cases:
            result = self.processor.normalize_brand(input_brand)
            assert result == expected
    
    def test_determine_availability(self):
        """Test availability determination."""
        # Test available products
        available_product = {'name': 'Available Product'}
        assert self.processor.determine_availability(available_product) == 'in_stock'
        
        # Test out of stock products
        out_of_stock_indicators = [
            'rupture de stock',
            'indisponible',
            'out of stock',
            'épuisé'
        ]
        
        for indicator in out_of_stock_indicators:
            product = {'name': f'Product {indicator}'}
            assert self.processor.determine_availability(product) == 'out_of_stock'
    
    def test_remove_duplicates(self):
        """Test duplicate removal."""
        products = [
            {'product_name': 'Product 1', 'product_url': 'https://example.com/1'},
            {'product_name': 'Product 2', 'product_url': 'https://example.com/2'},
            {'product_name': 'Product 1 Duplicate', 'product_url': 'https://example.com/1'},  # Duplicate
            {'product_name': 'Product 3', 'product_url': 'https://example.com/3'}
        ]
        
        result = self.processor.remove_duplicates(products)
        
        assert len(result) == 3  # Should remove one duplicate
        assert any(p['product_name'] == 'Product 1' for p in result)
        assert any(p['product_name'] == 'Product 2' for p in result)
        assert any(p['product_name'] == 'Product 3' for p in result)


class TestCastoramaScraper:
    """Test cases for CastoramaScraper."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = CastoramaScraper()
    
    def test_initialization(self):
        """Test scraper initialization."""
        assert hasattr(self.scraper, 'headers')
        assert hasattr(self.scraper, 'session')
        assert hasattr(self.scraper, 'all_products')
        assert isinstance(self.scraper.all_products, list)
    
    def test_save_to_json(self):
        """Test JSON saving functionality."""
        # Add some test products
        self.scraper.all_products = [
            {'name': 'Test Product 1', 'price': '€25.99'},
            {'name': 'Test Product 2', 'price': '€19.99'}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            original_filename = self.scraper.save_to_json.__defaults__[0] if self.scraper.save_to_json.__defaults__ else 'castorama_scraper___.json'
            
            # Temporarily change the save filename
            self.scraper.save_to_json.__defaults__ = (tmp_file.name,)
            
            try:
                self.scraper.save_to_json()
                
                # Check if file was created and contains data
                assert os.path.exists(tmp_file.name)
                
                with open(tmp_file.name, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                assert len(data) == 2
                assert data[0]['name'] == 'Test Product 1'
                assert data[1]['name'] == 'Test Product 2'
                
            finally:
                # Clean up
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)
    
    @patch('requests.Session.get')
    def test_product_parser(self, mock_get):
        """Test product parsing functionality."""
        # Mock HTML response with the actual structure Castorama uses
        mock_html = '''
        <html>
            <main id="main-content">
                <script type="application/ld+json">
                {
                    "itemListElement": [
                        {
                            "sku": "SKU123",
                            "name": "Test Product",
                            "offers": {
                                "price": "25.99",
                                "priceCurrency": "EUR"
                            },
                            "url": "/product/123",
                            "aggregateRating": {
                                "ratingValue": "4.5"
                            },
                            "description": "Test product description"
                        }
                    ]
                }
                </script>
            </main>
        </html>
        '''
        
        # Mock the product detail page response
        mock_detail_html = '''
        <html>
            <ul data-testid="product-gallery-thumbnail-list">
                <img src="https://example.com/image1.jpg?$param" />
            </ul>
            <table>
                <tr>
                    <th>Marque</th>
                    <td>Test Brand</td>
                </tr>
                <tr>
                    <th>Largeur (cm)</th>
                    <td>30</td>
                </tr>
                <tr>
                    <th>Hauteur (cm)</th>
                    <td>60</td>
                </tr>
            </table>
        </html>
        '''
        
        mock_response = Mock()
        mock_response.text = mock_detail_html
        mock_get.return_value = mock_response
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(mock_html, 'html.parser')
        
        products = self.scraper.product_parser(soup, 'Test Category')
        
        assert len(products) == 1
        product = products[0]
        assert product['product_name'] == 'Test Product'
        assert product['category'] == 'Test Category'
        assert product['price'] == '25.99'
        assert product['sku_id'] == 'SKU123'


class TestLeroymerlinScraper:
    """Test cases for LeroymerlinScraper."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = LeroymerlinScraper()
    
    def test_initialization(self):
        """Test scraper initialization."""
        assert hasattr(self.scraper, 'headers')
        assert hasattr(self.scraper, 'session')
        assert hasattr(self.scraper, 'all_products')
        assert isinstance(self.scraper.all_products, list)
    
    def test_save_to_json(self):
        """Test JSON saving functionality."""
        # Add some test products
        self.scraper.all_products = [
            {'name': 'Test Product 1', 'price': '€25.99'},
            {'name': 'Test Product 2', 'price': '€19.99'}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            original_filename = self.scraper.save_to_json.__defaults__[0] if self.scraper.save_to_json.__defaults__ else 'leroymerlin_scraper___.json'
            
            # Temporarily change the save filename
            self.scraper.save_to_json.__defaults__ = (tmp_file.name,)
            
            try:
                self.scraper.save_to_json()
                
                # Check if file was created and contains data
                assert os.path.exists(tmp_file.name)
                
                with open(tmp_file.name, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                assert len(data) == 2
                assert data[0]['name'] == 'Test Product 1'
                assert data[1]['name'] == 'Test Product 2'
                
            finally:
                # Clean up
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)


class TestManomanoScraper:
    """Test cases for ManomanoScraper."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = ManomanoScraper()
    
    def test_initialization(self):
        """Test scraper initialization."""
        assert hasattr(self.scraper, 'headers')
        assert hasattr(self.scraper, 'all_products')
        assert hasattr(self.scraper, 'json_file')
        assert isinstance(self.scraper.all_products, list)
    
    def test_extract_capital_brand(self):
        """Test brand extraction functionality."""
        test_cases = [
            ('This is a TEST BRAND product', 'TEST BRAND'),
            ('Another BRAND NAME here', 'BRAND NAME'),
            ('No brand here', None),
            ('MULTIPLE BRANDS HERE', 'MULTIPLE BRANDS'),
            ('', None)
        ]
        
        for text, expected in test_cases:
            result = self.scraper.extract_capital_brand(text)
            assert result == expected
    
    def test_save_to_json(self):
        """Test JSON saving functionality."""
        # Add some test products
        self.scraper.all_products = [
            {'name': 'Test Product 1', 'price': '€25.99'},
            {'name': 'Test Product 2', 'price': '€19.99'}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            original_filename = self.scraper.json_file
            self.scraper.json_file = tmp_file.name
            
            try:
                self.scraper.save_to_json()
                
                # Check if file was created and contains data
                assert os.path.exists(tmp_file.name)
                
                with open(tmp_file.name, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                assert len(data) == 2
                assert data[0]['name'] == 'Test Product 1'
                assert data[1]['name'] == 'Test Product 2'
                
            finally:
                # Clean up
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)
                self.scraper.json_file = original_filename


if __name__ == '__main__':
    pytest.main([__file__])
