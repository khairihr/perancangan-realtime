from SX127x.LoRa import *
from SX127x.board_config import BOARD
import pymysql

class LoRaSender(LoRa):
    def __init__(self, verbose=False):
        super(LoRaSender, self).__init__(verbose)
        BOARD.setup()

    def send_data(self, data):
        self.write_payload(list(map(ord, data)))
        self.set_mode(MODE.TX)
        time.sleep(0.5)
        self.set_mode(MODE.STDBY)

def send_position(lat, lon):
    lora = LoRaSender()
    lora.set_mode(MODE.STDBY)
    lora.set_pa_config(pa_select=1)
    data = f"{lat},{lon}"
    lora.send_data(data)
    save_to_database(lat, lon)

def save_to_database(lat, lon):
    connection = pymysql.connect(host='localhost', user='root', password='password', db='vehicle_data')
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO gps_data (latitude, longitude) VALUES (%s, %s)"
            cursor.execute(sql, (lat, lon))
        connection.commit()
    finally:
        connection.close()
