from bs4 import BeautifulSoup
import json
import csv, time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
from botasaurus.request import Request
from urllib.parse import urljoin
from datetime import datetime
from utils.logger import get_logger, get_output_manager


class LeroymerlinScraper:

    def __init__(self):
        self.payload = {}
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'priority': 'u=1, i',
            'resourcepath': '/search',
            'sec-ch-device-memory': '8',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-arch': '"x86"',
            'sec-ch-ua-full-version-list': '"Not;A=Brand";v="99.0.0.0", "Google Chrome";v="139.0.7258.67", "Chromium";v="139.0.7258.67"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        }
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
        # Proxy pool (round-robin)
        self.proxy_credentials_list = [
            {"host": "1.2.3.4", "port": "1234", "user": "vivek", "password": "vivek"},
            {"host": "5.6.7.8", "port": "1234", "user": "vivek", "password": "vivek"},
        ]
        self._proxy_index = 0
        
        # Initialize professional logging and output management
        self.logger = get_logger("leroymerlin")
        self.output_manager = get_output_manager()
        self.start_time = datetime.now()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize session files for incremental saving
        self.json_filepath, self.csv_filepath = self.output_manager.initialize_session_files("leroymerlin", self.session_id)
        self.logger.log_info(f"Initialized session files: {self.json_filepath}, {self.csv_filepath}")

    def _next_proxies(self):
        if not self.proxy_credentials_list:
            return None
        cred = self.proxy_credentials_list[self._proxy_index % len(self.proxy_credentials_list)]
        self._proxy_index += 1
        proxy_url = f"http://{cred['user']}:{cred['password']}@{cred['host']}:{cred['port']}"
        return {"http": proxy_url, "https": proxy_url}

    def save_to_json(self):
        """Save all collected products to JSON and CSV files."""
        try:
            # Save JSON file
            json_filepath = self.output_manager.save_scraper_data_session("leroymerlin", self.all_products, self.session_id)
            self.logger.log_success(f"Saved {len(self.all_products)} products to JSON: {json_filepath}")
            
            # Save CSV file
            csv_filepath = self.output_manager.save_scraper_data_csv("leroymerlin", self.all_products, self.session_id)
            self.logger.log_success(f"Saved {len(self.all_products)} products to CSV: {csv_filepath}")
        except Exception as e:
            self.logger.log_error(e, "save_to_json")

    def append_products_incrementally(self, products):
        """Append products to session files incrementally."""
        if products:
            try:
                self.output_manager.append_products_to_session("leroymerlin", products, self.session_id)
                self.logger.log_success(f"Appended {len(products)} products to session files")
            except Exception as e:
                self.logger.log_error(e, "append_products_incrementally")

    def product_parser(self, soup, keyword):
        try:
            products = []
            for tag in soup.find_all("script", {"type": "application/json", "class": "dataTms"}):
                text = (tag.string or tag.get_text() or "").strip()
                if not text:
                    continue
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    continue

                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict) and item.get("name") == "cdl_products_list":

                        try:    
                            data = items
                            for j_data in data[0]['value']:
                                product_dict = {}
                                try:
                                    product_dict["product_id"] = j_data["sku"]
                                except:
                                    product_dict["product_id"] = ''

                                try:
                                    product_dict["product_name"] = j_data['name']
                                except:
                                    product_dict["product_name"] = ''
                                
                                try:
                                    product_dict["brand"] = j_data['brand']
                                except:
                                    product_dict["brand"] = ''

                                product_dict["category"] = keyword
                                
                                price = {}
                                try:
                                    price["price"] = j_data["offer"]['unitprice_ati']
                                except:
                                    price["price"] = ''
                                try:
                                    price["original_price"] = j_data["offer"]['initial_price']
                                except:
                                    price["original_price"] = ''

                                price["unit_measurement"] = {"price": "", "unit": ""}

                                try:
                                    product_url = "https://www.leroymerlin.fr" + j_data['url']

                                    in_response = Request().get(url=product_url, headers=self.headers, data=self.payload)
                                    in_soup = BeautifulSoup(in_response.text, 'html.parser')

                                    measurement = {"length": "", "width": "", "unit": "" }

                                    # Extract width (Largeur)
                                    try:
                                        th_tag = in_soup.find("th", string=lambda text: text and text.strip().lower() == "Largeur (en cm)")
                                        if th_tag:
                                            td_tag = th_tag.find_next("td")
                                            if td_tag:
                                                measurement["width"] = td_tag.get_text(strip=True)
                                    except:
                                        pass

                                    try:
                                        th_tag = in_soup.find("th", string=lambda text: text and text.strip().lower() == "Hauteur (en cm)")
                                        if th_tag:
                                            td_tag = th_tag.find_next("td")
                                            if td_tag:
                                                measurement["length"] = td_tag.get_text(strip=True)
                                                measurement["unit"] = "cm"
                                    except:
                                        pass

                                    try:
                                        prod = in_soup.find('script', {'id':'jsonld_PRODUCT'}).text.strip()
                                        j_prod = json.loads(prod)
                                        try:
                                            price["currency"] = j_prod[0]["offers"]["priceCurrency"]
                                        except:
                                            price["currency"] = ""
                                        product_dict["price"] = price
                                        product_dict["measurement"] = measurement
                                        product_dict["unit_count"] = ""
                                        
                                        try:
                                            product_dict["rating"] = j_prod[0]["aggregateRating"]["ratingValue"]
                                            product_dict["rating_count"] = j_prod[0]["aggregateRating"]["reviewCount"]
                                        except:
                                            product_dict["rating"] = ""
                                            product_dict["rating_count"] = ""

                                        try:
                                            cate_path_ = []
                                            cate_path = in_soup.find('script', {'id':'jsonld_BREADCRUMB'}).text.strip()
                                            j_cate = json.loads(cate_path)
                                            for path in j_cate["itemListElement"]:
                                                cate_path_.append(path["item"]["name"])
                                            cate_path_str = " > ".join(cate_path_)            
                                            product_dict["category_path"] = cate_path_str
                                        except:
                                            product_dict["category_path"] = ""

                                        product_dict["product_url"] = product_url

                                        try:
                                            div_thumbnails = in_soup.find("div", class_="m-nav-thumbnails js-nav-thumbnails mu-pt-100")
                                            image_urls = []
                                            if div_thumbnails:
                                                imgs = div_thumbnails.find_all("img")
                                                for img in imgs:
                                                    url = img.get("data-src").split('?')[0] or img.get("src").split('?')[0]
                                                    if url:
                                                        image_urls.append(url)
                                            product_dict["image_url"] = image_urls
                                        except:
                                            product_dict["image_url"] = ""

                                        try:
                                            product_dict["description"] = j_prod[0]["description"]
                                        except:
                                            product_dict["description"] = ""

                                    except Exception as e:
                                        self.logger.log_error(f"product json error: ", {e})

                                except Exception as e:
                                    self.logger.log_error(f"❌ Error in product_url: {e}")
                                
                                products.append(product_dict)
                        except json.JSONDecodeError as e:
                            self.logger.log_error("JSON decoding failed:", e)

        except Exception as e:
            self.logger.log_error(e, "product JSON decoding")

        return products
    
    
    def scrape_category_page(self, url):
        self.logger.log_info(f"Fetching category page: {url}")
        response = self.session.get(url, headers=self.headers, timeout=self.request_timeout_seconds, proxies=self._next_proxies())
        if response.status_code != 200:
            self.logger.log_info(f"Failed to fetch {url}, status code {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        # Find all <a> with the class you mentioned
        links = soup.find_all("a", class_="l-childrencategories-item-designation__link")
        
        full_urls = []
        for a in links:
            href = a.get("href")
            if href:
                # Join relative URL with base URL
                full_url = urljoin("https://www.leroymerlin.fr", href)
                full_urls.append(full_url)

        return full_urls

    def scrape_keyword_from_url(self, url, keyword):
        page = 1
        while True:
            # Append pagination param if needed; adjust URL accordingly if required
            paged_url = f"{url}?p={page}" if "?" not in url else f"{url}&p={page}"
            self.logger.log_info(f"📄 Fetching: {paged_url}")

            response = self.session.get(
                paged_url,
                headers=self.headers,
                timeout=self.request_timeout_seconds,
                proxies=self._next_proxies(),
            )

            if response.status_code != 200:
                break

            soup = BeautifulSoup(response.text, "html.parser")

            is_last_page = False
            nav = soup.find("nav", class_="mc-pagination")
            if nav:
                try:
                    current = int((nav.get("data-current") or "0").strip())
                    max_page = int((nav.get("data-max-page") or "0").strip())
                    next_btn = nav.select_one("a.js-next")
                    next_disabled = bool(next_btn and "is-disabled" in (next_btn.get("class") or []))
                    is_last_page = (current >= max_page) or next_disabled
                except Exception:
                    is_last_page = False

            products = self.product_parser(soup, keyword)
            if not products:
                break

            self.all_products.extend(products)
            self.append_products_incrementally(products) # Incrementally save products

            if is_last_page:
                break
            page += 1


    def scrape_keyword(self, keyword):
        self.logger.log_category_start(keyword)
        
        page = 1
        while True:
            search_url = f"https://www.leroymerlin.fr/search-product/services/searchproducts?q={keyword}&p={page}"
            self.logger.log_page_scraping(page, search_url, 0)
            
            response = self.session.get(
                search_url,
                headers=self.headers,   
                timeout=self.request_timeout_seconds,
                proxies=self._next_proxies(),
            )
            
            if response.status_code != 200:
                self.logger.log_warning(f"Failed to fetch page {page}, status code: {response.status_code}")
                break

            soup = BeautifulSoup(response.text, "html.parser")

            is_last_page = False
            nav = soup.find("nav", class_="mc-pagination")
            if nav:
                try:
                    current = int((nav.get("data-current") or "0").strip())
                    max_page = int((nav.get("data-max-page") or "0").strip())
                    next_btn = nav.select_one("a.js-next")
                    next_disabled = bool(next_btn and "is-disabled" in (next_btn.get("class") or []))

                    # Stop if current >= max_page or if the next button is disabled
                    is_last_page = (current >= max_page) or next_disabled
                except Exception:
                    is_last_page = False  # fall back to products-empty check

            products = self.product_parser(soup, keyword)
            if not products:
                self.logger.log_info(f"No more products found on page {page}")
                break

            self.all_products.extend(products)
            self.append_products_incrementally(products) # Incrementally save products
            self.logger.log_page_scraping(page, search_url, len(products))

            if is_last_page:
                break

            page += 1
        
        # Log category completion
        category_products = [p for p in self.all_products if p.get('category') == keyword]
        self.logger.log_category_end(keyword, len(category_products))

    def run(self, keywords):
        self.logger.log_scraping_start(keywords)
        
        base_category_urls = {
            "Douches": "https://www.leroymerlin.fr/produits/salle-de-bains/douche/",
            "Carrelage": "https://www.leroymerlin.fr/produits/revetement-sol-et-mur/carrelage/?src=cat&query=Carrelage"
        }

        for kw in keywords:
            try:
                if kw in base_category_urls:
                    category_links = self.scrape_category_page(base_category_urls[kw])
                    for link in category_links:
                        self.scrape_keyword_from_url(link, kw)
                else:
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
    scraper = LeroymerlinScraper()
    keywords = ["Peinture", "Lavabos", "Toilettes", "Meubles-lavabos", "Douches", "Carrelage"] # "Douches", "Carrelage"
    scraper.run(keywords)