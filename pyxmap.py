# Set up virtual webcam
# Set up array of pixel map point locations and sizes
# Grab Data from Virtual Webcam
# Average data from each pixel map point
# Arrange the data into an array based on the topology of the LED board
# Serialize and send the data to the Arduino

import cv2
import numpy as np
import serial
import time 

class Pixel:
    r = 0
    g = 0
    b = 0

    
    def __init__(self):
        pass

    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b
        
class PixelMapPoint:
    x = 0
    y = 0
    square_size = 1
    
    def __init__(self, x, y, square_size = 1):
        self.x = x
        self.y = y
        self.square_size = square_size
        
    def get_average_pixel_value(self, frame):
        # Access the frame and average all the pixels in the square, then return the value as a pixel object
        a = np.mean(frame[int(self.y - (self.square_size / 2)):int(self.y + (self.square_size / 2)), int(self.x - (self.square_size / 2)):int(self.x + (self.square_size / 2))], axis=(0, 1))
        return Pixel(a[2], a[1], a[0])

NEOPIXEL_SHEET_HEIGHT = 16
NEOPIXEL_SHEET_WIDTH = 1

def neopixel_array_to_index(x, y):
    # Convert the x, y coordinates of the pixel map to the correct order for the neopixel array
    neopixel_sheet = int(y / NEOPIXEL_SHEET_HEIGHT)
    neopixel_local_y = y % NEOPIXEL_SHEET_HEIGHT
    
    if neopixel_sheet == 0:
        neopixel_hook = int(x / 2)
        neopixel_hook_offset = neopixel_local_y if x % 2 == 0 else (NEOPIXEL_SHEET_HEIGHT * 2 - 1) - neopixel_local_y
        neopixel_index = (neopixel_hook * NEOPIXEL_SHEET_HEIGHT * 2) + neopixel_hook_offset
    if neopixel_sheet == 1:
        neopixel_hook = int((NEOPIXEL_SHEET_WIDTH -1   - x) / 2) 
        neopixel_hook_offset = NEOPIXEL_SHEET_HEIGHT + neopixel_local_y  if x % 2 == 0 else NEOPIXEL_SHEET_HEIGHT - neopixel_local_y - 1
        neopixel_index = (NEOPIXEL_SHEET_WIDTH * NEOPIXEL_SHEET_HEIGHT) + (neopixel_hook * (NEOPIXEL_SHEET_HEIGHT) * 2) + neopixel_hook_offset
    #print(f'x: {x}, y: {y}, sheet: {neopixel_sheet}, local_y: {neopixel_local_y}, hook: {neopixel_hook}, hook_offset: {neopixel_hook_offset}, index: {neopixel_index}')
    return int(neopixel_index)
    
   

#######################

arduino = None
try:
    arduino = serial.Serial('COM4', 115200, timeout=.5)
except:
    print("Failed to open serial port, continuing anyway")

ARRAY_HEIGHT = 16
ARRAY_WIDTH = 1    

# For now we just hardcode the array to be an equally spaced grid centered in the middle of the screen
# TODO: Make this more flexible
PIXELMAP_SPACING =  40 
PIXELMAP_SQUARE_WIDTH = 6

cv2.namedWindow("Pixels", cv2.WINDOW_NORMAL)

# Set up virtual webcam
cv2.namedWindow("Display", cv2.WINDOW_NORMAL)
vc = cv2.VideoCapture(1)
vc.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
vc.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
#vc.set(cv2.CAP_PROP_FPS, 60)

if vc.isOpened():
    rval, frame = vc.read()
else:
    rval = False
    
if rval is False:
    print("Failed to open webcam")
    exit(1)
    

resolution = (int(vc.get(cv2.CAP_PROP_FRAME_WIDTH)), int(vc.get(cv2.CAP_PROP_FRAME_HEIGHT)))
print("Resolution: " + str(resolution))

rows, cols = (ARRAY_HEIGHT, ARRAY_WIDTH)


pixmap_points = []

for j in range(rows):
    pixmap_row = []
    for i in range(cols):
        x = int((resolution[0] / 2) - ((ARRAY_WIDTH / 2) * PIXELMAP_SPACING) + (i * PIXELMAP_SPACING)) + PIXELMAP_SPACING/2
        y = int((resolution[1] / 2) - ((ARRAY_HEIGHT / 2) * PIXELMAP_SPACING) + (j * PIXELMAP_SPACING)) + PIXELMAP_SPACING/2
        pixmap_row.append(PixelMapPoint(x, y, PIXELMAP_SQUARE_WIDTH))
    pixmap_points.append(pixmap_row)
        
#TODO fix the offset

while rval:
    cv2.imshow("Display", frame)
    rval, frame = vc.read()
    # Draw the pixel map points on the image
    
    
    output_points = np.zeros((ARRAY_HEIGHT, ARRAY_WIDTH, 3), np.uint8)
    
    x = 0
    y = 0
    for row in pixmap_points:
        for point in row:
            avg_pix = point.get_average_pixel_value(frame)
            output_points[y, x] = [avg_pix.b, avg_pix.g, avg_pix.r]
            
            cv2.rectangle(frame, (int(point.x - (point.square_size / 2)), int(point.y - (point.square_size / 2))), (int(point.x + (point.square_size / 2)), int(point.y + (point.square_size / 2))), (0, 255, 0), 1)
            x += 1
        y += 1
        x = 0
        
    cv2.circle(frame, (int(resolution[0] / 2), int(resolution[1] / 2)), 5, (0, 0, 255), 2)
    
    cv2.imshow("Pixels", output_points)
    
    # Convert the output points to the neopixel array
    neopixel_array = [0] * (ARRAY_WIDTH * ARRAY_HEIGHT * 3)
    for y in range(ARRAY_HEIGHT):
        for x in range(ARRAY_WIDTH):
            # Output the pixels in the order GBR
            index = neopixel_array_to_index(x, y) * 3
            neopixel_array[index] = output_points[y, x][1]
            neopixel_array[index + 1] = output_points[y, x][2]
            neopixel_array[index + 2] = output_points[y, x][0]
            #print(f'The index for {x}, {y} is {index} and the value is {output_points[y, x]}')

    
    # Send the neopixel array to the arduino
    #print(bytearray(neopixel_array))

    if arduino is not None:
        
        arduino.write(bytearray(neopixel_array))

            
    key = cv2.waitKey(20)
    if key == 27: # exit on ESC
        break

vc.release()
cv2.destroyWindow("preview")