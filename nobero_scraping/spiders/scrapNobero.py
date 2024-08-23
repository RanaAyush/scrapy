import scrapy
from pathlib import Path
import json
import threading


class ScrapnoberoSpider(scrapy.Spider):
    name = "scrapNobero"
    allowed_domains = ["nobero.com"]
    start_urls = ["https://nobero.com/"]
    
    def start_requests(self):
        urls=[
        "https://nobero.com/collections/pick-printed-t-shirts",
        "https://nobero.com/collections/best-selling-co-ord-sets",
        "https://nobero.com/collections/fashion-joggers-men",
        "https://nobero.com/collections/mens-shorts-collection",
        "https://nobero.com/collections/plus-size-t-shirts",
        "https://nobero.com/collections/men-oversized-t-shirts"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_category)

    def parse_category(self, response):
        # print("\n\n parsing url 1\n\n")
        product_links = response.css('.product_link::attr(href)').getall()
        for link in product_links:
            yield scrapy.Request(url=response.urljoin(link), callback=self.parse_product)
        # yield scrapy.Request(url=response.urljoin(product_links[0]), callback=self.parse_product)

    def parse_product(self, response):
        # Scraping the required details from the CARD 
        # print("\n\nhello parsing category\n\n")
        price = self.extract_price(response.css('#variant-price spanclass::text').get())
        MRP = self.extract_price(response.css('#variant-compare-at-price spanclass::text').get())
        data = {
            "category": self.extract_category(response),
            "url": response.url,
            "title": response.css('h1.product-title::text').get().strip(),
            "price": price,
            "MRP": MRP,
            "fit": self.extract_detail(response, 'Fit'),
            "fabric": self.extract_detail(response, 'Fabric'),
            "neck": self.extract_detail(response, 'Neck'),
            "sleeve": self.extract_detail(response, 'Sleeve'),
            "pattern": self.extract_detail(response, 'Pattern'),
            "length": self.extract_detail(response, 'Length'),
            "description":self.extract_desc(response)
        }
        
        # Appending to JSON file
        self.save_to_json(data)

    def extract_category(self, response):
        title = response.css('h1.product-title::text').get().split()
        if("Joggers" in title):
            return "Joggers"
        elif("Oversized" in title and  "T-Shirts" in title):
            return "Oversized T-Shirts"
        elif("T-Shirts" in title):
             return "T-Shirts"
        elif("Co-ord" in title):
            return "Co-ord"
        elif("Shorts" in title):
            return "Shorts"
        else:
            return "Plus Size T-Shirts"
    
    def extract_desc(self,response):
        material = response.css("strong:contains('Material') + span::text").get()
        neck = response.css("strong:contains('Neck') + span::text").get()
        sleeves = response.css("strong:contains('Sleeves') + span::text").get()
        features = response.css("strong:contains('Features') ~ span::text").extract()
        origin = response.css("strong:contains('Origin') + span::text").get()
        wash_care = response.css("strong:contains('Wash Care') + span::text").get()
        note = response.css("strong:contains('Please Note') + span::text").get()

        # Clean up and process the features list
        features = [feature.strip('• ') for feature in features if '•' in feature]

        data = f"""
        Material: {material} 
        Neck: {neck} 
        Sleeves: {sleeves} 
        Features: {features}  
        Origin: {origin} 
        Wash Care: {wash_care} 
        Please Note: {note} 
        """
        return data


    def extract_price(self,price_text):
        if price_text:
            return int(price_text.replace('₹', '').replace(',', '').strip())
        return None

    def extract_skus(self, response):
        skus = []
        color_variants = response.css('div#product-variants div.color-variant')

        for variant in color_variants:
            color = variant.css('span.variant-color::text').get().strip()
            sizes = variant.css('div.size-variant span.variant-option::text').getall()
            sizes = [size.strip() for size in sizes]
            
            skus.append({
                "color": color,
                "sizes": sizes
            })
        return skus

    def extract_detail(self, response, detail_name):
        field = response.css("#product-metafields-container div h4::text").getall()
        value = response.css("#product-metafields-container div p::text").getall()
        for i,x in enumerate(field):
            if(x == detail_name):
                return value[i]

    def save_to_json(self, data):
        output_path = Path("nobero_products.json").absolute()

        lock = threading.Lock()

        with lock:
            if output_path.exists():
                with output_path.open("r+") as f:
                    content = json.load(f)
                    content.append(data)
                    f.seek(0)
                    json.dump(content, f, indent=4)
            else:
                with output_path.open("w") as f:
                    json.dump([data], f, indent=4)
