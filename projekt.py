import requests
import json
from sys import argv
from arcgis.gis import GIS
from arcgis.features import Feature

GIOS_BASE_URL = "https://api.gios.gov.pl/pjp-api/v1/rest"

# Nowe klucze zgodnie z nowym API
STATION_ID_KEY = "Identyfikator stacji"
LAT_KEY = "WGS84 φ N"
LON_KEY = "WGS84 λ E"
SENSOR_ID_KEY = "Identyfikator stanowiska"
SENSOR_CODE_KEY = "Wskaźnik - kod"
VALUE_KEY = "Wartość"
DATE_KEY = "Data"

# Funkcja do pobierania stacji
def get_stations():
    response = requests.get(f"{GIOS_BASE_URL}/station/findAll?size=500")
    response.raise_for_status()
    data = response.json()
    return data.get("Lista stacji pomiarowych", [])

# Funkcja do pobierania czujników
def get_sensors(station_id):
    response = requests.get(f"{GIOS_BASE_URL}/station/sensors/{station_id}")
    response.raise_for_status()
    data = response.json()
    return data.get("Lista stanowisk pomiarowych dla podanej stacji", [])

# Funkcja do pobierania danych z czujnika
def get_sensor_data(sensor_id):
    response = requests.get(f"{GIOS_BASE_URL}/data/getData/{sensor_id}")
    response.raise_for_status()
    data = response.json()
    return data.get("Lista danych pomiarowych", [])

# Funkcja do generowania GeoJSON
def generate_geojson():
    stations = get_stations()
    features = []

    for station in stations:
        station_id = station[STATION_ID_KEY]
        try:
            lat = float(station[LAT_KEY])
            lon = float(station[LON_KEY])
        except (KeyError, ValueError):
            continue

        # Przygotuj szkielet properties
        properties = {
            "CO_date": None,
            "CO_value": None,
            "PM10_date": None,
            "PM10_value": None,
            "PM2_5_date": None,
            "PM2_5_value": None,
            "esrignss_latitude": lat,
            "esrignss_longitude": lon,
            "OBJECTID": None,
            "stationId": station_id,
            "stationName": station.get("Nazwa stacji", "")
        }

        has_data = False
        try:
            sensors = get_sensors(station_id)
            for sensor in sensors:
                param_code = sensor[SENSOR_CODE_KEY]
                if param_code in ["PM10", "PM2.5", "CO"]:
                    safe_param_code = param_code.replace(".", "_")
                    sensor_id = sensor[SENSOR_ID_KEY]
                    try:
                        values = get_sensor_data(sensor_id)
                        last_measurement = next((v for v in values if v[VALUE_KEY] is not None), None)
                        if last_measurement:
                            properties[f"{safe_param_code}_value"] = last_measurement[VALUE_KEY]
                            properties[f"{safe_param_code}_date"] = last_measurement[DATE_KEY]
                            has_data = True
                    except requests.exceptions.RequestException as e:
                        print(f"Błąd pobierania danych z czujnika {sensor_id}: {e}")
                        continue
        except requests.exceptions.RequestException as e:
            print(f"Błąd pobierania czujników dla stacji {station_id}: {e}")
            continue

        if has_data:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": properties,
            })

    return {
        "type": "FeatureCollection",
        "features": features,
    }

# Funkcja do aktualizacji danych w ArcGIS Online
def update_arcgis_layer(geojson, layer_id, gis):
    # Pobierz warstwę
    layer = gis.content.get(layer_id).layers[0]

    # Konwersja GeoJSON na listę obiektów Feature
    features = []
    for feature in geojson["features"]:
        geometry = feature["geometry"]
        if geometry["type"] == "Point":
            point_geometry = {"x": geometry["coordinates"][0],
                              "y": geometry["coordinates"][1],
                              "spatialReference": {"wkid": 4326}}
            features.append(
                Feature(geometry=point_geometry, attributes=feature["properties"]))
        else:
            print(f"Nieobsługiwana geometria: {geometry['type']}")

    # Aktualizacja warstwy
    result = layer.edit_features(deletes=None, adds=features)

    # Logowanie wyniku
    # if "addResults" in result:
    #     print(f"Zaktualizowano warstwę {layer_id}. Dodano {len(result['addResults'])} obiektów.")
    # else:
    #     print(f"Nie udało się zaktualizować warstwy {layer_id}. Wynik: {result}")


def main():
    if len(argv) > 1 and argv[1] == "--geojson":
        geojson = generate_geojson()
        print(json.dumps(geojson, ensure_ascii=False, indent=2))
        return

    config = json.loads(argv[1])

    ARC_GIS_URL = config["arcgis_url"]
    ARC_GIS_USERNAME = config["arcgis_username"]
    ARC_GIS_PASSWORD = config["arcgis_password"]
    LAYER_ID = config["layer_id"]
    # 1. Pobierz dane z API GIOŚ i wygeneruj GeoJSON
    geojson = generate_geojson()

    # 2. Połącz się z ArcGIS Online
    gis = GIS(ARC_GIS_URL, ARC_GIS_USERNAME, ARC_GIS_PASSWORD)

    # 3. Zaktualizuj warstwę
    update_arcgis_layer(geojson, LAYER_ID, gis)
    # print(json.dumps(geojson, indent=2))


if __name__ == "__main__":
    main()