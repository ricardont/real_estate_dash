
const map = L.map('map').setView([28.67, -106.05], 12);

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '© OpenStreetMap contributors',
}).addTo(map);
// Style for state borders and regions
function style(feature) {
  return {
    fillColor: getColor(feature.properties.state_name),
    weight: 2,
    opacity: 1,
    color: '#0000FF', // Strong blue borders
    dashArray: '3',
    fillOpacity: 0.7
  };
}
var file = "./data/zonificacion_secundaria_2023_utm13n.zip";
        // Fetch the Shapefile from the server
fetch('./data/zonificacion_secundaria_2023_utm13n.zip')
    .then(response => response.arrayBuffer())
    .then(arrayBuffer => shp(arrayBuffer))
    .then(geojson => {
        L.geoJSON(geojson).addTo(map);
        map.fitBounds(L.geoJSON(geojson).getBounds());
    })
    .catch(error => console.error('Error loading Shapefile:', error));
// Color scale for regions
function getColor(region) {
  switch (region) {
    case 'Norte': return '#add8e6'; // Light blue
    case 'Occidente': return '#87CEFA'; // Sky blue
    case 'Centro-Norte': return '#4682B4'; // Steel blue
    case 'Centro': return '#4169E1'; // Royal blue
    case 'Sur-Este': return '#0000FF'; // Blue
    case 'Pacífico Sur': return '#1E90FF'; // Dodger blue
    case 'Bajío': return '#5F9EA0'; // Cadet blue
    case 'Golfo de México': return '#6495ED'; // Cornflower blue
    case 'Península de Yucatán': return '#00BFFF'; // Deep sky blue
    default: return '#B0C4DE'; // Light steel blue
  }
}

    // Add GeoJSON for Mexico states
const mexicoRegions = "https://raw.githubusercontent.com/ricardont/real_estate_dash/refs/heads/main/data/mexicoRegions.geojson"; 
const mexicoStates  = "https://raw.githubusercontent.com/ricardont/real_estate_dash/refs/heads/main/data/mexicoStates.geojson";
const chihState = "https://raw.githubusercontent.com/ricardont/real_estate_dash/refs/heads/main/data/chihState.geojson";
const chihStateLand = "https://raw.githubusercontent.com/ricardont/real_estate_dash/refs/heads/main/data/chihStateLand.geojson";
const chihZonePrim = "https://raw.githubusercontent.com/ricardont/real_estate_dash/refs/heads/main/data/chihuahuaZonePrim.geojson";
// fetch(chihStateLand)
//   .then(response => response.json())
//   .then(data => {
//     L.geoJson(data, {
//       style: style,
//       onEachFeature: function (feature, layer) {
//         layer.on({
//           click: function () {
//             map.fitBounds(layer.getBounds());
//           }
//         });
//       layer.bindPopup(`Zona:<b>${feature.properties.ZPAR_ZONA}</b><br>Clave Municipio: ${feature.properties.MUN_CLV}`);
//     }
//   }).addTo(map);
// });
  // L.geoJson(mexicoStatesConst, {
  //   style: style,
  //   onEachFeature: function (feature, layer) {
  //     layer.on({
  //       click: function () {
  //         map.fitBounds(layer.getBounds());
  //       }
  //     });
  //     layer.bindPopup(`<b>${feature.properties.state_name}</b><br>Region: ${feature.properties.reg_code}`);
  //   }
  // }).addTo(map);
// Add legend
const legend = L.control({ position: 'bottomright' });
legend.onAdd = function () {
  const div = L.DomUtil.create('div', 'legend');
  div.innerHTML += `<p><strong>Regions</strong></p>`;
  div.innerHTML += `<span style="background:#add8e6"></span> Norte<br>`;
  div.innerHTML += `<span style="background:#87CEFA"></span> Occidente<br>`;
  div.innerHTML += `<span style="background:#4682B4"></span> Centro-Norte<br>`;
  div.innerHTML += `<span style="background:#4169E1"></span> Centro<br>`;
  div.innerHTML += `<span style="background:#0000FF"></span> Sur-Este<br>`;
  div.innerHTML += `<span style="background:#1E90FF"></span> Pacífico Sur<br>`;
  div.innerHTML += `<span style="background:#5F9EA0"></span> Bajío<br>`;
  div.innerHTML += `<span style="background:#6495ED"></span> Golfo de México<br>`;
  div.innerHTML += `<span style="background:#00BFFF"></span> Península de Yucatán<br>`;
  return div;
};
legend.addTo(map)


// // Leaflet Map Setup
// document.addEventListener('DOMContentLoaded', function () {
//   const map = L.map('map').setView([30.6353, -106.0889], 6);

//   // Free map tiles from OpenStreetMap
//   L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
//     maxZoom: 19,
//     attribution: '© OpenStreetMap contributors',
//   }).addTo(map);

//   // Dummy Hotspot Data
//   const hotspots = [
//     { name: "Zona Centro", lat: 28.6353, lng: -106.0889, info: "High Demand" },
//     { name: "Delicias", lat: 28.2052, lng: -105.4701, info: "Medium Demand" },
//     { name: "Juárez", lat: 31.6904, lng: -106.4245, info: "Low Demand" },
//   ];

//   hotspots.forEach((hotspot) => {
//     L.marker([hotspot.lat, hotspot.lng])
//       .addTo(map)
//       .bindPopup(`<strong>${hotspot.name}</strong><br>${hotspot.info}`);
//   });
// });

// // Data Sources
// const dataSources = {
//   propertyPrices: "https://www.vivanuncios.com.mx/",
//   vacancyRates: "https://www.inegi.org.mx/",
//   demographicData: "https://datausa.io/profile/geo/chihuahua-mx/",
// };

// console.log("Data Sources for Integration:", dataSources);


