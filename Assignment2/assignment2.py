import board
import neopixel
import audiobusio
import array
import math
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.standard.hid import HIDService
from adafruit_hid.keyboard import Keyboard, Keycode
import time
from adafruit_apds9960 import colorutility
import simpleio

# Initialize microphone
mic = audiobusio.PDMIn(board.MICROPHONE_CLOCK, board.MICROPHONE_DATA, sample_rate=16000, bit_depth=16)
samples = array.array('H', [0] * 160)  # room to store 160 samples

# Normalized root mean square of an array of values
def normalized_rms(values):
    mean = int(sum(values) / len(values))
    samples_sum = sum(
        float(sample - mean) * (sample - mean)
        for sample in values
    )
    return math.sqrt(samples_sum / len(values))

# Initialize NeoPixels
pixel_pin = board.NEOPIXEL
pixel_num = 10
pixels = neopixel.NeoPixel(pixel_pin, pixel_num, brightness=0.1, auto_write=False)

# Sound threshold
LOUD_THRESHOLD = 50

# Initialize APDS9960
i2c = board.I2C()
apds = APDS9960(i2c)
apds.enable_proximity = True
apds.enable_gesture = True

# BLE setup
ble = BLERadio()
hid = HIDService()
advertisement = ProvideServicesAdvertisement(hid)
advertisement.complete_name = "Mel's Keyboard"
keyboard = Keyboard(hid.devices)

GREEN = (0, 127, 0)
RED = (127, 0, 0)
YELLOW = (127, 127, 0)
OFF = (0, 0, 0)
colors = [GREEN, GREEN, GREEN, GREEN, GREEN, GREEN, GREEN, YELLOW, YELLOW, RED]

def rainbow_cycle(wait=2):
    start_time = time.monotonic()  # Start time
    while True:
        current_time = time.monotonic() 
        if current_time - start_time > wait:
            break  # End after 2 seconds

        for j in range(255):
            for i in range(pixel_num):
                rc_index = (i * 256 // pixel_num) + j
                pixels[i] = wheel(rc_index & 255)
            pixels.show()
            if current_time - start_time > wait:
                break
            time.sleep(0.01)

        pixels.fill(OFF)
        pixels.show()

def wheel(pos):
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)

while True:
    ble.start_advertising(advertisement)
    while not ble.connected:
        pass
    ble.stop_advertising()
    print("\nConnected!")

    while ble.connected:
        gesture = apds.gesture()

        mic.record(samples, len(samples))
        magnitude = normalized_rms(samples)
        if magnitude > LOUD_THRESHOLD:
            pixels.fill(RED)
        else:
            pixels.fill(OFF)

        pixels.show()

        if gesture == 0x01:  # Up
            print("Want to talk to you!")
            pixels.fill(GREEN)
            pixels.show()
            time.sleep(3)
            pixels.fill(OFF)
            pixels.show()
        elif gesture == 0x02:  # Down
            print("You are being annoying!")
            pixels.fill(YELLOW)
            pixels.show()
            time.sleep(3)
            pixels.fill(OFF)
            pixels.show()
        elif gesture == 0x03:  # Left
            print("Hello!")
            rainbow_cycle()
            pixels.fill(OFF)
            pixels.show()

        elif gesture == 0x04:  # Right
            print("Bye!")
            rainbow_cycle() 
            pixels.fill(OFF)
            pixels.show()

        try:
            if not ble.connected:
                raise ConnectionError
        except ConnectionError:
            print("\nDisconnected!")
            break
