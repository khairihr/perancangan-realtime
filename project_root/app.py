from flask import Flask, render_template, jsonify
import mysql.connector
import json
import time

app = Flask(__name__)

# Fungsi untuk mengambil data posisi kendaraan dari database
def get_positions():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="raspbian",
        database="capstone"
    )
    try:
        cursor = connection.cursor(dictionary=True)

        # Mengambil data terbaru dari tabel selfgps (kendaraan pengguna)
        cursor.execute("SELECT latitude, longitude, speed, time FROM selfgps ORDER BY date DESC, time DESC LIMIT 1")
        result_user = cursor.fetchone()

        # Mengambil data dari tabel gps_data (kendaraan lain)
        cursor.execute("SELECT latitude, longitude, speed, time, node FROM gps_data ORDER BY date DESC, time DESC LIMIT 3")
        result_others = cursor.fetchall()

        vehicles_positions = []
        for row in result_others:
            vehicles_positions.append({
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude']),
                'speed': row['speed'],
                'time': row['time'],
                'node': row['node']
            })

        return {
            'user': result_user,
            'others': vehicles_positions
        }

    finally:
        cursor.close()
        connection.close()

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
