
import os
import time

while True:
    os.system('cls' if os.name == 'nt' else 'clear')
    f = open("display.txt", "r")
    print(f.read())
    f.close()   
    time.sleep(.5)
