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
import geopandas as gpd
from shapely.geometry import Point, shape
from shapely.geometry import Point, Polygon
import pyproj
from pyproj import Transformer
# Initialize geolocator
geolocator = Nominatim(user_agent="geo_locator")

# Websites to scrape
# """
# TO DO:
# - Include neighborhood 
SITES = {
    # "inmobiliaria21": "https://www.century21mexico.com/",
    # "inmuebles24": "https://www.inmuebles24.com/"
    "mercadolibre": "https://inmuebles.mercadolibre.com.mx/casas/"
    # "facebook": "https://www.facebook.com/marketplace"
}
# Target cities in Chihuahua
STATE = "Chihuahua"
def mercado_libre_detail(url):
    # url = "https://casa.mercadolibre.com.mx/MLM-3404347540-aprovecha-hermosa-casa-en-venta-en-quintas-del-sol-chihuahua-_JM#polycard_client=search-nordic&position=1&search_layout=grid&type=item&tracking_id=b1588e4b-3ea2-46d0-b389-fd881b700ba2"
    sub_response = requests.get(f"{url}")
    item = BeautifulSoup(sub_response.text, "html.parser")                
    location_url = item.select_one(".ui-vip-location").select_one("img").get("src")
    lat_lon = location_url.split("center=")[1].split("&zoom")[0].split(",")[0].split("%2C")
    # ejemplo centro
    lon, lat = float(lat_lon[1]),  float(lat_lon[0]) 
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32613", always_xy=True)  # Adjust EPSG:32613 if needed
    point_projected = Point(transformer.transform(lon, lat))
    data = {
        "latitude": [float(lat)],
        "longitude": [float(lon)],
        "geometry": [point_projected ]
    }
    return data
# Function to scrape a single site
def scrape_site(site_url, city):
    results = []
    if "mercadolibre" in site_url:
        # Example: Simple request-based scraping
        for t in ["venta","renta"]:
            full_url = f"{site_url}{t}/{STATE}/{city}"
            response = requests.get(full_url)
            soup = BeautifulSoup(response.text, "html.parser")
            pagination = soup.select(".andes-pagination__button")
            if pagination == []:
                pagination = [1]
            for page in pagination: 
                if page == 1:
                    sub_site_url = full_url 
                else:
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
                        latitude = "None" 
                        longitude = "None" 
                        geometry = "None" 
                        image = listing.select_one(".poly-card__portada").select_one("img").get("data-src") 
                        for attribute in attributes:
                            if attribute:
                                if "construido" in attribute.text.strip() or "terreno" in attribute.text.strip():
                                    contruction_area = attribute.text.strip()
                                elif "mara" in attribute.text.strip():
                                    bedrooms = attribute.text.strip()
                                else:
                                    bathrooms = attribute.text.strip()
                        mercado_libre_detail = mercado_libre_detail(f"{link}")
                        if mercado_libre_detail:
                            latitude = mercado_libre_detail["latitude"]
                            longitude = mercado_libre_detail["longitude"]
                            geometry = mercado_libre_detail["geometry"]
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
                                "land_area": land_area,
                                "latitude" : latitude, 
                                "longitude" : longitude, 
                                "geometry" : geometry 
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
        cities = ["Guadalajara", "Tlaquepaque", "Tonala", "Zapopan", "El Salto", "Tlajomulco"]
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

def mergeChihNeighborhoods(locations_df):
    zipshape = zipfile.ZipFile(open(r'.\\data\\080190001_ColoniasyFraccionamientos_2016.zip', 'rb'))
    cpg_file, dbf_file, prj_file, sbn_file, sbx_file, shp_file, xml_file, shx_file = zipshape.namelist()
    features = shapefile.Reader(
        shp=zipshape.open(shp_file),
        shx=zipshape.open(shx_file),
        dbf=zipshape.open(dbf_file),
    )  
    shapes = features.shapes()  # Geometry data
    records = features.records()  # Attributes
    # Extract neighborhood names (Replace "NAME_FIELD" with the actual field name)
    neighborhoods_list = []
    for record, geom in zip(records, shapes):
        neighborhoods_list.append({
            "geometry": shape(geom),  
            "neighborhood": record["Nombre"]# Replace with correct field index or name
        })
    # # Convert to GeoDataFrame
    locations = gpd.GeoDataFrame(locations_df, geometry='geometry', crs="EPSG:32613")
    neighborhoods = gpd.GeoDataFrame(neighborhoods_list, geometry='geometry', crs="EPSG:32613")
    merged = gpd.sjoin(locations, neighborhoods, how="left", predicate="within")
    return merged
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
    df_venta = df[df['type'].str.contains('venta')]
    df_renta = df[df['type'].str.contains('renta')]
    print(len(df_venta))
    # df.to_json(f"{STATE}_real_estate.json", orient='records', lines=True)
    # save_to_json(scraped_data, f"{STATE}_real_estate.json")
    df_venta['price'] = df_venta['price'].str.replace('[A-Za-z]', '').str.replace(',', '').astype(int)
    df_grouped_by_city = df_venta.groupby('city').agg({'price': ['mean', 'min', 'max']},{'location': 'count'}).reset_index()
    df_chihuahua = df[df['city'].str.contains('Chihuahua')]
    df_chihuahua.to_csv(f"{STATE}_real_estate_chihuahua_city.csv", index=False)
    # link = "https://casa.mercadolibre.com.mx/MLM-3404347540-aprovecha-hermosa-casa-en-venta-en-quintas-del-sol-chihuahua-_JM#polycard_client=search-nordic&position=1&search_layout=grid&type=item&tracking_id=b1588e4b-3ea2-46d0-b389-fd881b700ba2"
    # mercado_libre_detail = mercado_libre_detail(link)
    # print(mercado_libre_detail)


   
    # print(features)
    # for feature in features:
    #     print(feature.record["Nombre"])
    # print(r.numRecords)










# Transform the point to projected coordinates