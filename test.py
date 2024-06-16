import serial
import time

i = 1
while True:
    f = open("/home/pi/test.txt", "w")
    print(i)
    i += 1
    f.write(str(i) + "\n")
    f.close()
    time.sleep(0.5)
