import serial
import time

f = open("/home/pi/gps.txt", "w")
for i in range(1, 11):
    print(i)
    time.sleep(1000)  # Add a delay of 1 second

f.write(output + "\n")
f.close()
