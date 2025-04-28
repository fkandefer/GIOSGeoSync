import requests
import json
from sys import argv
from arcgis.gis import GIS
from arcgis.features import Feature
GIOS_BASE_URL = "https://api.gios.gov.pl/pjp-api/rest"

# Funkcja do pobierania stacji
def get_stations():
    response = requests.get(f"{GIOS_BASE_URL}/station/findAll")
    response.raise_for_status()
    return response.json()


# Funkcja do pobierania czujników
def get_sensors(station_id):
    response = requests.get(f"{GIOS_BASE_URL}/station/sensors/{station_id}")
    response.raise_for_status()
    return response.json()


# Funkcja do pobierania danych z czujnika
def get_sensor_data(sensor_id):
    response = requests.get(f"{GIOS_BASE_URL}/data/getData/{sensor_id}")
    response.raise_for_status()
    return response.json()


# Funkcja do generowania GeoJSON
def generate_geojson():
    stations = get_stations()
    features = []

    for station in stations:
        station_id = station["id"]
        station_coords = (station["gegrLat"], station["gegrLon"])

        # Pobierz wszystkie dane stacji jako właściwości
        properties = {key: station[key] for key in station if key not in ["gegrLat", "gegrLon"]}
        properties["stationId"] = station_id

        # Dodaj współrzędne geograficzne
        properties["esrignss_latitude"] = float(station_coords[0])
        properties["esrignss_longitude"] = float(station_coords[1])

        try:
            # Pobierz dane z czujników
            sensors = get_sensors(station_id)
            for sensor in sensors:
                param_code = sensor['param']['paramCode']
                if param_code in ["PM10", "PM2.5", "CO"]:
                    safe_param_code = param_code.replace(".", "_")

                    sensor_id = sensor["id"]
                    try:
                        data = get_sensor_data(sensor_id)
                        values = data.get("values", [])

                        # Znajdź ostatni pomiar
                        last_measurement = next((v for v in values if v["value"] is not None), None)
                        if last_measurement:
                            properties[f"{safe_param_code}_value"] = last_measurement["value"]
                            properties[f"{safe_param_code}_date"] = last_measurement["date"]
                    except requests.exceptions.RequestException as e:
                        print(f"Błąd pobierania danych z czujnika {sensor_id}: {e}")
                        continue  # Przechodzimy do następnego czujnika

        except requests.exceptions.RequestException as e:
            print(f"Błąd pobierania czujników dla stacji {station_id}: {e}")
            continue  # Przechodzimy do następnej stacji

        # Utwórz funkcję GeoJSON
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(station_coords[1]), float(station_coords[0])],
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
            # print(f"Przetwarzanie punktu: {point_geometry}")
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