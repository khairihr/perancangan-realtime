import random
import math
import os
import time
import requests
import numpy as np
from flask import Flask, render_template, jsonify, send_from_directory

app = Flask(__name__)

# --- Tile Configuration ---
TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png' 
TILE_DIR = 'tiles_bojongsoang'  # Specific directory for Bojongsoang tiles

# --- Pre-Download Settings ---
MIN_ZOOM = 13  # Adjust zoom levels as needed
MAX_ZOOM = 16

# Coordinates for 6°58'21.4"S 107°38'04.5"E
CENTER_LATITUDE = -6.972611  # Convert degrees, minutes, seconds to decimal degrees
CENTER_LONGITUDE = 107.634583
TILE_SIZE = 256  # Standard tile size for most map providers
LATITUDE_RANGE = 0.02  # Adjust this to control the area covered
LONGITUDE_RANGE = 0.02

# --- Pre-Download Settings (Adjusted) ---
BOUNDS = [
    CENTER_LONGITUDE - LONGITUDE_RANGE, 
    CENTER_LATITUDE - LATITUDE_RANGE, 
    CENTER_LONGITUDE + LONGITUDE_RANGE, 
    CENTER_LATITUDE + LATITUDE_RANGE
]


def triangular(x, a, b, c):
    if b - a == 0:
        return np.where(np.isclose(x, a), 1, 0)
    elif c - b == 0:
        return np.where(np.isclose(x, c), 1, 0)
    else:
        return np.maximum(np.minimum((x - a) / (b - a), (c - x) / (c - b)), 0)

def trapezoidal(x, a, b, c, d):
    return max(min((x - a) / (b - a), 1, (d - x) / (d - c)), 0)

def fuzzy_and(a, b):
    return min(a, b)

def fuzzy_or(a, b):
    return max(a, b)

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def calculate_safe_distance(kecepatan, jarak, selisih_kecepatan):
    kecepatan_lambat = triangular(kecepatan, 0, 0, 50)
    kecepatan_sedang = triangular(kecepatan, 40, 80, 120)
    kecepatan_cepat = triangular(kecepatan, 110, 120, 120)
    jarak_dekat = triangular(jarak, 0, 0, 30)
    jarak_sedang = triangular(jarak, 20, 50, 80)
    jarak_jauh = triangular(jarak, 70, 100, 100)
    selisih_negatif = triangular(selisih_kecepatan, -50, -50, 0)
    selisih_nol = triangular(selisih_kecepatan, -10, 0, 10)
    selisih_positif = triangular(selisih_kecepatan, 0, 50, 50)
    jarak_aman_universe = np.arange(0, 101, 1)
    jarak_aman_pendek = triangular(jarak_aman_universe, 0, 0, 20)
    jarak_aman_sedang = triangular(jarak_aman_universe, 10, 50, 90)
    jarak_aman_panjang = triangular(jarak_aman_universe, 80, 100, 100)
    activation_pendek = fuzzy_and(fuzzy_and(kecepatan_lambat, jarak_dekat), selisih_negatif)
    activation_sedang = fuzzy_or(
        fuzzy_and(fuzzy_and(kecepatan_lambat, jarak_dekat), selisih_nol),
        fuzzy_and(fuzzy_and(kecepatan_lambat, jarak_sedang), selisih_nol)
    )
    activation_panjang = fuzzy_or(
        fuzzy_and(fuzzy_and(kecepatan_lambat, jarak_dekat), selisih_positif),
        fuzzy_and(fuzzy_and(kecepatan_lambat, jarak_sedang), selisih_positif)
    )
    pendek_centroid = np.average(jarak_aman_universe, weights=jarak_aman_pendek)
    sedang_centroid = np.average(jarak_aman_universe, weights=jarak_aman_sedang)
    panjang_centroid = np.average(jarak_aman_universe, weights=jarak_aman_panjang)
    numerator = activation_pendek * pendek_centroid + activation_sedang * sedang_centroid + activation_panjang * panjang_centroid
    denominator = activation_pendek + activation_sedang + activation_panjang
    if denominator == 0:
        return 50
    safe_distance = numerator / denominator
    return safe_distance

def get_dummy_positions():
    # Define the center coordinates (your specified location)
    center_lat = -6.972611  # 6°58'21.4"S
    center_lon = 107.634583  # 107°38'04.5"E

    user_vehicle = {
        'latitude': center_lat,
        'longitude': center_lon,
        'speed': random.uniform(0, 120),
        'time': '12:00:00'
    }

    other_vehicles = []
    for i in range(5):
        latitude = center_lat + random.uniform(-0.005, 0.005)
        longitude = center_lon + random.uniform(-0.005, 0.005)
        speed = random.uniform(0, 120)
        distance = calculate_distance(user_vehicle['latitude'], user_vehicle['longitude'], latitude, longitude)
        relative_speed = speed - user_vehicle['speed']
        safe_distance = calculate_safe_distance(user_vehicle['speed'], distance, relative_speed)
        other_vehicles.append({
            'latitude': latitude,
            'longitude': longitude,
            'speed': speed,
            'time': '12:00:00',
            'node': f'vehicle_{i}',
            'safe_distance': safe_distance,
            'distance': distance
        })

    return {
        'user': user_vehicle,
        'others': other_vehicles
    }

def download_tile(z, x, y):
    subdomains = ['a', 'b', 'c']
    for s in subdomains:
        url = TILE_URL.format(s=s, z=z, x=x, y=y)
        tile_path = os.path.join(TILE_DIR, str(z), str(x), f'{y}.png')
        if not os.path.exists(tile_path):
            os.makedirs(os.path.dirname(tile_path), exist_ok=True)
            try:
                response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
                response.raise_for_status()
                with open(tile_path, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded tile: {z}/{x}/{y}")
                return True
            except requests.exceptions.RequestException as e:
                print(f"Error downloading tile from subdomain '{s}': {e}")
                time.sleep(2)  # Add a delay to avoid rate limiting
    return False  # Failed to download from all subdomains

def get_tile(z, x, y):
    tile_path = os.path.join(TILE_DIR, str(z), str(x), f'{y}.png')
    if not os.path.exists(tile_path):
        if not download_tile(z, x, y):
            return None
    return send_from_directory(os.path.join(TILE_DIR, str(z), str(x)), f'{y}.png')



def pre_download_tiles():
    for zoom in range(MIN_ZOOM, MAX_ZOOM + 1):
        x_min, y_min = deg2num(*BOUNDS[:2], zoom)
        x_max, y_max = deg2num(*BOUNDS[2:], zoom)
        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                download_tile(zoom, x, y)

# Function to convert latitude/longitude to tile numbers
def deg2num(lon_deg, lat_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

# --- Flask Routes ---


@app.route('/')
def index():
    return render_template('map.html')

@app.route('/get_positions')
def get_positions_endpoint():
    return jsonify(get_dummy_positions())

@app.route('/tiles_bojongsoang/<int:z>/<int:x>/<int:y>.png')
def tiles(z, x, y):
    tile_path = os.path.join(TILE_DIR, str(z), str(x), f'{y}.png')
    if not os.path.exists(tile_path):
        download_tile(z, x, y)  # Download the tile if it doesn't exist
    return send_from_directory(os.path.join(TILE_DIR, str(z), str(x)), f'{y}.png')


if __name__ == '__main__':
    pre_download_tiles()  # Pre-download tiles on server start
    app.run(debug=True)
