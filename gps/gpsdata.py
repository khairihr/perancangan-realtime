import serial
from datetime import datetime, timedelta
import mysql.connector

port = "/dev/serial0"

# Establishing MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="raspbian",
    database="capstone"
)
cursor = db.cursor()

def parseGPS(data):
    if data.startswith("$GPRMC"):
        sdata = data.split(",")
        if sdata[2] == 'V':
            print("no satellite data available")
            return
        print("---Parsing GPRMC---")
        
        # Extracting time
        utc_time_str = sdata[1][0:2] + sdata[1][2:4] + sdata[1][4:6]
        date_str = sdata[9][0:2] + sdata[9][2:4] + sdata[9][4:6]

        # Creating datetime object for UTC time
        utc_time = datetime.strptime(date_str + utc_time_str, '%d%m%y%H%M%S')

        # Convert UTC to GMT+7
        gmt7_time = utc_time + timedelta(hours=7)
        time_str = gmt7_time.strftime('%H:%M:%S')
        date_str = gmt7_time.strftime('%Y-%m-%d')  # For MySQL date format

        lat = decode(sdata[3])  # latitude
        dirLat = sdata[4]       # latitude direction N/S
        lon = decode(sdata[5])  # longitude
        dirLon = sdata[6]       # longitude direction E/W
        speed_knots = float(sdata[7])  # Speed in knots
        speed_kmh = speed_knots * 1.852  # Convert knots to km/h

        if dirLat in ['S']:
            lat = -lat
        
        if dirLon in ['W']:
            lot = -lot

        # Write to file
        output = ('%s,%s,%s,%s,%f') %  (date_str, time_str, lat, lon, speed_kmh)

        print(output)
        f = open("/home/pi/gps.txt", "w")
        f.write(output + "\n")
        f.close()

        # Store in MySQL database
        sql = "INSERT INTO selfgps (date, time, latitude, longitude, speed) VALUES (%s, %s, %s, %s, %s)"
        val = (date_str, time_str, lat, lon, speed_kmh)

        cursor.execute(sql, val)
        db.commit()

def decode(coord):
    # Converts DDDMM.MMMMM > DD deg MM.MMMMM min
    x = coord.split(".")
    head = x[0]
    tail = x[1]
    deg = head[0:-2]
    min = head[-2:]
    minute = float("{}.{}".format(min, tail))
    degree = float(deg) + (minute / 60.00)
    return degree
    # return deg + " deg " + min + "." + tail + " min"

print("Receiving GPS data")
ser = serial.Serial(port, baudrate=9600, timeout=0.5)
while True:
    data = ser.readline()
    parseGPS(data)

# Close MySQL connection
cursor.close()
db.close()
