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
from shapely.geometry import Point, shape, Polygon
from shapely import  wkt
from shapely.wkt import  loads
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
def check_response(response):
    print(response.status_code)
    if not response or not response.content or response.status_code >= 400:
        return False
    return True
def scrape_mercadolibre_detail(url):
    sub_response = requests.get(f"{url}")
    lat = 0.000000
    lon = 0.000000
    point_projected = Point(0.000000, 0.000000)
    print(str(check_response(sub_response)))
    if check_response(sub_response):
        with open(f"{url[-10:]}_dtl_mlibre_scrape.txt", "w", encoding="utf-8") as file:
            file.write(sub_response.text)
        item = BeautifulSoup(sub_response.text, "html.parser") 
        url = url.split("?")[0]
        map_url = item.find("img", src=lambda x: x and "/maps.googleapis.com" in x)
        if map_url is None and item.select_one("#root-app > div.ui-vip-core > div.ui-pdp-container.ui-pdp-container--pdp").select_one("#ui-pdp-main-container > div.ui-pdp-container__col.col-2.ui-pdp-container--column-left.pb-40 > div.ui-pdp-container__col.col-1.ui-vip-core-container--content-left") and item.select_one("#root-app > div.ui-vip-core > div.ui-pdp-container.ui-pdp-container--pdp").select_one("#ui-pdp-main-container > div.ui-pdp-container__col.col-2.ui-pdp-container--column-left.pb-40 > div.ui-pdp-container__col.col-1.ui-vip-core-container--content-left").select_one("#ui-vip-location__map"):
            map_url = item.select_one("#root-app > div.ui-vip-core > div.ui-pdp-container.ui-pdp-container--pdp").select_one("#ui-pdp-main-container > div.ui-pdp-container__col.col-2.ui-pdp-container--column-left.pb-40 > div.ui-pdp-container__col.col-1.ui-vip-core-container--content-left").select_one("#ui-vip-location__map").get("src")  
        if map_url is None and  item.select_one(".ui-vip-location"):
            map_url = item.select_one(".ui-vip-location").get("src")
        if map_url:
            lat_lon = map_url.get("src").split("center=")[1].split("&zoom")[0].split(",")[0].split("%2C")
            lat = float(lat_lon[0]) 
            lon = float(lat_lon[1])  
            transformer = Transformer.from_crs("EPSG:4326", "EPSG:32613", always_xy=True) 
            point_projected = Point(transformer.transform(lon, lat))
    print(f"latitude:{lat}, longitude:{lon}, geometry:{point_projected}")
    return {"latitude": lat, "longitude": lon, "geometry": point_projected}
