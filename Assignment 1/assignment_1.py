import digitalio
import time
import board
import analogio
import simpleio
from adafruit_circuitplayground import cp
import rtc
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

ble = BLERadio()
ble.name = "mel's playground"
uart_server = UARTService()
advertisement = ProvideServicesAdvertisement(uart_server)

cp.pixels.auto_write = False
cp.pixels.brightness = 0.1
real_time_clock = rtc.RTC()
real_time_clock.datetime = time.struct_time((2024, 2, 18, 15, 55, 15, 2, 149, -1))

def scale_range(value):
    return round(value / 9)

timer_start = None

print("hi")
stand_up = False
light = False

while True:
    # Advertise when not connected.
    ble.start_advertising(advertisement)
    while not ble.connected:
        pass
    ble.stop_advertising()
    print("Connected!")
    
    while ble.connected:
        try:
            x, y, z = cp.acceleration
            
            if cp.button_a and timer_start is None:
                print("Button A pressed! Starting the 10-minute countdown.")
                cp.play_file("rise.wav")
                timer_start = time.monotonic()  # Start the timer
                light = True
                uart_server.write("start timer \n")

            if cp.button_b:
                print("Button B pressed! Turning off the light.")
                cp.play_file("rise.wav")
                light = False
                timer_start = None
                uart_server.write("end timer - stop by button b \n")

            # If the timer has started, check if 10 minutes have passed
            if timer_start is not None and (time.monotonic() - timer_start) > 10:  # 600 seconds = 10 minutes
                # cp.start_tone(262)
                print("10 minutes passed. Turning off the light.")
                cp.play_file("rise.wav")
                light = False
                timer_start = None  # Reset the timer
                uart_server.write("end timer \n")

            # Check if the hat is worn
            if z < 3:
                stand_up = True
                uart_server.write("hat stands up \n")
            else:
                stand_up = False
                uart_server.write("hat lays flat \n")
            
            # Light
            peak = scale_range(cp.light)
            num_of_light = 9 - peak
        #     print("peak")
        #     print(peak)
        #     print("num_of_light")
        #     print(num_of_light)
            for i in range(10):
        #         print(i <= num_of_light)
        #         print("stand up or light")
        #         print(stand_up or light)
                if i <= num_of_light and (stand_up or light):            
                    cp.pixels[i] = (0, 255, 255)
                    uart_server.write(f"{i} light up \n")
                else:
                    cp.pixels[i] = (0, 0, 0)
            cp.pixels.show()
            # uart_server.write(f"{x},{y},{z}\n")
        except ConnectionError:
            print("Disconnected!")
            break
        time.sleep(1)
    