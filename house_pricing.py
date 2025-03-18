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
from tqdm import tqdm 
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
def scrape_mercadolibre_detail(url):
    print("Scraping detail...")
    print(url)
    sub_response = requests.get(f"{url}")
    item = BeautifulSoup(sub_response.text, "html.parser") 
    # map_url = "center=0.000000%2C0.000000&zoom=15"
    map_url = item.find("img", src=lambda x: x and "/maps.googleapis.com" in x)
    if map_url is None and item.select_one("#root-app > div.ui-vip-core > div.ui-pdp-container.ui-pdp-container--pdp").select_one("#ui-pdp-main-container > div.ui-pdp-container__col.col-2.ui-pdp-container--column-left.pb-40 > div.ui-pdp-container__col.col-1.ui-vip-core-container--content-left").select_one("#ui-vip-location__map") is not None:
        map_url = item.select_one("#root-app > div.ui-vip-core > div.ui-pdp-container.ui-pdp-container--pdp").select_one("#ui-pdp-main-container > div.ui-pdp-container__col.col-2.ui-pdp-container--column-left.pb-40 > div.ui-pdp-container__col.col-1.ui-vip-core-container--content-left").select_one("#ui-vip-location__map").get("src")  
    if map_url is None and  item.select_one(".ui-vip-location") is not None:
        map_url = item.select_one(".ui-vip-location").select_one("img")
    if map_url is not None:
        lat_lon = map_url.get("src").split("center=")[1].split("&zoom")[0].split(",")[0].split("%2C")
        # ejemplo centro
        lon, lat = float(lat_lon[1]),  float(lat_lon[0]) 
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:32613", always_xy=True) 
        point_projected = Point(transformer.transform(lon, lat))
    else:
        lat = 0.000000
        lon = 0.000000
        point_projected = Point(0.000000, 0.000000)
    data = {
        "latitude": lat,
        "longitude": lon,
        "geometry": point_projected
    }
    return data
# Function to scrape a single site
def scrap_mercadolibre(site_url, city):
    results = []
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
                    land_sqm = "None"
                    contruction_sqm = "None" 
                    latitude = "None" 
                    longitude = "None" 
                    geometry = "None" 
                    image = listing.select_one(".poly-card__portada").select_one("img").get("data-src") 
                    for attribute in attributes:
                        if attribute:
                            if "construido" in attribute.text.strip() or "terreno" in attribute.text.strip():
                                contruction_sqm = attribute.text.strip().split(" m")[0]
                            elif "mara" in attribute.text.strip():
                                bedrooms = attribute.text.strip()
                            else:
                                bathrooms = attribute.text.strip()
                    mercado_libre_detail = scrape_mercadolibre_detail(link)
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
                            "contruction_area":contruction_sqm,
                            "land_area": land_sqm,
                            "latitude" : latitude, 
                            "longitude" : longitude, 
                            "geometry" : geometry 
                        }
                    results.append(data)
    return results            

def scrape_site(site_url, city):
    if "mercadolibre" in site_url:
        return scrap_mercadolibre(site_url, city)
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
        return ''
# Scrape all sites for all cities
def scrap_by_city():
    all_data = []
    # cities = ["Chihuahua", "Juarez", "Delicias", "Cuauhtémoc", "Hidalgo del Parral"]
    cities = ["Chihuahua"]
    if STATE == "Jalisco":
        cities = ["Guadalajara", "Tlaquepaque", "Tonala", "Zapopan", "El Salto", "Tlajomulco"]
        neighborhoods = ["Providencia","Club","Bodega", "remate", "Cuarto", "Departamento", "Edificio", "Local", "Oficina","Terreno","Nave","Industrial","Otro"]
    for city in cities:
        for site, url in SITES.items():
            print(f"Scraping {site} for {city}...")
            data = scrape_site(url, city)
            all_data.extend(data)
    df = pd.DataFrame.from_dict(all_data)
    filter_values = ['Providencia','Club','Bodega', 'remate', 'Cuarto', 'Departamento', 'Edificio', 'Local', 'Oficina','Terreno','Nave','Industrial','Otro'] 
    filters = '|'.join(filter_values)
    df = df[~df['propert_type'].str.contains(filters, case=False, na=False)]
    filter_values = ['Providencia','Club','Bodega', 'remate', 'Departamento', 'Edificio', 'Local', 'Oficina','Terreno','Nave','Industrial','Otro'] 
    filters = '|'.join(filter_values)
    df = df[~df['title'].str.contains(filters, case=False, na=False)]          
    df['price'] = df['price'].str.replace('[A-Za-z]', '').str.replace(',', '').astype(int)
    df = merge_chih_neighborhoods(df)
    return df 

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

def merge_chih_neighborhoods(locations_df):
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
            "geometry_neighbor": shape(geom),  
            "geometry": shape(geom),
            "neighborhood": record["Nombre"]# Replace with correct field index or name
        })
    # # Convert to GeoDataFrame
    locations = gpd.GeoDataFrame(locations_df, geometry='geometry', crs="EPSG:32613")
    neighborhoods = gpd.GeoDataFrame(neighborhoods_list, geometry='geometry', crs="EPSG:32613")
    merged = gpd.sjoin(locations, neighborhoods, how="left", predicate="within")
    return merged

def retry_get_location_from_existing_df(df):
    df_without_location = df[df['latitude'] + df['longitude'] == 0.000000]
    print("Scraping again..." + str(len(df_without_location)) + " records")
    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        if row["latitude"] + row["longitude"] == 0 :  # Only scrape if non neighborhood
            location = scrape_mercadolibre_detail(row["link"])
            if location["latitude"] + location["longitude"] > 0.000000:
                # scrapping again succesfully 
                print(location["latitude"])
                print(location["longitude"])
                df.at[index, "latitude"] = location["latitude"]
                df.at[index, "longitude"] = location["latitude"]
# print(features)
# Main script
if __name__ == "__main__":
    scraped_data = scrap_by_city()
    df = scraped_data
    df_venta = df[df['type'].str.contains('venta')]
    df_renta = df[df['type'].str.contains('renta')]
    df.to_csv(f"{STATE}_real_estate.csv", index=False)
    df_grouped_by_city = df_venta.groupby('city').agg({'price': ['mean', 'min', 'max']},{'location': 'count'}).reset_index()
    df_chihuahua = df[df['city'].str.contains('Chihuahua')]
    df_grouped_by_neighborhood = df_venta.groupby('city').agg({'price': ['mean', 'min', 'max']},{'location': 'count'}).reset_index()
    df_chihuahua.to_csv(f"{STATE}_real_estate_chihuahua_city.csv", index=False)