# Function to scrape a single site
def scrap_mercadolibre(site_url, city):
    results = []
    # Example: Simple request-based scraping
    for t in ["venta","renta"]:
        full_url = f"{site_url}{t}/{STATE}/{city}"
        response = requests.get(full_url)
        with open(f"{t}_{STATE}_{city}_mlibre_scrape.txt", "w", encoding="utf-8") as file:
            file.write(response.text)
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
                with open(f"{STATE}_{city}_{sub_site_url[-10:]}_mlibre_scrape.txt", "w", encoding="utf-8") as file:
                    file.write(sub_response.text)
                print("Scraping pagination...")
                print(sub_site_url[-10:])
                print(sub_site_url)
                sub_soup = BeautifulSoup(sub_response.text, "html.parser")   
                for listing in sub_soup.select(".ui-search-result__wrapper"):
                    if listing.select_one(".ui-search-item__group__element"):
                        propert_type = listing.select_one(".ui-search-item__group__element").text.strip()
                    elif listing.select_one(".poly-component__headline"):
                        propert_type = listing.select_one(".poly-component__headline").text.strip()
                    else:
                        propert_type = "No Type"
                    if listing.select_one(".poly-component__title-wrapper"):
                        title = listing.select_one(".poly-component__title-wrapper").select_one("a").text.strip()
                        link = listing.select_one(".poly-component__title-wrapper").select_one("a").get("href") 
                    elif listing.select_one(".ui-search-result__content-wrapper"):
                        title =  listing.select_one(".ui-search-result__content-wrapper").select_one("a").text.strip()  
                        link = listing.select_one(".ui-search-result__content-wrapper").select_one("a").get("href")
                    else:
                        title = "No Title"
                        link  = "No Link"
                    print(propert_type)
                    print("Title:")        
                    print(title)
                    print(link)
                    if listing.select_one(".ui-search-item__location-container-grid"):
                        location = listing.select_one(".ui-search-item__location-container-grid").text.strip()
                    elif listing.select_one(".poly-component__location"):
                        location = listing.select_one(".poly-component__location").text.strip()
                    else:
                        location = "No location"
                    print("Location:")        
                    print(location)
                    if listing.select_one(".ui-search-price"):
                        price = listing.select_one(".ui-search-price").select_one(".ui-search-price__second-line").select_one(".andes-money-amount").select_one(".andes-money-amount__fraction").text.strip()
                    elif listing.select_one(".poly-component__price").select_one(".poly-price__current").select_one(".andes-money-amount").select_one(".andes-money-amount__fraction"):
                        price = listing.select_one(".poly-component__price").select_one(".poly-price__current").select_one(".andes-money-amount").select_one(".andes-money-amount__fraction").text.strip()
                    else:
                        price = "No Price" 
                    print(price)
                    # currency = listing.select_one(".poly-component__price").select_one(".poly-price__current").select_one(".andes-money-amount").select_one(".andes-money-amount__currency-symbol").text.strip()
                    currency = "MXN"
                    if listing.select_one(".ui-search-item__attributes-container-grid"):
                        attributes = listing.select_one(".ui-search-item__attributes-container-grid").select_one(".ui-search-card-attributes").select(".ui-search-card-attributes__attribute")
                    elif listing.select_one(".poly-component__attributes-list"):
                        attributes = listing.select_one(".poly-component__attributes-list").select_one(".poly-attributes-list").select(".poly-attributes-list__item")
                    else:
                        attributes = None    
                    bedrooms = "None" 
                    bathrooms = "None" 
                    land_sqm = "None"
                    contruction_sqm = "None" 
                    latitude = "None" 
                    longitude = "None" 
                    geometry = "None" 
                    if listing.select_one(".andes-carousel-snapped__wrapper"):
                        image = listing.select_one(".andes-carousel-snapped__wrapper").select_one(".andes-carousel-snapped__slide").select_one(".ui-search-result-image__element").get("src")
                    elif listing.select_one(".poly-card__portada"):
                        image = listing.select_one(".poly-card__portada").select_one("img").get("data-src")         
                    else:
                        image = "no image"
                    print(image)
                    if attributes:
                        for attribute in attributes:
                            if "construido" in attribute.text.strip() or "terreno" in attribute.text.strip():
                                contruction_sqm = attribute.text.strip().split(" m")[0]
                            elif "mara" in attribute.text.strip():
                                bedrooms = attribute.text.strip().split(" ")[0]
                            else:
                                bathrooms = attribute.text.strip().split(" ")[0]
                    print("Scraping details...")
                    print(link)
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
                            "image": image,
                            "link": link, 
                            "price": price,
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
    results = []
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

def shape_zip_to_df(zip_file):
    zip_file = f"{zip_file}"
    zipshape = zipfile.ZipFile(open(r'{zip_file}', 'rb'))
    cpg_file, dbf_file, prj_file, sbn_file, sbx_file, shp_file, xml_file, shx_file = zipshape.namelist()
    features = shapefile.Reader(
        shp=zipshape.open(shp_file),
        shx=zipshape.open(shx_file),
        dbf=zipshape.open(dbf_file),
    )  
    shapes = features.shapes()  # Geometry data
    records = features.records()  # Attributes
    # Extract neighborhood names (Replace "NAME_FIELD" with the actual field name)
    list = []    
    shapes = features.shapes()  # Geometry data
    records = features.records()  # Attributes
    df = gpd.GeoDataFrame(list, geometry='geometry', crs="EPSG:32613")
    return df

