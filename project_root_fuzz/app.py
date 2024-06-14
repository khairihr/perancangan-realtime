from flask import Flask, render_template, jsonify
import mysql.connector
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import math

app = Flask(__name__)

# Konfigurasi database (sesuaikan dengan pengaturan Anda)
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'raspbian',
    'database': 'capstone'
}

# Definisi variabel fuzzy
kecepatan_saat_ini = ctrl.Antecedent(np.arange(0, 121, 1), 'kecepatan_saat_ini')
selisih_jarak = ctrl.Antecedent(np.arange(0, 101, 1), 'selisih_jarak')
selisih_kecepatan = ctrl.Antecedent(np.arange(-50, 51, 1), 'selisih_kecepatan')
jarak_aman = ctrl.Consequent(np.arange(0, 101, 1), 'jarak_aman')

# Definisi himpunan fuzzy
kecepatan_saat_ini['lambat'] = fuzz.trimf(kecepatan_saat_ini.universe, [0, 0, 50])
kecepatan_saat_ini['sedang'] = fuzz.trimf(kecepatan_saat_ini.universe, [40, 80, 120])
kecepatan_saat_ini['cepat'] = fuzz.trimf(kecepatan_saat_ini.universe, [110, 120, 120])

selisih_jarak['dekat'] = fuzz.trimf(selisih_jarak.universe, [0, 0, 30])
selisih_jarak['sedang'] = fuzz.trimf(selisih_jarak.universe, [20, 50, 80])
selisih_jarak['jauh'] = fuzz.trimf(selisih_jarak.universe, [70, 100, 100])

selisih_kecepatan['negatif'] = fuzz.trimf(selisih_kecepatan.universe, [-50, -50, 0])
selisih_kecepatan['nol'] = fuzz.trimf(selisih_kecepatan.universe, [-10, 0, 10])
selisih_kecepatan['positif'] = fuzz.trimf(selisih_kecepatan.universe, [0, 50, 50])

jarak_aman['pendek'] = fuzz.trimf(jarak_aman.universe, [0, 0, 20])
jarak_aman['sedang'] = fuzz.trimf(jarak_aman.universe, [10, 50, 90])
jarak_aman['panjang'] = fuzz.trimf(jarak_aman.universe, [80, 100, 100])

# Definisi aturan fuzzy (lengkapi sesuai kebutuhan)
rule1 = ctrl.Rule(kecepatan_saat_ini['lambat'] & selisih_jarak['dekat'] & selisih_kecepatan['negatif'], jarak_aman['pendek'])
rule2 = ctrl.Rule(kecepatan_saat_ini['lambat'] & selisih_jarak['dekat'] & selisih_kecepatan['nol'], jarak_aman['sedang'])
rule3 = ctrl.Rule(kecepatan_saat_ini['lambat'] & selisih_jarak['dekat'] & selisih_kecepatan['positif'], jarak_aman['panjang'])
rule4 = ctrl.Rule(kecepatan_saat_ini['lambat'] & selisih_jarak['sedang'] & selisih_kecepatan['negatif'], jarak_aman['pendek'])
rule5 = ctrl.Rule(kecepatan_saat_ini['lambat'] & selisih_jarak['sedang'] & selisih_kecepatan['nol'], jarak_aman['sedang'])
rule6 = ctrl.Rule(kecepatan_saat_ini['lambat'] & selisih_jarak['sedang'] & selisih_kecepatan['positif'], jarak_aman['panjang'])

jarak_aman_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6])  # Tambahkan semua aturan Anda di sini
jarak_aman_sim = ctrl.ControlSystemSimulation(jarak_aman_ctrl)

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
            # Hitung jarak dan selisih kecepatan
            distance = calculate_distance(result_user['latitude'], result_user['longitude'], float(row['latitude']), float(row['longitude']))
            relative_speed = row['speed'] - result_user['speed'] if result_user['speed'] != 0 else 0

            # Tentukan jarak aman menggunakan logika fuzzy
            jarak_aman_sim.input['kecepatan_saat_ini'] = result_user['speed']
            jarak_aman_sim.input['selisih_jarak'] = distance
            jarak_aman_sim.input['selisih_kecepatan'] = relative_speed
            jarak_aman_sim.compute()
            safe_distance = jarak_aman_sim.output['jarak_aman']

            vehicles_positions.append({
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude']),
                'speed': row['speed'],
                'time': row['time'],
                'node': row['node'],
                'safe_distance': safe_distance,
                'distance': distance
            })

        return {
            'user': result_user,
            'others': vehicles_positions
        }

    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return jsonify({'error': 'Database error'})
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Fungsi untuk menghitung jarak antara dua titik koordinat (Haversine formula)
def calculate_distance(lat1, lon1, lat2, lon2):
    # Radius bumi dalam meter
    R = 6371000

    # Konversi derajat ke radian
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Jarak dalam meter
    distance = R * c
    return distance

# Route utama untuk menampilkan halaman peta
@app.route('/')
def index():
    return render_template('map.html')

# Endpoint untuk mengambil data posisi kendaraan
@app.route('/get_positions')
def get_positions_endpoint():
    return jsonify(get_positions())

if __name__ == '__main__':
    app.run(debug=True)
