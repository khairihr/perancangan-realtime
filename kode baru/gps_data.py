import serial
import pynmea2
import pymysql

def get_gps_data():
    port = "/dev/serial0"
    ser = serial.Serial(port, baudrate=9600, timeout=1)
    while True:
        data = ser.readline().decode('ascii', errors='replace')
        if data[0:6] == '$GPGGA':
            msg = pynmea2.parse(data)
            lat = msg.latitude
            lon = msg.longitude
            save_to_database(lat, lon)
            return lat, lon

def save_to_database(lat, lon):
    connection = pymysql.connect(host='localhost', user='root', password='password', db='vehicle_data')
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO gps_data (latitude, longitude) VALUES (%s, %s)"
            cursor.execute(sql, (lat, lon))
        connection.commit()
    finally:
        connection.close()