def add_neighborhoods_to_df(locations_df):
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
            "neighborhood_geometry": shape(geom),
            "neighborhood": record["Nombre"]# Replace with correct field index or name
        })
    # # Convert to GeoDataFrame
    locations = gpd.GeoDataFrame(locations_df, geometry='geometry', crs="EPSG:32613")
    neighborhoods = gpd.GeoDataFrame(neighborhoods_list, geometry='geometry', crs="EPSG:32613")
    # Get all locations with and without neighborhoods
    locations_with_neighborhoods = gpd.sjoin(locations, neighborhoods, how="left", predicate="within")
    locations_without_neighborhoods = locations_with_neighborhoods[locations_with_neighborhoods['index_right'].isna()].copy()
    # Get all neighborhoods without locations
    neighborhoods_with_locations = gpd.sjoin(neighborhoods, locations, how="left", predicate="contains")
    neighborhoods_without_locations = neighborhoods_with_locations[neighborhoods_with_locations['index_right'].isna()].copy()
    merged = pd.concat([locations_with_neighborhoods, neighborhoods_without_locations], ignore_index=True)
    return locations_with_neighborhoods

def scrap_location_from_df(df):
    print("Scraping again..." + str(len(df)) + " records")
    affected_records = 0
    df_new = df.copy()
    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        location = scrape_mercadolibre_detail(row["link"])
        if location["latitude"] + location["longitude"] != 0.000000:
            # scrapping again succesfully 
            print(location["latitude"])
            print(location["longitude"])
            print(location["geometry"])
            df.at[index, "latitude"] = location["latitude"]
            df.at[index, "longitude"] = location["longitude"]
            df.at[index, "geometry"] = location["geometry"]
            affected_records += 1
        print("Scraped " + str(affected_records) + " records")        
    return df
def df_snippets(type="shapefile_convert", df=None, geometry_field="geometry", request_response="", text_response_file=""):
    output = None
    # df_new['geometry'] = df_new['geometry'].apply(wkt.loads)
    # gdf['geometry'] = gdf['geometry'].apply(loads)
    # df_new[df_new["geometry"] == Point(0, 0)]
    # df_without_location = df[ df.geometry == loads('POINT (0 0)') ]
    if type == "shapefile_convert":
        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        gdf.to_file("output.shp", driver="ESRI Shapefile")
        output = "converted"
    elif type == "convert_to_csv":
        df.to_csv("output.csv", index=False)
    elif type == "group_by_neighborhood":
        df  = df_chihuahua.groupby(["neighborhood","neighborhood_geometry"])["price"].mean().shift()
    elif type == "group_by_city":
        output = df.groupby('city').agg({'price': ['mean', 'min', 'max']},{'location': 'count'}).reset_index()
    elif type == "filter_city":
        df_chihuahua = df[df['city'].str.contains('Chihuahua')]
    elif type == "filter_city_venta":
        output = df[df['city'].str.contains('Chihuahua')]
    elif type == "group_by_neighborhood_avg":
        output  = df_chihuahua.groupby("neighborhood_geometry")["price"].mean()
    elif type == "add_geometry":
        # df['geometry_wkt'] = df[f"f{geometry_field}"].apply(wkt.loads)
        df['geometry_wkt'] = df[f"{geometry_field}"].apply(lambda x: x.wkt)
    elif type == 'save_response_in_text':
        with open(f"{text_response_file}", "w", encoding="utf-8") as file:
            file.write(request_response.text)
        return "response file saved ${text_response_file}"
    elif type == 'get_response_from_text':
        with open(f"{text_response_file}", "r", encoding="utf-8") as file:
            saved_content = file.read()
        return "response file saved {text_response_file}"
    else:
        print("No snippet found")    
    return output
def shapezip_to_df(zip_file):
    zipshape = zipfile.ZipFile(open(zip_file, 'rb'))
    cpg_file, dbf_file, prj_file, sbn_file, sbx_file, shp_file, xml_file, shx_file = zipshape.namelist()
    features = shapefile.Reader(
        shp=zipshape.open(shp_file),
        shx=zipshape.open(shx_file),
        dbf=zipshape.open(dbf_file),
    )  
    fields = [field[0] for field in features.fields[1:]]
    shapes = features.shapes()  # Geometry data
    records = features.records()  # Attributes
    list = []
    for sr, geom in zip(records, shapes):
        row = dict(zip(fields, sr))
        row["geometry"] = shape(geom)
        list.append(row)
    # # Convert to GeoDataFrame   
    df = gpd.GeoDataFrame(list, geometry='geometry', crs="EPSG:32613")
    return df

# Main script
if __name__ == "__main__":
    df = scrap_by_city()
    df_snippets("convert_to_csv", df)

    
