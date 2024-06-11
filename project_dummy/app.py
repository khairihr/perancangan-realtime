from flask import Flask, render_template, jsonify
import random
import time
import threading

app = Flask(__name__)

# Data dummy untuk posisi kendaraan (sudah dikonversi ke desimal derajat)
vehicles_data = {
    'user': {
        'latitude': -6.938806, 
        'longitude': 107.667472, 
        'speed': 20,
        'time': time.strftime('%Y-%m-%d %H:%M:%S'),  # Waktu saat ini
        'node': 'user'
    },
    'others': [
        {
            'latitude': -6.939056,  
            'longitude': 107.663722,
            'speed': random.uniform(10, 30),
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'node': 'vehicle1'
        },
        {
            'latitude': -6.940444,
            'longitude': 107.657667,
            'speed': random.uniform(10, 30),
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'node': 'vehicle2'
        }
    ]
}

# Fungsi untuk terus memperbarui data posisi (dummy)
def update_positions():
    global vehicles_data  # Akses variabel global
    while True:
        for vehicle in vehicles_data['others']:
            vehicle['latitude'] += random.uniform(-0.001, 0.001)  # Perubahan posisi acak
            vehicle['longitude'] += random.uniform(-0.001, 0.001)
            vehicle['speed'] = random.uniform(10, 30)
            vehicle['time'] = time.strftime('%Y-%m-%d %H:%M:%S')  # Update waktu setiap iterasi
        vehicles_data['user']['time'] = time.strftime('%Y-%m-%d %H:%M:%S') # Update waktu untuk user
        time.sleep(5)  # Interval update (5 detik)

# Route utama untuk menampilkan halaman peta
@app.route('/')
def index():
    return render_template('map.html')

# Endpoint untuk mengambil data posisi kendaraan
@app.route('/get_positions')
def get_positions_endpoint():
    return jsonify(vehicles_data)

if __name__ == '__main__':
    # Jalankan thread untuk update data dummy
    update_thread = threading.Thread(target=update_positions)
    update_thread.start()

    app.run(debug=True)
