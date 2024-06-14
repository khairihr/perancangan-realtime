from flask import Flask, render_template, jsonify
import mysql.connector
import math
import numpy as np

app = Flask(__name__)

# Konfigurasi database
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'raspbian',
    'database': 'capstone'
}

# Fungsi keanggotaan (membership functions)
def triangular(x, a, b, c):
    if b - a == 0:
        return np.where(np.isclose(x, a), 1, 0)  # Use np.isclose for element-wise comparison with tolerance
    elif c - b == 0:
        return np.where(np.isclose(x, c), 1, 0)  # Use np.isclose for element-wise comparison with tolerance
    else:
        return np.maximum(np.minimum((x - a) / (b - a), (c - x) / (c - b)), 0)


def trapezoidal(x, a, b, c, d):
    return max(min((x - a) / (b - a), 1, (d - x) / (d - c)), 0)

# Fungsi fuzzy AND dan OR
def fuzzy_and(a, b):
    return min(a, b)

def fuzzy_or(a, b):
    return max(a, b)

# Fungsi untuk menghitung jarak antara dua titik koordinat (Haversine formula)
def calculate_distance(lat1, lon1, lat2, lon2):
    # Radius bumi dalam meter
    R = 6371000 

    # Konversi derajat ke radian (tambahkan float())
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))

    # Haversine formula
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Jarak dalam meter
    distance = R * c
    return distance

# Fungsi untuk menghitung jarak aman menggunakan logika fuzzy manual
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
     # Handle zero denominator
    if denominator == 0:
        return 50  # atau nilai default lainnya yang sesuai

    safe_distance = numerator / denominator
    return safe_distance

# Fungsi untuk mengambil data posisi kendaraan dari database
def get_positions():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # Mengambil data terbaru dari tabel selfgps (kendaraan pengguna)
        cursor.execute("SELECT latitude, longitude, speed, time FROM selfgps ORDER BY date DESC, time DESC LIMIT 1")
        result_user = cursor.fetchone()

        if result_user is None:
            return jsonify({'error': 'User data not found'})

        # Mengambil data dari tabel gps_data (kendaraan lain)
        cursor.execute("SELECT latitude, longitude, speed, time, node FROM gps_data ORDER BY date DESC, time DESC LIMIT 10")
        result_others = cursor.fetchall()

        vehicles_positions = []
        for row in result_others:
            # Hitung jarak dan selisih kecepatan (tambahkan float())
            distance = calculate_distance(float(result_user['latitude']), float(result_user['longitude']), float(row['latitude']), float(row['longitude']))
            relative_speed = float(row['speed']) - float(result_user['speed']) if float(result_user['speed']) != 0 else 0

            # Tentukan jarak aman menggunakan logika fuzzy
            safe_distance = calculate_safe_distance(float(result_user['speed']), distance, relative_speed)

            vehicles_positions.append({
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude']),
                'speed': float(row['speed']),
                'time': row['time'],
                'node': row['node'],
                'safe_distance': float(safe_distance),
                'distance': float(distance)
            })

        return {
            'user': {
                'latitude': float(result_user['latitude']),
                'longitude': float(result_user['longitude']),
                'speed': float(result_user['speed']),
                'time': result_user['time']
            },
            'others': vehicles_positions
        }

    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return jsonify({'error': 'Database error'})
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/')
def index():
    return render_template('map.html')

@app.route('/get_positions')
def get_positions_endpoint():
    return jsonify(get_positions())

if __name__ == '__main__':
    app.run(debug=True)
