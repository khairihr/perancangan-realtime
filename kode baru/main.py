import threading
import time
import gps_data
import create_map

def lora_thread():
    while True:
        lat, lon = gps_data.get_gps_data()
        lora_communication.send_position(lat, lon)
        time.sleep(5)

def gps_thread():
    while True:
        gps_data.get_gps_data()
        time.sleep(5)

def map_thread():
    while True:
        create_map.main()
        time.sleep(10)

if __name__ == "__main__":
    thread1 = threading.Thread(target=lora_thread)
    thread2 = threading.Thread(target=gps_thread)
    thread3 = threading.Thread(target=map_thread)

    thread1.start()
    thread2.start()
    thread3.start()

    thread1.join()
    thread2.join()
    thread3.join()
