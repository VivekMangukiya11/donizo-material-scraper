import json
from bs4 import BeautifulSoup
from datetime import datetime
from botasaurus.request import Request
from utils.logger import get_logger, get_output_manager


class ManomanoScraper:

    def __init__(self):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            'x-ig-app-id': '936619743392459'
        }
        self.all_products = []
        
        # Initialize logging and output management
        self.logger = get_logger("manomano")
        self.output_manager = get_output_manager()
        self.start_time = datetime.now()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize session files for incremental saving
        self.json_filepath, self.csv_filepath = self.output_manager.initialize_session_files("manomano", self.session_id)
        self.logger.log_info(f"Initialized session files: {self.json_filepath}, {self.csv_filepath}")

    def save_to_json(self):
        """Save all collected products to JSON and CSV files."""
        try:
            # Save JSON file
            json_filepath = self.output_manager.save_scraper_data_session("manomano", self.all_products, self.session_id)
            self.logger.log_success(f"Saved {len(self.all_products)} products to JSON: {json_filepath}")
            
            # Save CSV file
            csv_filepath = self.output_manager.save_scraper_data_csv("manomano", self.all_products, self.session_id)
            self.logger.log_success(f"Saved {len(self.all_products)} products to CSV: {csv_filepath}")
        except Exception as e:
            self.logger.log_error(e, "save_to_json")

    def append_products_incrementally(self, products):
        """Append products to session files incrementally."""
        if products:
            try:
                self.output_manager.append_products_to_session("manomano", products, self.session_id)
                self.logger.log_success(f"Appended {len(products)} products to session files")
            except Exception as e:
                self.logger.log_error(e, "append_products_incrementally")

    def product_parser(self, soup, category):
        products = []

        product_links = soup.find_all('a', {'data-testid': 'productCardListing'})
        if len(product_links) == 0:
            return products

        for a in product_links:
            href = 'https://www.manomano.fr' + a.get('href')
            try:
                if a.find(string=lambda t: t and 'Sponsorisé' in t):
                    continue
            except:
                pass
            response1 = Request().get(href, headers=self.headers)
            soup1 = BeautifulSoup(response1.text, 'html.parser')
            data = soup1.find('script',{'id':'__NEXT_DATA__'}).text.strip()
            json_data = json.loads(data)
            
            product_ = json_data['props']['pageProps']['initialReduxState']['productDiscovery']['productPage']

            product_name = product_['detail']['data']['title']
            try:
                productId = product_['detail']['data']['productId']
            except:
                productId-''
            try:
                brand = product_.get('brand', {}).get('name', '')
            except:
                brand = ''
            try:
                discount_price  = product_['detail']['data']['price']['primaryPrice']['amountWithVat']
            except:
                discount_price  = ''
            try:
                original_price = product_['detail']['data']['price']['retailPrice']['amountWithVat']
            except:
                original_price = discount_price 
            try:       
                unit_price_value  = product_['detail']['data']['price']['measurementPrice']['amountWithVat']
            except:
                unit_price_value =''   
            try:     
                unit_price_unit  = product_['detail']['data']['price']['measurementPrice']['measurementUnit']
            except:
                unit_price_unit =''
            try:    
                unit  = f"{unit_price_value} {unit_price_unit}"
            except:
                unit =''
            try:
                unitCount1 = product_['detail']['data']['unitCount']
            except:
                unitCount1 = ''
            try:
                unitCount = f"{unitCount1} {unit_price_unit}"
            except:
                unitCount = ''
            try:
                currency = product_['detail']['data']['currency']
            except:
                currency = 'EUR'
            price = {
                "price": float(discount_price) if discount_price != '' else None,
                "original_price": float(original_price) if original_price != '' else None,
                "unit_measurement": {
                    "price": float(unit_price_value) if unit_price_value != '' else None,
                    "unit": unit_price_unit or None
                },
                "currency": currency or None
            }    
            try:    
                rating = product_['detail']['data']['averageRating']
            except:
                rating =''
            try:
                totalRating = product_['detail']['data']['totalRating']
            except:
                totalRating = ''
            try:
                description_txt = product_['detail']['data']['description']
            except:
                description_txt = ''
            soup2 = BeautifulSoup(description_txt, 'html.parser')
            description = soup2.get_text(strip=True)
            cat_path=[]
            for variant in product_.get('breadcrumbs', []):
                cat_path.append(variant.get('name', ''))
            catgroy_path = ' > '.join(cat_path)
            
            image_url=[]
            for img in product_['detail']['data']['media']:
                image_url.append(img['largeUrl'])
                
            try:
                length = product_['detail']['data']['attributes'][0]['value']
            except:
                length =''
            try:
                width = product_['detail']['data']['attributes'][1]['value']
            except:
                width = ''
            try:
                unit = product_['detail']['data']['attributes'][0]['unit']
            except:
                unit = ''
            measurement = {"length": length, "width": width, "unit": unit}
             
  
            products.append({
                "product_id":productId,
                "product_name": product_name,
                "brand": brand,
                "category": category,
                "price": price,
                "measurement": dict(measurement),
                "unit_count":unitCount,
                "rating": rating,
                "rating_count":totalRating,
                "catgroy_path": catgroy_path,
                "product_url":href ,
                "image_url": list(dict.fromkeys(image_url)),
                "description":description
            })

        return products

    def scrape_keyword(self, category):
        self.logger.log_category_start(category)
        page = 1
        while True:
            url = f"https://www.manomano.fr/recherche/{category}?page={page}"
            self.logger.log_page_scraping(page, url, 0)
            response = Request().get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            products = self.product_parser(soup, category)

            if not products:
                self.logger.log_info(f"No more products found for {category} on page {page}")
                break
            
            # Append products incrementally to session files
            self.append_products_incrementally(products)
            self.all_products.extend(products)
            self.logger.log_page_scraping(page, url, len(products))
            page += 1
        
        # Log category completion
        category_products = [p for p in self.all_products if p.get('category') == category]
        self.logger.log_category_end(category, len(category_products))

    def run(self, categories):
        self.logger.log_scraping_start(categories)
        
        for category in categories:
            try:
                self.scrape_keyword(category)
            except Exception as e:
                self.logger.log_error(e, f"scraping category '{category}'")
        
        # Calculate duration and log completion
        duration = (datetime.now() - self.start_time).total_seconds()
        self.logger.log_scraping_end(len(self.all_products), duration)
        
        # Data is already saved incrementally, no need for final save
        self.logger.log_success(f"Scraping completed. Total products: {len(self.all_products)}")
        
        return self.all_products


if __name__ == "__main__":
    categories = ["Carrelage", "Éviers", "Toilettes", "Peinture", "Vanités", "Douches"]
    scraper = ManomanoScraper()
    scraper.run(categories)
