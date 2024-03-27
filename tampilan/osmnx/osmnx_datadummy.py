import osmnx as ox
import matplotlib.pyplot as plt
from geopy.distance import geodesic

# Function to convert DMS to DD
def dms_to_dd(d, m, s, direction):
    dd = d + m/60 + s/3600
    if direction in ['S', 'W']:
        dd *= -1
    return dd

# User's vehicle (DMS to DD conversion)
user_vehicle_lat = dms_to_dd(6, 56, 42.4, 'S')
user_vehicle_lon = dms_to_dd(107, 38, 30.6, 'E')

# Other vehicles (DMS to DD conversion)
vehicle_1_lat = dms_to_dd(6, 56, 42.5, 'S')
vehicle_1_lon = dms_to_dd(107, 38, 34.4, 'E')
vehicle_2_lat = dms_to_dd(6, 56, 45.2, 'S')
vehicle_2_lon = dms_to_dd(107, 38, 25.3, 'E')

# Convert to tuples for geopy and OSMnx
user_vehicle = (user_vehicle_lat, user_vehicle_lon)
vehicles_positions = [(vehicle_1_lat, vehicle_1_lon), (vehicle_2_lat, vehicle_2_lon)]

# Fetch the street network
location_point = user_vehicle
G = ox.graph_from_point(location_point, dist=5000, dist_type='bbox', network_type='drive')
fig, ax = ox.plot_graph(G, show=False, close=False, node_size=0)

# Plot user vehicle position
ax.scatter(user_vehicle_lon, user_vehicle_lat, c='blue', s=100, label='User Vehicle', zorder=5)

# Plot other vehicles and calculate distances
for vehicle_position in vehicles_positions:
    ax.scatter(vehicle_position[1], vehicle_position[0], c='red', s=100, zorder=5)
    distance = geodesic(user_vehicle, vehicle_position).meters
    distance_text = f"{distance:.2f} m"
    ax.text(vehicle_position[1], vehicle_position[0], distance_text, fontsize=8, ha='center', va='bottom', color='darkred', zorder=10, bbox=dict(facecolor='white', alpha=0.5, edgecolor='none', boxstyle='round,pad=0.2'))

plt.legend()
plt.show()
