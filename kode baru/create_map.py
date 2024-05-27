import folium
from geopy.distance import geodesic
import pymysql

def get_vehicle_coordinates():
    connection = pymysql.connect(host='localhost', user='root', password='raspbian', db='capstone')
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Mengambil 3 entri terbaru dari tabel gps_data
            cursor.execute("SELECT latitude, longitude FROM gps_data ORDER BY id DESC LIMIT 3")
            result = cursor.fetchall()
            if len(result) < 3:
                raise ValueError("Tidak cukup data untuk menampilkan kendaraan pengguna dan kendaraan lain.")
            
            # Entri pertama dianggap sebagai koordinat kendaraan pengguna
            user_vehicle = (float(result[0]['latitude']), float(result[0]['longitude']))
            # Dua entri berikutnya dianggap sebagai koordinat kendaraan lain
            vehicles_positions = [(float(row['latitude']), float(row['longitude'])) for row in result[1:]]
        return user_vehicle, vehicles_positions
    finally:
        connection.close()

def create_map(user_vehicle, vehicles_positions):
    # Membuat peta dengan pusat pada kendaraan pengguna
    vehicle_map = folium.Map(location=user_vehicle, zoom_start=15)
    # Menambahkan marker untuk kendaraan pengguna
    folium.Marker(location=user_vehicle, popup="User Vehicle", icon=folium.Icon(color="blue")).add_to(vehicle_map)
    
    # Menambahkan marker untuk kendaraan lain
    for vehicle_position in vehicles_positions:
        distance = geodesic(user_vehicle, vehicle_position).meters
        distance_text = f"{distance:.2f} m"
        folium.Marker(location=vehicle_position, popup=distance_text, icon=folium.Icon(color="red")).add_to(vehicle_map)
    
    # Menyimpan peta ke dalam file HTML
    vehicle_map.save("vehicle_map.html")

def main():
    user_vehicle, vehicles_positions = get_vehicle_coordinates()
    create_map(user_vehicle, vehicles_positions)

if __name__ == "__main__":
    main()
