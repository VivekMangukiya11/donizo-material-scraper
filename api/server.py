"""
FastAPI server for Donizo Material Scraper
Provides RESTful endpoints for accessing scraped data
"""

import json
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from utils.data_processor import DataProcessor


class ProductResponse(BaseModel):
    """Product response model"""
    id: str
    supplier: str
    category: str
    product_name: str
    brand: str
    price: str
    price_currency: str
    product_url: str
    image_urls: List[str]
    measurement: Dict[str, Any]
    rating: str
    availability: str
    sku_id: str
    description: str
    timestamp: str
    metadata: Dict[str, Any]


class StatsResponse(BaseModel):
    """Statistics response model"""
    total_products: int
    suppliers: Dict[str, int]
    categories: Dict[str, int]
    last_updated: str


class APIServer:
    """FastAPI server for material data"""
    
    def __init__(self, config_path: str = "config/scraper_config.yaml"):
        self.config = self._load_config(config_path)
        self.data_processor = DataProcessor(self.config)
        self.app = self._create_app()
        self._setup_routes()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Configuration file not found: {config_path}")
            return {}
        except yaml.YAMLError as e:
            print(f"Warning: Error parsing configuration: {e}")
            return {}
    
    def _create_app(self) -> FastAPI:
        """Create FastAPI application"""
        api_config = self.config.get('api', {})
        
        app = FastAPI(
            title="Donizo Material Scraper API",
            description="API for accessing scraped renovation material data",
            version="1.0.0"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=api_config.get('cors_origins', ["*"]),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        return app
    
    def _setup_routes(self) -> None:
        """Setup API routes"""
        
        @self.app.get("/", response_model=Dict[str, str])
        async def root():
            """Root endpoint"""
            return {
                "message": "Donizo Material Scraper API",
                "version": "1.0.0",
                "docs": "/docs"
            }
        
        @self.app.get("/materials", response_model=List[ProductResponse])
        async def get_materials(
            supplier: Optional[str] = Query(None, description="Filter by supplier"),
            category: Optional[str] = Query(None, description="Filter by category"),
            limit: int = Query(100, description="Maximum number of products to return"),
            offset: int = Query(0, description="Number of products to skip")
        ):
            """Get all materials with optional filtering"""
            products = self._load_products()
            
            # Apply filters
            if supplier:
                products = [p for p in products if p.get('supplier') == supplier]
            
            if category:
                products = [p for p in products if p.get('category') == category]
            
            # Apply pagination
            products = products[offset:offset + limit]
            
            return products
        
        @self.app.get("/materials/{category}", response_model=List[ProductResponse])
        async def get_materials_by_category(
            category: str,
            supplier: Optional[str] = Query(None, description="Filter by supplier"),
            limit: int = Query(100, description="Maximum number of products to return"),
            offset: int = Query(0, description="Number of products to skip")
        ):
            """Get materials by category"""
            products = self._load_products()
            
            # Filter by category
            products = [p for p in products if p.get('category') == category]
            
            # Apply supplier filter if specified
            if supplier:
                products = [p for p in products if p.get('supplier') == supplier]
            
            # Apply pagination
            products = products[offset:offset + limit]
            
            if not products:
                raise HTTPException(status_code=404, detail=f"No products found for category: {category}")
            
            return products
        
        @self.app.get("/materials/search/{query}", response_model=List[ProductResponse])
        async def search_materials(
            query: str,
            supplier: Optional[str] = Query(None, description="Filter by supplier"),
            limit: int = Query(100, description="Maximum number of products to return"),
            offset: int = Query(0, description="Number of products to skip")
        ):
            """Search materials by query"""
            products = self._load_products()
            
            # Search in product name and description
            query_lower = query.lower()
            filtered_products = []
            
            for product in products:
                product_name = product.get('product_name', '').lower()
                description = product.get('description', '').lower()
                brand = product.get('brand', '').lower()
                
                if (query_lower in product_name or 
                    query_lower in description or 
                    query_lower in brand):
                    filtered_products.append(product)
            
            # Apply supplier filter if specified
            if supplier:
                filtered_products = [p for p in filtered_products if p.get('supplier') == supplier]
            
            # Apply pagination
            filtered_products = filtered_products[offset:offset + limit]
            
            return filtered_products
        
        @self.app.get("/materials/stats", response_model=StatsResponse)
        async def get_stats():
            """Get scraping statistics"""
            products = self._load_products()
            
            # Count by supplier
            suppliers = {}
            for product in products:
                supplier = product.get('supplier', 'unknown')
                suppliers[supplier] = suppliers.get(supplier, 0) + 1
            
            # Count by category
            categories = {}
            for product in products:
                category = product.get('category', 'unknown')
                categories[category] = categories.get(category, 0) + 1
            
            # Get last updated timestamp
            last_updated = "Unknown"
            if products:
                timestamps = [p.get('timestamp', '') for p in products if p.get('timestamp')]
                if timestamps:
                    last_updated = max(timestamps)
            
            return StatsResponse(
                total_products=len(products),
                suppliers=suppliers,
                categories=categories,
                last_updated=last_updated
            )
        
        @self.app.get("/categories", response_model=Dict[str, List[str]])
        async def get_categories():
            """Get available categories"""
            products = self._load_products()
            
            categories = {}
            for product in products:
                supplier = product.get('supplier', 'unknown')
                category = product.get('category', 'unknown')
                
                if supplier not in categories:
                    categories[supplier] = []
                
                if category not in categories[supplier]:
                    categories[supplier].append(category)
            
            return categories
        
        @self.app.get("/suppliers", response_model=List[str])
        async def get_suppliers():
            """Get available suppliers"""
            products = self._load_products()
            
            suppliers = set()
            for product in products:
                supplier = product.get('supplier', 'unknown')
                suppliers.add(supplier)
            
            return list(suppliers)
        
        @self.app.get("/health", response_model=Dict[str, str])
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    def _load_products(self) -> List[Dict[str, Any]]:
        """Load products from JSON file"""
        output_config = self.config.get('output', {})
        file_path = output_config.get('file_path', 'data/materials.json')
        
        return self.data_processor.load_from_json(file_path)
    
    def run(self, host: str = None, port: int = None, debug: bool = None):
        """Run the API server"""
        api_config = self.config.get('api', {})
        
        host = host or api_config.get('host', 'localhost')
        port = port or api_config.get('port', 8000)
        debug = debug if debug is not None else api_config.get('debug', False)
        
        import uvicorn
        uvicorn.run(self.app, host=host, port=port, debug=debug)


def main():
    """Main entry point for API server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Donizo Material Scraper API Server")
    parser.add_argument("--config", "-c", default="config/scraper_config.yaml",
                       help="Path to configuration file")
    parser.add_argument("--host", default=None, help="Host to bind to")
    parser.add_argument("--port", type=int, default=None, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    try:
        server = APIServer(args.config)
        print(f"🚀 Starting API server...")
        print(f"📖 API documentation available at: http://{args.host or 'localhost'}:{args.port or 8000}/docs")
        server.run(host=args.host, port=args.port, debug=args.debug)
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
