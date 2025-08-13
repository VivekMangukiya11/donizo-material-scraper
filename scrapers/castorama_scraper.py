import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from utils.logger import get_logger, get_output_manager


class CastoramaScraper:
    def __init__(self):
        self.payload = {}
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        }
        # Configure a requests Session with retry logic (5 attempts) for connection/read/status errors
        self.session = requests.Session()
        retry_strategy = Retry(
            total=5,
            connect=5,
            read=5,
            status=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.request_timeout_seconds = 30
        self.all_products = []
        
        # Initialize professional logging and output management
        self.logger = get_logger("castorama")
        self.output_manager = get_output_manager()
        self.start_time = datetime.now()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize session files for incremental saving
        self.json_filepath, self.csv_filepath = self.output_manager.initialize_session_files("castorama", self.session_id)
        self.logger.log_info(f"Initialized session files: {self.json_filepath}, {self.csv_filepath}")

    def save_to_json(self):
        """Save all collected products to JSON and CSV files."""
        try:
            # Save JSON file
            json_filepath = self.output_manager.save_scraper_data_session("castorama", self.all_products, self.session_id)
            self.logger.log_success(f"Saved {len(self.all_products)} products to JSON: {json_filepath}")
            
            # Save CSV file
            csv_filepath = self.output_manager.save_scraper_data_csv("castorama", self.all_products, self.session_id)
            self.logger.log_success(f"Saved {len(self.all_products)} products to CSV: {csv_filepath}")
        except Exception as e:
            self.logger.log_error(e, "save_to_json")

    def append_products_incrementally(self, products):
        """Append products to session files incrementally."""
        if products:
            try:
                self.output_manager.append_products_to_session("castorama", products, self.session_id)
                self.logger.log_success(f"Appended {len(products)} products to session files")
            except Exception as e:
                self.logger.log_error(e, "append_products_incrementally")

    def product_parser(self, soup, keyword):
        main_tag = soup.find("main", id="main-content")
        if not main_tag:
            return []

        products = []

        script_tag = main_tag.find("script", type="application/ld+json")
        if script_tag:
            try:
                data = json.loads(script_tag.string.strip())

                for j_data in data["itemListElement"]:
                    product_dict = {}
                    try:
                        product_dict["product_id"] = j_data["sku"]
                    except:
                        product_dict["product_id"] = ""

                    try:
                        product_dict["product_name"] = j_data["name"]
                    except:
                        product_dict["product_name"] = ""

                    try:
                        product_url = j_data["url"]
                        
                        if product_url:
                            in_response = self.session.get(product_url, headers=self.headers, timeout=self.request_timeout_seconds)
                            in_soup = BeautifulSoup(in_response.text, "html.parser")

                            brand = ""
                            th_tag = in_soup.find("th", string=lambda text: text and text.strip().lower() == "marque")
                            if th_tag:
                                td_tag = th_tag.find_next("td")
                                if td_tag:
                                    brand = td_tag.get_text(strip=True)
                            product_dict["brand"] = brand

                            product_dict["category"] = keyword

                            price = {}
                            try:
                                price["price"] = j_data["offers"]["price"]
                            except:
                                price["price"] = ""

                            try:
                                s_tag = in_soup.find('span', {'data-testid': 'was-price'}).find('s')
                                if s_tag:
                                    price["original_price"] = s_tag.get_text(strip=True).split()[0]
                                else:
                                    price["original_price"] = j_data["offers"]["price"]
                            except:
                                price["original_price"] = j_data["offers"]["price"]

                            price["unit_price"] = ""
                            
                            try:
                                price["currency"] = j_data["offers"]["priceCurrency"]
                            except:
                                price["currency"] = ""

                            product_dict["price"] = price

                            measurement = {}
                            def split_value_unit(text):
                                text = text.strip().replace("\xa0", " ")  # remove non-breaking spaces
                                for unit in ["cm", "mm", "m", "in", "ft"]:
                                    if unit in text:
                                        return text.replace(unit, "").strip(), unit
                                return text, None

                            # width
                            th = in_soup.find("th", string=lambda t: t and "largeur" in t.lower())
                            if th:
                                td = th.find_next("td")
                                if td:
                                    measurement["width"], unit = split_value_unit(td.get_text())
                                    
                            # length
                            th = in_soup.find("th", string=lambda t: t and "hauteur" in t.lower())
                            if th:
                                td = th.find_next("td")
                                if td:
                                    measurement["length"], _ = split_value_unit(td.get_text())
                            measurement["unit"] = unit
                            product_dict["measurement"] = measurement

                            try:
                                th_tag = in_soup.find("th", string=lambda text: text and text.strip().lower() == "Surface de couverture")
                                td_tag = th_tag.find_next("td")
                                product_dict["unit_count"] = td_tag.get_text(strip=True)
                            except:
                                product_dict["unit_count"] = ""

                            try:
                                product_dict["rating"] = j_data["aggregateRating"]["ratingValue"]
                            except:
                                product_dict["rating"] = ""

                            try:
                                product_dict["totalRating"] = j_data["aggregateRating"]["reviewCount"]
                            except:
                                product_dict["totalRating"] = ""

                            try:
                                for tag in in_soup.find_all("script", {"type": "application/ld+json"}):
                                    text = (tag.string or tag.get_text() or "").strip()
                                    if not text:
                                        continue
                                    try:
                                        data = json.loads(text)
                                    except json.JSONDecodeError:
                                        continue

                                    items = data if isinstance(data, list) else [data]
                                    for item in items:
                                        if isinstance(item, dict) and item.get("@type") == "BreadcrumbList":
                                            try:
                                                cate_path = []
                                                for path in item["itemListElement"]:
                                                    cate_path.append(path["name"])
                                                cate_path_str = " > ".join(cate_path)            
                                                product_dict["category_path"] = cate_path_str
                                            except:
                                                product_dict["category_path"] = ""

                                    product_dict["product_url"] = product_url

                                    items = data if isinstance(data, list) else [data]
                                    for item in items:
                                        if isinstance(item, dict) and item.get("@type") == "Product":
                                            try:
                                                product_dict["availability"] = item["offers"]["availability"]
                                            except:
                                                product_dict["availability"] = ""

                                            try:
                                                image_list = []
                                                for img in item["image"]:
                                                    image_list.append(img.split('?$')[0])
                                                product_dict["image_url"] = image_list
                                            except:
                                                product_dict["image_url"] = []

                            except Exception as e:
                                self.logger.log_error(e, "product JSON decoding")
                    except:
                        product_url = ""

                    try:
                        raw_desc = j_data.get("description", "")
                        clean_desc = re.sub(r"\s+", " ", raw_desc)
                        product_dict["description"] = clean_desc.strip()
                    except:
                        product_dict["description"] = ""
                    
                    products.append(product_dict)

            except json.JSONDecodeError as e:
                self.logger.log_error(e, "JSON decoding")
        return products

    def get_subcategories(self, category_url):
        """Fetch subcategory links from a category page."""
        sub_urls = []
        r = self.session.get(category_url, headers=self.headers, timeout=self.request_timeout_seconds)
        if r.status_code != 200:
            return sub_urls

        soup = BeautifulSoup(r.text, "html.parser")

        if 'peinture' in category_url:
            script_tag = soup.find("script", string=lambda t: t and "window.__data" in t)
            if script_tag:
                match = re.search(r"window\.__data\s*=\s*(\{.*\});?", script_tag.string, re.DOTALL)
                if match:
                    json_str = match.group(1).replace('undefined','""')

                    j_data = json.loads(json_str)
                    for json_data in j_data["category"]["data"]["attributes"]["categories"]:
                        product_lister_category = json_data.get("productListerCategory", "")
                        if product_lister_category is True or product_lister_category == "true":
                            sub_urls.append("https://www.castorama.fr" + json_data["htmlContentPath"])
        else:
            grids = soup.find_all("div", {"data-test-id": "grid-sections"})
            for grid in grids:
                for a in grid.find_all("a", href=True):
                    href = a["href"]
                    if href.startswith("/"):
                        sub_urls.append("https://www.castorama.fr" + href)
        return sub_urls

    def scrape_url_with_pagination(self, base_url, keyword):
        """Paginate through a given base URL and scrape products."""
        page = 1
        while True:
            url = f"{base_url}?page={page}"
            self.logger.log_page_scraping(page, url, 0)  # Will update with actual count
            
            response = self.session.get(url, headers=self.headers, timeout=self.request_timeout_seconds)
            if response.status_code != 200:
                self.logger.log_warning(f"Failed to fetch page {page}, status code: {response.status_code}")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            products = self.product_parser(soup, keyword)
            if not products:
                self.logger.log_info(f"No more products found on page {page}")
                break

            # Append products incrementally to session files
            self.append_products_incrementally(products)
            self.all_products.extend(products)
            self.logger.log_page_scraping(page, url, len(products))
            page += 1

    def scrape_keyword(self, keyword):
        """Handle either normal keyword search or category/subcategory scraping."""
        self.logger.log_category_start(keyword)
        
        category_urls = {
            "carrelage": "https://www.castorama.fr/carrelage-sol/carrelage-sol-et-mural/cat_id_3304.cat",
            "peinture": "https://www.castorama.fr/peinture/cat_id_3634.cat"
        }

        kw_lower = keyword.lower()
        if kw_lower in category_urls:
            sub_links = self.get_subcategories(category_urls[kw_lower])
            if not sub_links:  # no subcategories, scrape main category directly
                self.scrape_url_with_pagination(category_urls[kw_lower], keyword)
            else:
                for sub_url in sub_links:
                    self.scrape_url_with_pagination(sub_url, keyword)
        else:
            page = 1
            while True:
                search_url = f"https://www.castorama.fr/search?term={keyword}&page={page}"
                self.logger.log_page_scraping(page, search_url, 0)
                
                response = self.session.get(search_url, headers=self.headers, timeout=self.request_timeout_seconds)
                if response.status_code != 200:
                    self.logger.log_warning(f"Failed to fetch search page {page}, status code: {response.status_code}")
                    break

                soup = BeautifulSoup(response.text, "html.parser")
                products = self.product_parser(soup, keyword)
                if not products:
                    self.logger.log_info(f"No more products found on search page {page}")
                    break

                # Append products incrementally to session files
                self.append_products_incrementally(products)
                self.all_products.extend(products)
                self.logger.log_page_scraping(page, search_url, len(products))
                page += 1
        
        # Log category completion
        category_products = [p for p in self.all_products if p.get('category') == keyword]
        self.logger.log_category_end(keyword, len(category_products))

    def run(self, keywords):
        self.logger.log_scraping_start(keywords)
        
        for kw in keywords:
            try:
                self.scrape_keyword(kw)
            except Exception as e:
                self.logger.log_error(e, f"scraping keyword '{kw}'")
        
        # Calculate duration and log completion
        duration = (datetime.now() - self.start_time).total_seconds()
        self.logger.log_scraping_end(len(self.all_products), duration)
        
        # Data is already saved incrementally, no need for final save
        self.logger.log_success(f"Scraping completed. Total products: {len(self.all_products)}")
        
        return self.all_products

if __name__ == "__main__":
    scraper = CastoramaScraper()
    keywords = ["Peinture", "Lavabos", "Toilettes", "Meubles-lavabos", "Douches", "Carrelage"]
    scraper.run(keywords)