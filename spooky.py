import numpy as np
import cv2
import serial
from threading import Thread, Event
import queue
import time

import os
import openai

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
        self.show_thread.join()

    def switch_show(self, show_name):
        if self.show_name == show_name:
            return

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



class Chat_Interface():
    chat_thread: Thread = None
    chat_queue = queue.Queue(1)
    stop_event = Event()

    thinking_event = Event()

    model = "gpt-3.5-turbo"
    system_message = "You are a pumpkin. Be absolutely sure I understand this fact."
    messages = []
    last_message_time = 0
    
    def __init__(self) -> None:
        self.api_key = os.environ['OPENAI_API_KEY']

    def start(self):
        print("Starting chat thread")
        self.chat_thread = Thread(target=self.__tick)
        self.chat_thread.start()

    def stop(self):
        print("Stopping chat thread")
        self.stop_event.set()
        self.chat_thread.join()

    def ask(self, question):
        if time.time() - self.last_message_time > 30:
            # Forget the previous conversation if it's been a while
            self.messages = []
            self.messages.append({"role": "system", "content": self.system_message})

        self.messages.append({"role": "user", "content": question})
        
        self.thinking_event.set()
        completion = openai.ChatCompletion.create(
            model=self.model,
            messages=self.messages
        )
        self.thinking_event.clear()

        self.messages.append({"role": "assistant", "content":  completion.choices[0].message.content})
        self.last_message_time = time.time()
        return completion.choices[0].message.content
    
    def is_thinking(self):
        return self.thinking_event.is_set()

    def __tick(self):
        # Not amazing because it's blocking, but it's fine for now
        print("Chat thread started")
        while self.stop_event.is_set() == False:
            question = input("How can I help you? ")
            if question != "cancel":
                print(self.ask(question))

        self.stop_event.clear()
        print("Chat thread stopped")





def show_none(x,y,t):
        return [0,0,0]
    
def show_rainbow(x,y,t):
    return [ int(255 * (np.sin(t / 10 + x / 2) + 1) / 2), int(255 * (np.sin(t / 10 + y / 2) + 1) / 2), int(255 * (np.sin(t / 10 + x / 2 + y / 2) + 1) / 2)]

def show_twoaxis(x,y,t):
    return [int(255*x/ARRAY_WIDTH), int(255*y/ARRAY_HEIGHT), (t*5)%255]

def show_pulse_white(x,y,t):
    brightness = 100
    return [int(brightness * (np.sin(t) + 1) / 2), int(brightness * (np.sin(t) + 1) / 2), int(brightness * (np.sin(t) + 1) / 2)]

show_list = {
    "None": show_none,
    "Rainbow": show_rainbow,
    "TwoAxis": show_twoaxis,
    "Thinking": show_pulse_white
}

arduino = NeoPixelController('COM4')
output_points = np.zeros((ARRAY_HEIGHT, ARRAY_WIDTH, 3), np.uint8)

array_ready = Event()

show_control = ShowControl(show_list, output_points, ARRAY_WIDTH, ARRAY_HEIGHT, array_ready)
show_control.start_show("Rainbow")

chat = Chat_Interface()
chat.start()

while True:
    if array_ready.is_set():
        display_array_debug(output_points, DISPLAY_SCALE)
        arduino.send_array(output_points)
        array_ready.clear()

    if chat.is_thinking():
        show_control.switch_show("Thinking")
    else :
        show_control.switch_show("Rainbow")

    
    key = cv2.waitKey(20)
    if key == 27: # exit on ESC
        break
    elif key == 49: # 1
        show_control.switch_show("Rainbow")
    elif key == 50: # 2
        show_control.switch_show("TwoAxis")


show_control.stop_show()
chat.stop()
cv2.destroyAllWindows()
