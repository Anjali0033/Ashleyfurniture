import requests
from lxml import html
import json
import pandas as pd
import time
import threading

session = requests.Session()
header = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
}
session.headers.update(header)


API_KEY = '5875c66d56298974fdc6fb8a70eef441'

def response_fetch(url, retries=2):
    try:
        r = session.get(url, timeout=10)
        if r.status_code == 200:
            return r
    except:
        pass

    for _ in range(retries):
        try:
            proxy_url = f"http://api.scraperapi.com/?api_key={API_KEY}&url={url}"
            r = session.get(proxy_url, timeout=5)
            if r.status_code == 200:
                print("response via Scraper API ")
                return r
        except:
            pass
        time.sleep(2)
    return None

Product_Data = []

def Detailspage_API_CALL(Category_name, Product_name, product_url, url):
    try:
        r = response_fetch(url)
        if r:
            data = json.loads(r.text)
            Product_Description = data.get('shortDescription', 'N/A')
            Product_Specifications = data.get('longDescription', 'N/A')

            Product_Data.append({
                "Product name": Product_name,
                "Category name": Category_name,
                "Product Description": Product_Description,
                "Product Specifications": Product_Specifications,
                "Product Url": product_url
            })
    except:
        pass
    return Product_Data

def Listpage(Category_name, url):

    print(f"Scraping category: {Category_name}")
    try:
        r = response_fetch(url)
        if r:
            tree = html.fromstring(r.text)

            for i in tree.xpath('//ul[@id="search-result-items"]//div[@class="product-tile"]'):
                product_url = ''.join(i.xpath('.//a[@class="thumb-link"]/@href')).strip()

                try:
                    Product_name = product_url.split('/')[-2].replace("_", " ").replace("%", " ")
                    Product_sku = product_url.split('/')[-1].replace(".html", "")
                    Detailspage_API = f'https://www.ashleyfurniture.com/on/demandware.store/Sites-Ashley-US-Site/default/Product-ProductDetailsJson?sku={Product_sku}'

                    print(f"  Scraping product: {Product_name}")
                    Detailspage_API_CALL(Category_name, Product_name, product_url, Detailspage_API)
                except:
                    pass
    except:
        pass

def Category_Page(url):
    print(f"Scraping category page: {url}")
    try:
        r = response_fetch(url)
        if r:
            tree = html.fromstring(r.text)
            Category_list = tree.xpath('//section[@class="svelte-1ds6vnh"]//li[@class="svelte-18j50z1"]')
            print("Total categories: ", len(Category_list))

            threads = []
            # thread to categories
            for cat_lst in Category_list:
                Category_name = ''.join(cat_lst.xpath('.//h3/text()')).strip()
                Category_url = ''.join(cat_lst.xpath('.//a/@href')).strip()
                if 'https:' not in Category_url:
                    Category_url = 'https://www.ashleyfurniture.com' + Category_url

                thread = threading.Thread(target=Listpage, args=(Category_name, Category_url))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

    except:
        pass

def save_to_excel(data, filename='products.xlsx'):
    try:
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"{e}")

Base_url = 'https://www.ashleyfurniture.com/'
Category_Page(Base_url)

save_to_excel(Product_Data)