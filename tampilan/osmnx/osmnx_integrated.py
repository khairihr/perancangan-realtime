import threading
import time
import serial
import pynmea2
from SX127x.LoRa import *
from SX127x.board_config import BOARD
import osmnx as ox
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import os
import pickle

# Fungsi untuk membaca data GPS
def get_gps_data():
    """
    Get GPS data from Neo6MV2.

    Returns:
    tuple: Latitude and longitude in decimal degrees
    """
    port = "/dev/serial0"  # Adjust according to your connection
    ser = serial.Serial(port, baudrate=9600, timeout=1)
    while True:
        data = ser.readline().decode('ascii', errors='replace')
        if data[0:6] == '$GPGGA':
            msg = pynmea2.parse(data)
            lat = msg.latitude
            lon = msg.longitude
            return lat, lon

class LoRaSender(LoRa):
    def __init__(self, verbose=False):
        super(LoRaSender, self).__init__(verbose)
        BOARD.setup()

    def send_data(self, data):
        self.write_payload(list(map(ord, data)))
        self.set_mode(MODE.TX)
        time.sleep(0.5)
        self.set_mode(MODE.STDBY)

def send_position():
    lora = LoRaSender()
    lora.set_mode(MODE.STDBY)
    lora.set_pa_config(pa_select=1)
    while True:
        lat, lon = get_gps_data()
        data = f"{lat},{lon}"
        lora.send_data(data)
        print(f"Sent data: {data}")
        time.sleep(5)  # Send data every 5 seconds

class LoRaReceiver(LoRa):
    def __init__(self, verbose=False):
        super(LoRaReceiver, self).__init__(verbose)
        BOARD.setup()
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)

    def start(self):
        self.set_mode(MODE.RXCONT)

    def on_rx_done(self):
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        data = ''.join([chr(x) for x in payload])
        print(f"Received data: {data}")
        lat, lon = map(float, data.split(","))
        return lat, lon

def receive_position(vehicles_positions):
    lora = LoRaReceiver()
    lora.start()
    while True:
        lat, lon = lora.on_rx_done()
        vehicles_positions.append((lat, lon))
        print(f"Received position: Latitude: {lat}, Longitude: {lon}")

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
    # Menginisialisasi posisi kendaraan lain
    vehicles_positions = []

    # Membuat thread untuk pengiriman dan penerimaan data
    sender_thread = threading.Thread(target=send_position)
    receiver_thread = threading.Thread(target=receive_position, args=(vehicles_positions,))

    sender_thread.start()
    receiver_thread.start()

    # Menyiapkan peta
    map_filename = 'map_network.pkl'
    initial_lat, initial_lon = -6.9175, 107.6191  # Initial point to fetch map (example coordinates)

    if os.path.exists(map_filename):
        with open(map_filename, 'rb') as file:
            G = pickle.load(file)
    else:
        G = ox.graph_from_point((initial_lat, initial_lon), dist=1000, dist_type='bbox', network_type='drive')
        with open(map_filename, 'wb') as file:
            pickle.dump(G, file)

    while True:
        user_vehicle = get_gps_data()  # Read user vehicle position from GPS
        plot_vehicles_on_map(G, user_vehicle, vehicles_positions)
        time.sleep(5)  # Update every 5 seconds

if __name__ == "__main__":
    main()
