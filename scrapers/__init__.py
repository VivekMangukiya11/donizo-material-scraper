"""
Scrapers package for Donizo Material Scraper.
Contains individual scraper implementations for different suppliers.
"""

from .castorama_scraper import CastoramaScraper
from .leroymerlin_scraper import LeroymerlinScraper
from .manomano_scraper import ManomanoScraper

__all__ = [
    'CastoramaScraper',
    'LeroymerlinScraper', 
    'ManomanoScraper'
]
