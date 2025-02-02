import json
import zipfile
from io import StringIO 
import shapefile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
from geopy.geocoders import Nominatim
import time
import pandas as pd
# Initialize geolocator
geolocator = Nominatim(user_agent="geo_locator")

# Websites to scrape

"""
TO DO:
- Include neighborhood 
- Include paginated scrapping
"""
SITES = {
    # "inmobiliaria21": "https://www.century21mexico.com/",
    # "inmuebles24": "https://www.inmuebles24.com/"
    "mercadolibre": "https://inmuebles.mercadolibre.com.mx/casas/"
    # "facebook": "https://www.facebook.com/marketplace"
}


# Target cities in Chihuahua
STATE = "Jalisco"
# Function to scrape a single site
def scrape_site(site_url, city):
    results = []
    if "mercadolibre" in site_url:
        # Example: Simple request-based scraping
        for t in ["venta", "renta"]:
            response = requests.get(f"{site_url}{t}/{STATE}/{city}")
            soup = BeautifulSoup(response.text, "html.parser")
            f = open(f"mercadilibre_raw_{t}.txt", "a")
            f.write(response.text)
            f.close()
            pagination =soup.select(".andes-pagination__button")
            for page in pagination: 
                sub_site_url = page.select_one("a").get("href")
                if sub_site_url != None:
                    sub_response = requests.get(f"{sub_site_url}")
                    sub_soup = BeautifulSoup(sub_response.text, "html.parser")                
                    for listing in sub_soup.select(".ui-search-result__wrapper"):
                        propert_type = listing.select_one(".poly-component__headline").text.strip()
                        title = listing.select_one(".poly-component__title-wrapper").select_one("a").text.strip()
                        link = listing.select_one(".poly-component__title-wrapper").select_one("a").get("href")
                        location = listing.select_one(".poly-component__location").text.strip()
                        price = listing.select_one(".poly-component__price").text.strip()
                        amount = listing.select_one(".poly-component__price").select_one(".poly-price__current").select_one(".andes-money-amount").select_one(".andes-money-amount__fraction").text.strip()
                        currency = listing.select_one(".poly-component__price").select_one(".poly-price__current").select_one(".andes-money-amount").select_one(".andes-money-amount__currency-symbol").text.strip()
                        attributes = listing.select_one(".poly-component__attributes-list").select_one(".poly-attributes-list").select(".poly-attributes-list__item")
                        bedrooms = "None" 
                        bathrooms = "None" 
                        land_area = "None"
                        contruction_area = "None" 
                        image = listing.select_one(".poly-card__portada").select_one("img").get("data-src") 
                        for attribute in attributes:
                            if attribute:
                                if "construido" in attribute.text.strip() or "terreno" in attribute.text.strip():
                                    contruction_area = attribute.text.strip()
                                elif "mara" in attribute.text.strip():
                                    bedrooms = attribute.text.strip()
                                else:
                                    bathrooms = attribute.text.strip()
                        data = {
                                "city": city,
                                "type": t,
                                "propert_type":propert_type,
                                "title": title,
                                "location": location,
                                "link": link,
                                "image": image,
                                "link": link, 
                                "price": amount,
                                "currency": currency,
                                "bedrooms": bedrooms,
                                "bathrooms": bathrooms,
                                "contruction_area":contruction_area,
                                "land_area": land_area
                            }
                        results.append(data)
            
    elif "facebook" in site_url:
        # Example: Dynamic scraping with Selenium
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get(f"{site_url}?q={city}")
        time.sleep(5)
        for listing in driver.find_elements(By.CSS_SELECTOR, ".x1n2onr6"):
            title = listing.text.split("\n")[0]
            price = listing.text.split("\n")[1]
            results.append({"title": title, "price": price, "city": city})
        driver.quit()
    return results

# Scrape all sites for all cities
def scrape_by_state():
    all_data = []
    cities = ["Chihuahua", "Juarez", "Delicias", "Cuauhtémoc", "Hidalgo del Parral"]
    if STATE == "Jalisco":
        cities = ["Guadalajara", "Tlaquepaque", "Tonala", "Zapopan", "El Salto"]
        neighborhoods = ["Providencia","Club","Bodega", "remate", "Cuarto", "Departamento", "Edificio", "Local", "Oficina","Terreno","Nave","Industrial","Otro"]
    for city in cities:
        for site, url in SITES.items():
            print(f"Scraping {site} for {city}...")
            data = scrape_site(url, city)
            all_data.extend(data)
    return all_data

# Add geolocation to each listing
def add_geolocation(listings):
    for listing in listings:
        location = geolocator.geocode(listing["location"])
        if location:
            listing["latitude"] = location.latitude
            listing["longitude"] = location.longitude
    return listings

# Save listings to JSON
def save_to_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Main script
if __name__ == "__main__":
    scraped_data = scrape_by_state()
    # data_with_geolocation = add_geolocation(scraped_data)
    
    filter_values = ['Providencia','Club','Bodega', 'remate', 'Cuarto', 'Departamento', 'Edificio', 'Local', 'Oficina','Terreno','Nave','Industrial','Otro'] 
    filters = '|'.join(filter_values)
    df = pd.DataFrame.from_dict(scraped_data)
    df = df[~df['propert_type'].str.contains(filters, case=False, na=False)]
    filter_values = ['Providencia','Club','Bodega', 'remate', 'Departamento', 'Edificio', 'Local', 'Oficina','Terreno','Nave','Industrial','Otro'] 
    filters = '|'.join(filter_values)
    df = df[~df['title'].str.contains(filters, case=False, na=False)]

            # - on property_type , filter "Terreno" "Nave Industrial", "Otro"
        # - on title , filter "Locales" "Nave Industrial"
    print(len(df))
    df.to_csv(f"{STATE}_real_estate.csv", index=False)
    df_venta= df[df['type'].str.contains('venta')]
    df_renta= df[df['type'].str.contains('renta')]
    print(len(df_venta))
    # df.to_json(f"{STATE}_real_estate.json", orient='records', lines=True)
    # save_to_json(scraped_data, f"{STATE}_real_estate.json")
    df_venta['price'] = df_venta['price'].str.replace('[A-Za-z]', '').str.replace(',', '').astype(int)
    df_grouped_by_city = df_venta.groupby('city').agg({'price': ['mean', 'min', 'max']},{'location': 'count'}).reset_index()
    print("Data saved to real_estate.json")
    print(df_grouped_by_city)

    zipshape = zipfile.ZipFile(open(r'.\\data\\080190001_ColoniasyFraccionamientos_2016.zip', 'rb'))
   
    cpg_file, dbf_file, prj_file, sbn_file, sbx_file, shp_file, xml_file, shx_file = zipshape.namelist()
    features = shapefile.Reader(
        shp=zipshape.open(shp_file),
        shx=zipshape.open(shx_file),
        dbf=zipshape.open(dbf_file),
    )  
    # print(features)
    # for feature in features:
    #     print(feature.record["Nombre"])
    # print(r.numRecords)