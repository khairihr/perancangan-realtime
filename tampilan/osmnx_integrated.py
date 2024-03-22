import osmnx as ox
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import threading
import time

# Function to convert DMS to DD
def dms_to_dd(d, m, s, direction):
    dd = d + m/60 + s/3600
    if direction in ['S', 'W']:
        dd *= -1
    return dd

# Placeholder for reading GPS data from your GPS module via SPI
def read_gps_data():
    # TODO: Implement SPI communication to read from the GPS module
    # This function should return the latitude and longitude as a tuple (lat, lon)
    return (0.0, 0.0)  # Return dummy coordinates for now

# Placeholder for reading vehicle positions from LoRa messages
def read_lora_messages():
    # TODO: Implement logic to read messages from the LoRa module
    # This could involve SPI communication or another interface your module uses
    # Should return a list of tuples with vehicle positions [(lat1, lon1), (lat2, lon2), ...]
    return []  # Return empty list for now

# Function to update vehicle positions and replot the map
def update_positions():
    while True:
        user_vehicle_lat, user_vehicle_lon = read_gps_data()
        vehicles_positions = read_lora_messages()

        # Assuming the update and replot logic is here.
        # NOTE: Direct manipulation of matplotlib plots outside the main thread may not work as expected.
        # This is a simplified representation of what needs to happen.
        
        # For a more complex GUI, consider using a framework that supports real-time updates in a thread-safe manner.
        
        time.sleep(5)  # Update every 5 seconds, adjust as needed

# Main execution
if __name__ == "__main__":
    # Start the update loop in a separate thread
    update_thread = threading.Thread(target=update_positions)
    update_thread.daemon = True  # Daemonize thread
    update_thread.start()

    # Initial plot (this section will only run once, further updates need to be handled in the update_positions function)
    user_vehicle_lat, user_vehicle_lon = read_gps_data()
    user_vehicle = (user_vehicle_lat, user_vehicle_lon)
    vehicles_positions = read_lora_messages()
    location_point = user_vehicle
    G = ox.graph_from_point(location_point, dist=500, dist_type='bbox', network_type='drive')
    fig, ax = ox.plot_graph(G, show=False, close=False, node_size=0)
    ax.scatter(user_vehicle_lon, user_vehicle_lat, c='blue', s=100, label='User Vehicle', zorder=5)

    for vehicle_position in vehicles_positions:
        ax.scatter(vehicle_position[1], vehicle_position[0], c='red', s=100, zorder=5)
        distance = geodesic(user_vehicle, vehicle_position).meters
        distance_text = f"{distance:.2f} m"
        ax.text(vehicle_position[1], vehicle_position[0], distance_text, fontsize=8, ha='center', va='bottom', color='darkred', zorder=10, bbox=dict(facecolor='white', alpha=0.5, edgecolor='none', boxstyle='round,pad=0.2'))

    plt.legend()
    plt.show()
