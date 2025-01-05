import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

# Load the Mexico states GeoJSON
input_geojson_path = r"mexicoStates.geojson"  # Placeho

output_geojson_path = r"mexicoRegions.geojson"

# Regions definition: states grouped by region
regions = {
    "Norte": ["Baja California", "Baja California Sur", "Chihuahua", "Coahuila", "Nuevo León", "Sonora", "Tamaulipas"],
    "Occidente": ["Aguascalientes", "Colima", "Jalisco", "Michoacán", "Nayarit", "Zacatecas"],
    "Centro-Norte": ["Guanajuato", "Querétaro", "San Luis Potosí"],
    "Centro": ["Ciudad de México", "Estado de México", "Hidalgo", "Morelos", "Puebla", "Tlaxcala"],
    "Sur-Este": ["Campeche", "Chiapas", "Oaxaca", "Quintana Roo", "Tabasco", "Veracruz", "Yucatán"],
    "Pacífico Sur": ["Guerrero", "Oaxaca", "Chiapas"],
    "Bajío": ["Aguascalientes", "Guanajuato", "Querétaro", "San Luis Potosí"],
    "Golfo de México": ["Veracruz", "Tabasco", "Tamaulipas"],
    "Península de Yucatán": ["Campeche", "Quintana Roo", "Yucatán"],
}

# Assign colors for regions
region_colors = {
    "Norte": "#FF5733",
    "Occidente": "#FF8D1A",
    "Centro-Norte": "#FFC300",
    "Centro": "#FFE333",
    "Sur-Este": "#FFC0CB",
    "Pacífico Sur": "#FF6F61",
    "Bajío": "#FFD700",
    "Golfo de México": "#FFA07A",
    "Península de Yucatán": "#FF4500",
}

# Process the GeoJSON
with open(input_geojson_path, "r", encoding="utf-8") as file:
    mexico_states = json.load(file)

# Group states by region and merge their geometries
region_features = []
for region_name, states in regions.items():
    # Collect geometries for states in this region
    region_geometries = [
        shape(feature["geometry"])
        for feature in mexico_states["features"]
        if feature["properties"]["state_name"] in states
    ]
    
    # Merge geometries into a single polygon
    merged_geometry = unary_union(st_buffer(region_geometries))
    
    # Create a GeoJSON feature for the region
    region_features.append({
        "type": "Feature",
        "properties": {
            "name": region_name,
            "reg_code": region_name[:3].upper(),
            "color": region_colors.get(region_name, "#FFFFFF"),
        },
        "geometry": mapping(merged_geometry),
    })

# Create the final GeoJSON structure
regions_geojson = {
    "type": "FeatureCollection",
    "features": region_features,
}

# Save the new GeoJSON
with open(output_geojson_path, "w", encoding="utf-8") as output_file:
    json.dump(regions_geojson, output_file, indent=2)

output_geojson_path
