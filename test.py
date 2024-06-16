import serial
import time

i = 1
while True:
    f = open("/home/pi/test.txt", "w")
    print(i)
    i += 1
    f.write(i + "\n")
    f.close()
    time.sleep(1000)
