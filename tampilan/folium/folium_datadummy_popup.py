import folium
from geopy.distance import geodesic

# Placeholder fungsi untuk membaca data GPS (gunakan data nyata di sini)
def read_gps_data():
    # Contoh koordinat kendaraan pengguna (lat, lon)
    return -6.9727, 107.6316

# Placeholder fungsi untuk membaca posisi kendaraan lain dari LoRa
def read_lora_messages():
    # Contoh koordinat kendaraan lain
    return [(-6.974, 107.630), (-6.975, 107.631)]

# Menginisiasi peta dengan lokasi tengah dan zoom awal
user_location = read_gps_data()
map = folium.Map(location=user_location, zoom_start=15)

# Menambahkan marker untuk kendaraan pengguna
folium.Marker(user_location, popup='Kendaraan Anda', icon=folium.Icon(color='blue')).add_to(map)

# Menambahkan marker untuk kendaraan lain dengan jarak
vehicles_positions = read_lora_messages()
for vehicle_pos in vehicles_positions:
    distance = geodesic(user_location, vehicle_pos).meters
    popup_text = f"Jarak: {distance:.2f} m"
    folium.Marker(vehicle_pos, popup = popup_text, icon=folium.Icon(color='red')).add_to(map)

# Menyimpan peta ke dalam file HTML
map.save('vehicle_positions_map.html')
