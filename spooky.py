import numpy as np
import cv2
import serial

ARRAY_WIDTH = 10
ARRAY_HEIGHT = 10
DISPLAY_SCALE = 20

def display_array_debug(array, scale=1):
    display_points = np.kron(array, np.ones((scale, scale, 1), dtype=np.uint8))
    cv2.imshow("Pixels", display_points)


class NeoPixelController():
    controller_serial = None
    
    def __init__(self, com_port) -> None:
        self.controller_serial = serial.Serial('COM4', 230400, timeout=.5)

    def neopixel_array_to_index(self, x, y):
        return ((ARRAY_WIDTH * y) + x)
    
    def send_array(self, array):
        if self.controller_serial is None:
            return
         
        neopixel_array = [0] * (ARRAY_WIDTH * ARRAY_HEIGHT * 3)
        for y in range(ARRAY_HEIGHT):
            for x in range(ARRAY_WIDTH):
                # Output the pixels in the order GBR
                index = self.neopixel_array_to_index(x, y) * 3
                neopixel_array[index] = array[y, x][1]
                neopixel_array[index + 1] = array[y, x][2]
                neopixel_array[index + 2] = array[y, x][0]
        self.controller_serial.write(bytearray(neopixel_array))



def show_rainbow(x,y,t):
    return [ int(255 * (np.sin(t / 10 + x / 2) + 1) / 2), int(255 * (np.sin(t / 10 + y / 2) + 1) / 2), int(255 * (np.sin(t / 10 + x / 2 + y / 2) + 1) / 2)]

def show_twoaxis(x,y,t):
    return [int(255*x/ARRAY_WIDTH), int(255*y/ARRAY_HEIGHT), (t*5)%255]

emotes = {
    "Rainbow": show_rainbow,
    "TwoAxis": show_twoaxis
}

arduino = NeoPixelController('COM4')
output_points = np.zeros((ARRAY_HEIGHT, ARRAY_WIDTH, 3), np.uint8)

show = "Rainbow"

t = 0
while True:
    for x in range(0, ARRAY_WIDTH):
        for y in range(0, ARRAY_HEIGHT):
            output_points[y, x] = emotes.get(show)(x, y, t)

    display_array_debug(output_points, DISPLAY_SCALE)
    arduino.send_array(output_points)


    key = cv2.waitKey(20)
    if key == 27: # exit on ESC
        break
    elif key == 49: # 1
        show = "Rainbow"
    elif key == 50: # 2
        show = "TwoAxis"

    t += 1


