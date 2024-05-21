import osmnx as ox
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import os
import pickle

# Function to convert DMS to DD
def dms_to_dd(d, m, s, direction):
    """
    Convert degrees, minutes, seconds to decimal degrees.

    Parameters:
    d (int): Degrees
    m (int): Minutes
    s (float): Seconds
    direction (str): Direction ('N', 'S', 'E', 'W')

    Returns:
    float: Decimal degrees
    """
    try:
        dd = d + m/60 + s/3600
        if direction in ['S', 'W']:
            dd *= -1
        return dd
    except Exception as e:
        print(f"Error converting DMS to DD: {e}")
        return None

def get_vehicle_coordinates():
    """
    Get coordinates of the user and other vehicles in decimal degrees.

    Returns:
    tuple: Coordinates of user vehicle, list of coordinates of other vehicles
    """
    try:
        user_vehicle_lat = dms_to_dd(6, 56, 42.4, 'S')
        user_vehicle_lon = dms_to_dd(107, 38, 30.6, 'E')
        vehicle_1_lat = dms_to_dd(6, 56, 42.5, 'S')
        vehicle_1_lon = dms_to_dd(107, 38, 34.4, 'E')
        vehicle_2_lat = dms_to_dd(6, 56, 45.2, 'S')
        vehicle_2_lon = dms_to_dd(107, 38, 25.3, 'E')

        user_vehicle = (user_vehicle_lat, user_vehicle_lon)
        vehicles_positions = [(vehicle_1_lat, vehicle_1_lon), (vehicle_2_lat, vehicle_2_lon)]

        return user_vehicle, vehicles_positions
    except Exception as e:
        print(f"Error getting vehicle coordinates: {e}")
        return None, None

def fetch_or_load_map(location_point, dist=1000):
    """
    Fetch the map from OSMnx or load it from a local file if already downloaded.

    Parameters:
    location_point (tuple): Coordinates of the location point
    dist (int): Distance in meters to define the bounding box

    Returns:
    networkx.classes.multidigraph.MultiDiGraph: Graph of the street network
    """
    map_filename = 'map_network.pkl'

    if os.path.exists(map_filename):
        with open(map_filename, 'rb') as file:
            G = pickle.load(file)
        print("Map loaded from local file.")
    else:
        G = ox.graph_from_point(location_point, dist=dist, dist_type='bbox', network_type='drive')
        with open(map_filename, 'wb') as file:
            pickle.dump(G, file)
        print("Map downloaded and saved locally.")

    return G

def plot_vehicles_on_map(G, user_vehicle, vehicles_positions):
    """
    Plot the vehicles on the map and display distances between them.

    Parameters:
    G (networkx.classes.multidigraph.MultiDiGraph): Graph of the street network
    user_vehicle (tuple): Coordinates of the user's vehicle
    vehicles_positions (list): List of coordinates of other vehicles
    """
    try:
        fig, ax = ox.plot_graph(G, bgcolor='white', edge_color='gray', node_size=0, show=False, close=False)

        # Plot user vehicle position
        ax.scatter(user_vehicle[1], user_vehicle[0], c='blue', s=100, label='User Vehicle', zorder=5)

        # Plot other vehicles and calculate distances
        for vehicle_position in vehicles_positions:
            ax.scatter(vehicle_position[1], vehicle_position[0], c='red', s=100, zorder=5)
            distance = geodesic(user_vehicle, vehicle_position).meters
            distance_text = f"{distance:.2f} m"
            ax.text(vehicle_position[1], vehicle_position[0], distance_text, fontsize=8, ha='center', va='bottom', color='darkred', zorder=10, bbox=dict(facecolor='white', alpha=0.5, edgecolor='none', boxstyle='round,pad=0.2'))

        plt.legend()
        plt.show()
    except Exception as e:
        print(f"Error plotting vehicles on map: {e}")

def main():
    """
    Main function to run the program.
    """
    user_vehicle, vehicles_positions = get_vehicle_coordinates()
    if user_vehicle and vehicles_positions:
        G = fetch_or_load_map(user_vehicle)
        plot_vehicles_on_map(G, user_vehicle, vehicles_positions)
    else:
        print("Error: Invalid vehicle coordinates.")

if __name__ == "__main__":
    main()
