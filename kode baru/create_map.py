import folium
from geopy.distance import geodesic
import pymysql

def get_vehicle_coordinates():
    connection = pymysql.connect(host='localhost', user='root', password='raspbian', db='capstone')
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT latitude, longitude FROM gps_data ORDER BY id DESC LIMIT 3")
            result = cursor.fetchall()
            user_vehicle = (float(result[0]['latitude']), float(result[0]['longitude']))
            vehicles_positions = [(float(row['latitude']), float(row['longitude'])) for row in result[1:]]
        return user_vehicle, vehicles_positions
    finally:
        connection.close()

def create_map(user_vehicle, vehicles_positions):
    vehicle_map = folium.Map(location=user_vehicle, zoom_start=15)
    folium.Marker(location=user_vehicle, popup="User Vehicle", icon=folium.Icon(color="blue")).add_to(vehicle_map)
    for vehicle_position in vehicles_positions:
        distance = geodesic(user_vehicle, vehicle_position).meters
        distance_text = f"{distance:.2f} m"
        folium.Marker(location=vehicle_position, popup=distance_text, icon=folium.Icon(color="red")).add_to(vehicle_map)
    vehicle_map.save("vehicle_map.html")

def main():
    user_vehicle, vehicles_positions = get_vehicle_coordinates()
    create_map(user_vehicle, vehicles_positions)

if __name__ == "__main__":
    main()
