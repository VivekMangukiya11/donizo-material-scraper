# Donizo Material Scraper

A Python-based web scraper that extracts renovation material pricing data from major French suppliers and structures it in a developer- and product-friendly format for Donizo's pricing engine.

## 🎯 Objective

Scrape real renovation material pricing data from French suppliers and structure it in a developer- and product-friendly format for Donizo's pricing engine.

## 🏗️ Project Structure

```
donizo-material-scraper/
├── scraper.py                 # Main orchestrator
├── config/
│   └── scraper_config.yaml    # Configuration file
├── scrapers/
│   ├── __init__.py
│   ├── castorama_scraper.py   # Castorama scraper (original logic)
│   ├── leroymerlin_scraper.py # Leroy Merlin scraper (original logic)
│   └── manomano_scraper.py    # ManoMano scraper (original logic)
├── utils/
│   ├── __init__.py
│   └── data_processor.py      # Data processing and structuring
├── api/
│   ├── __init__.py
│   └── server.py              # FastAPI server for data access
├── tests/
│   ├── __init__.py
│   └── test_scraper.py        # Unit tests
├── data/
│   └── materials.json         # Sample output
├── requirements.txt           # Python dependencies
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd donizo-material-scraper
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the scraper:**
   ```bash
   python scraper.py
   ```

## 📋 Usage

### Basic Usage

Run all scrapers with default configuration:
```bash
python scraper.py
```

### Advanced Usage

Run specific suppliers:
```bash
python scraper.py --suppliers castorama manomano
```

Run specific categories:
```bash
python scraper.py --categories "Peinture" "Carrelage" "Douches"
```

Use custom configuration:
```bash
python scraper.py --config custom_config.yaml
```

Specify output file:
```bash
python scraper.py --output data/my_materials.json
```

### Configuration

The scraper uses a YAML configuration file (`config/scraper_config.yaml`) to define:

- **Suppliers**: Which suppliers to scrape
- **Categories**: Product categories to target
- **Scraping settings**: Timeouts, delays, retries
- **Output settings**: File paths, data format
- **API settings**: Server configuration
- **Logging**: Log levels and file paths

Example configuration:
```yaml
suppliers:
  - castorama
  - leroymerlin
  - manomano

categories:
  - Peinture
  - Lavabos
  - Toilettes
  - Meubles-lavabos
  - Douches
  - Carrelage
  - Éviers
  - Vanités

scraping:
  delay_between_requests: 2
  timeout: 30
  max_retries: 3
  max_products_per_category: 100

output:
  file: data/materials.json
  format: json
  backup_previous: true
