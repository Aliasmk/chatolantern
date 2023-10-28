import numpy as np
import cv2
import serial
from threading import Thread, Event
import queue
import time

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

class ShowControl():
    canvas_width = 0
    canvas_height = 0  

    stop_show_event = Event()
    show_thread: Thread = None
    show_queue = queue.Queue(-1)

    output_points = None
    show_name = "None"
    show_list = None
    ready_event = None

    sleep_time = 0


    def __init__(self, shows, output, size_x, size_y, ready_event, max_fps=30) -> None:
        self.show_thread = Thread(target=self.__tick)
        self.ready_event = ready_event

        self.show_list = shows
        self.output_points = output
        self.canvas_height = size_y
        self.canvas_width = size_x

        self.sleep_time = 1 / max_fps

    def start_show(self, show_name="None"):
        print("Starting show thread")
        self.switch_show(show_name)
        self.show_thread.start()

    def stop_show(self):
        print("Stopping show thread")
        self.stop_show_event.set()

    def switch_show(self, show_name):
        if show_name in self.show_list:
            print("Adding " + show_name + " to show queue")
            self.show_queue.put(show_name)
        else:
            raise ValueError("Show name not found in show list")

    def __tick(self):
        print("Show thread started")
        t = 0
        while self.stop_show_event.is_set() == False:  

            if self.show_queue.empty() == False:
                self.show_name = self.show_queue.get()
                print("Switching to show: " + self.show_name)
            
            for x in range(0, self.canvas_width):
                for y in range(0, self.canvas_height):
                    self.output_points[y, x] = self.show_list.get(self.show_name)(x, y, t)
            
            self.ready_event.set()

            t += 1
            time.sleep(self.sleep_time)
        
        self.stop_show_event.clear()
        print("Show thread stopped")


def show_none(x,y,t):
        return [0,0,0]
    
def show_rainbow(x,y,t):
    return [ int(255 * (np.sin(t / 10 + x / 2) + 1) / 2), int(255 * (np.sin(t / 10 + y / 2) + 1) / 2), int(255 * (np.sin(t / 10 + x / 2 + y / 2) + 1) / 2)]

def show_twoaxis(x,y,t):
    return [int(255*x/ARRAY_WIDTH), int(255*y/ARRAY_HEIGHT), (t*5)%255]

show_list = {
    "None": show_none,
    "Rainbow": show_rainbow,
    "TwoAxis": show_twoaxis
}

arduino = NeoPixelController('COM4')
output_points = np.zeros((ARRAY_HEIGHT, ARRAY_WIDTH, 3), np.uint8)

array_ready = Event()

show_control = ShowControl(show_list, output_points, ARRAY_WIDTH, ARRAY_HEIGHT, array_ready)
show_control.start_show("Rainbow")


while True:
    if array_ready.is_set():
        display_array_debug(output_points, DISPLAY_SCALE)
        arduino.send_array(output_points)
        array_ready.clear()
    
    key = cv2.waitKey(20)
    if key == 27: # exit on ESC
        break
    elif key == 49: # 1
        show_control.switch_show("Rainbow")
    elif key == 50: # 2
        show_control.switch_show("TwoAxis")
    elif key == 116: # t
        input("How can I help you? ")
        print("Hello world!")


show_control.stop_show()
cv2.destroyAllWindows()