```

## 📊 Output Format

The scraper produces structured JSON data with the following format:

```json
{
  "metadata": {
    "scraper": "manomano",
    "session_id": "20250812_235158",
    "scraped_at": "2025-08-12T23:51:58.298218",
    "total_products": 648,
    "file_version": "1.0",
    "last_updated": "2025-08-12T23:58:52.581704"
  },
  "products": [
    {
      "product_id": 132162369,
      "product_name": "Carrelage Imitation Carreaux de Ciment LOFT FLOOR 20x20 (0,52m²) Sylvania - Les Carreaux de Jean",
      "brand": "NANDA TILES",
      "category": "Carrelage",
      "price": {
        "discount_price": 28.08,
        "original_price": 31.9,
        "unit_measurement": {
          "price": 54.0,
          "unit": "m²"
        },
        "currency": "EUR"
      },
      "measurement": {
        "length": "20.0",
        "width": "20.0",
        "unit": "cm"
      },
      "unit_count": "0.52 m²",
      "rating": 4.45,
      "rating_count": 20,
      "catgroy_path": "Carrelage, parquet et sol souple > Carrelage > Carrelage de sol intérieur > Carreaux de ciment",
      "product_url": "https://www.manomano.fr/p/carrelage-aspect-ciment-decore-vieilli-20x20-cm-strymon-052-m-35313125",
      "image_url": [
        "https://cdn.manomano.com/images/images_products/29803958/L/132162369_1.jpg",
        "https://cdn.manomano.com/images/images_products/29803958/L/132162369_2.jpg",
        "https://cdn.manomano.com/images/images_products/29803958/L/132162369_3.jpg",
        "https://cdn.manomano.com/images/images_products/29803958/L/132162369_4.jpg",
        "https://cdn.manomano.com/images/images_products/29803958/L/132162369_5.jpg",
        "https://cdn.manomano.com/images/images_products/29803958/L/132162369_6.jpg"
      ],
      "description": "Description généraleDécouvrez le carrelage aspect ciment décoré vieilli 20x20 cm STRYMON, parfait pour apporter une touche moderne et élégante à vos espaces intérieurs ou à vos terrasses couvertes. Ce carrelage en grès cérame combine esthétique et robustesse, offrant une surface mate qui résiste au gel.Spécifications techniquesType : grès cérame émailléDestination : Sol ou mur, intérieur et terrasse couverteRésistance : Résistant au gelSurface : MateDimensions : 20 cm x 20 cmÉpaisseur : 8 mmStyle : CimentUnité de vente : 0.52 m²Poids par m² : 10.7 kgCompatibilité et accessoiresProduit pour entretien régulier recommandé : FilaCleanerNettoyant de fin de chantier recommandé : DeterdekInstallationPour une installation optimale, suivez les recommandations du fabricant concernant la préparation du support et le choix des colles adaptées au grès cérame.UtilisationIdéal pour les zones à fort trafic, ce carrelage est parfait pour les salons, cuisines et terrasses couvertes, offrant à la fois style et durabilité.Autres informationsCe carrelage est conçu pour résister à l'usure et est facile à entretenir, ce qui en fait un choix pratique pour votre projet de rénovation ou de construction."
    },
    {
      "product_id": 88690989,
      "product_name": "Carrelage Effet Zellige MITTE Ocean 6,5x20cm (0,35m2 ) - Les Carreaux de Jean",
      "brand": "BESTILE",
      "category": "Carrelage",
      "price": {
        "discount_price": 20.12,
        "original_price": 22.29,
        "unit_measurement": {
          "price": 57.49,
          "unit": "m²"
        },
        "currency": "EUR"
      },
      "measurement": {
        "length": "20.0",
        "width": "6.5",
        "unit": "cm"
      },
      "unit_count": "0.35 m²",
      "rating": 0,
      "rating_count": 0,
      "catgroy_path": "Carrelage, parquet et sol souple > Carrelage > Carrelage de sol intérieur > Carrelage sol uni",
      "product_url": "https://www.manomano.fr/p/carrelage-effet-zellige-mitte-ocean-65x20cm-035m2-les-carreaux-de-jean-68566294",
      "image_url": [
        "https://cdn.manomano.com/images/images_products/29803958/L/88690989_1.jpg",
        "https://cdn.manomano.com/images/images_products/29803958/L/88690989_2.jpg",
        "https://cdn.manomano.com/images/images_products/29803958/L/88690989_3.jpg"
      ],
      "description": "Description généraleL’effet zellige, souvent utilisé dans les salles de bain et les cuisines, ajoute de la couleur et une touche d’authenticité à vos murs. Originaire du Maroc, le zellige est un carreau emblématique de la culture marocaine, apprécié pour ses couleurs vives et son aspect artisanal. Il crée une atmosphère chaleureuse et accueillante, idéale pour des espaces de vie dynamiques.Spécifications techniquesSérie MitteCarrelage effet zelligeDimensions : 6,5 x 20 cm6 coloris disponiblesEffet matMatériau : grès cérameÉpaisseur : 9 mmPose possible au sol et sur les mursBoîte de 0,35 m² (27 pièces)Compatibilité et accessoiresCompatible avec tous types d'adhésifs pour carrelagePeut être associé à des joints de couleur pour un rendu personnaliséInstallationPréparez la surface en la nettoyant et en la nivelantAppliquez l'adhésif uniformémentPosez les carreaux en veillant à respecter les espaces de jointoiementLaissez sécher selon les recommandations du fabricantUtilisationIdéal pour des applications murales et au sol dans des espaces intérieursFacile à nettoyer et à entretenir grâce à son matériau en grès cérameAjoute une touche décorative unique à votre intérieur"
    }
  ]
}
```

## 🔧 Data Processing

The `DataProcessor` class handles:

- **Product ID Generation**: Creates unique IDs for each product
- **Price Normalization**: Converts various price formats to standardized structure
- **Measurement Normalization**: Standardizes dimensions and units
- **URL Validation**: Ensures valid product URLs
- **Brand Normalization**: Standardizes brand names
- **Availability Detection**: Determines product availability
- **Duplicate Removal**: Removes duplicate products based on URLs

## 🌐 API Server

Start the API server to access scraped data via REST endpoints:

```bash
python -m api.server
```

Available endpoints:
- `GET /materials` - Get all materials
- `GET /materials/{category}` - Get materials by category
- `GET /materials/supplier/{supplier}` - Get materials by supplier
- `GET /search?q={query}` - Search materials
- `GET /stats` - Get scraping statistics

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
```

Run specific test categories:
```bash
pytest tests/test_scraper.py::TestDataProcessor
pytest tests/test_scraper.py::TestCastoramaScraper
```

## 📝 Data Assumptions & Transformations

### Price Handling
- Extracts numeric values from price strings
- Handles various currency symbols (€, EUR)
- Normalizes decimal separators (comma to period)
- Detects price per unit (e.g., €/m²)

### Measurement Handling
- Converts various measurement formats to standardized structure
- Handles dimensions like "30x60 cm" or "100x200mm"
- Normalizes units to standard format

### Brand Normalization
- Converts brand names to title case
- Handles missing or unknown brands
- Removes common prefixes/suffixes

### Availability Detection
- Detects out-of-stock indicators in French
- Defaults to "in_stock" for products without explicit availability info

### URL Validation
- Validates URLs from supported suppliers
- Rejects invalid or unsupported domains
- Returns "N/A" for invalid URLs

## 🔄 Pagination & Anti-Bot Logic

### Pagination Handling
- Each scraper implements its own pagination logic
- Detects "next page" buttons and pagination controls
- Respects maximum page limits from configuration
- Handles different pagination formats per supplier

### Anti-Bot Measures
- **Request Delays**: Configurable delays between requests
- **User-Agent Rotation**: Uses realistic browser user agents
- **Session Management**: Maintains persistent sessions
- **Retry Logic**: Automatic retries for failed requests
- **Error Handling**: Graceful handling of network errors

## ⭐ Bonus Features

### ✅ Implemented
- **API Simulation**: FastAPI server with RESTful endpoints
- **YAML Configuration**: Modular configuration system
- **Data Structuring**: Vector DB-ready output format
- **Timestamped Data**: Version tracking with timestamps
- **Availability Logic**: Out-of-stock detection
- **Comprehensive Testing**: Unit tests for all components
- **Logging**: Detailed logging for monitoring and debugging

### 🔮 Future Enhancements
- **Auto-sync Pipeline**: Monthly automated scraping
- **Price Comparison**: Cross-supplier price analysis
- **Advanced Analytics**: Price trend analysis
- **Web Dashboard**: Real-time monitoring interface
- **Database Integration**: Direct database storage
- **Cloud Deployment**: Scalable cloud infrastructure

## 🛠️ Development

### Adding New Suppliers

1. Create a new scraper class in `scrapers/`
2. Implement the required methods:
   - `__init__()`: Initialize scraper
   - `run(categories)`: Main scraping method
   - `save_to_json()`: Save results
3. Add the scraper to `scraper.py` mapping
4. Update configuration file
5. Add tests

### Adding New Categories

1. Update `config/scraper_config.yaml`
2. Ensure scrapers can handle the category
3. Update tests if needed

## 📈 Performance

### Optimization Tips
- Adjust `delay_between_requests` in config
- Use specific suppliers/categories for targeted scraping
- Monitor logs for performance bottlenecks
- Consider running scrapers in parallel (future enhancement)

### Expected Performance
- **Castorama**: ~50-100 products per category
- **Leroy Merlin**: ~50-100 products per category  
- **ManoMano**: ~50-100 products per category
- **Total**: 100+ products across all suppliers

## 🚨 Error Handling

The scraper includes comprehensive error handling:

- **Network Errors**: Automatic retries with exponential backoff
- **Parsing Errors**: Graceful handling of malformed HTML
- **Configuration Errors**: Clear error messages for invalid config
- **File I/O Errors**: Safe file operations with backups
- **Logging**: Detailed error logging for debugging

## 📄 License

This project is developed for the Donizo Material Scraper challenge.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📞 Support

For questions or issues:
1. Check the logs in `scraper.log`
2. Review the configuration file
3. Run tests to verify functionality
4. Check the API documentation

---

**Note**: This scraper preserves the original logic of the provided scraper files while adding structured output, API access, and comprehensive testing to meet the Donizo challenge requirements.
