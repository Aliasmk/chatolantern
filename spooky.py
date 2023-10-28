import numpy as np
import serial
from threading import Thread, Event
import queue
import time

import os
import openai

import tkinter as tk
from PIL import Image, ImageTk

class NeoPixelController(Thread):
    controller_serial = None

    array_queue = queue.Queue(1)
    stop_event = Event()
    
    def __init__(self, com_port) -> None:
        super().__init__()
        self.controller_serial = serial.Serial(com_port, 230400, timeout=.5)
        if self.controller_serial is None:
            raise ValueError("Serial port not found")
        
    def stop(self):
        self.stop_event.set()

    def neopixel_array_to_index(self, x, y, width, height):
        return ((width * y) + x)
    
    def draw(self, array):
        self.array_queue.put(array)
    
    def run(self):
        print("Starting NeoPixel thread")
        while self.stop_event.is_set() == False:
            
            output_array: np.ndarray = None
            try:
                output_array = self.array_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            array_width = output_array.shape[1]
            array_height = output_array.shape[0]
            
            neopixel_array = [0] * (array_width * array_height * 3)
            for y in range(array_height):
                for x in range(array_width):
                    # Output the pixels in the order GBR
                    index = self.neopixel_array_to_index(x, y, array_width, array_height) * 3
                    neopixel_array[index] = output_array[y, x][1]
                    neopixel_array[index + 1] = output_array[y, x][2]
                    neopixel_array[index + 2] = output_array[y, x][0]
            
            self.controller_serial.write(bytearray(neopixel_array))
        
        self.stop_event.clear()
        print("Stopped NeoPixel thread")

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


    def __init__(self, shows, output, size_x, size_y, max_fps=30) -> None:
        self.show_thread = Thread(target=self.__tick)

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
                self.show_name = self.show_queue.get(timeout=1)
                print("Switching to show: " + self.show_name)
            
            for x in range(0, self.canvas_width):
                for y in range(0, self.canvas_height):
                    self.output_points[y, x] = self.show_list.get(self.show_name)(x, y, t)

            t += 1
            time.sleep(self.sleep_time)
        
        self.stop_show_event.clear()
        print("Show thread stopped")



class Chat_Interface():
    chat_thread: Thread = None
    chat_queue = queue.Queue(1)
    stop_event = Event()

    thinking_event = Event()
    answer_ready_event = Event()

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

    def ask(self, question, return_queue):
        self.chat_queue.put((question, return_queue))
    
    def is_thinking(self):
        return self.thinking_event.is_set()

    def __tick(self):
        # Not amazing because it's blocking, but it's fine for now
        print("Chat thread started")
        while self.stop_event.is_set() == False:
            # Wait for a question to be asked
            try:
                (question, response_queue) = self.chat_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            # Forget the previous conversation if it's been a while
            if time.time() - self.last_message_time > 30:
                
                self.messages = []
                self.messages.append({"role": "system", "content": self.system_message})

            self.messages.append({"role": "user", "content": question})
            
            self.thinking_event.set()
            completion = openai.ChatCompletion.create(
                model=self.model,
                messages=self.messages
            )
            self.thinking_event.clear()
            response_queue.put(completion.choices[0].message.content)

            self.messages.append({"role": "assistant", "content":  completion.choices[0].message.content})
            self.last_message_time = time.time()


        self.stop_event.clear()
        print("Chat thread stopped")


ARRAY_WIDTH = 10
ARRAY_HEIGHT = 10
DISPLAY_SCALE = 20

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


output_points = np.zeros((ARRAY_HEIGHT, ARRAY_WIDTH, 3), np.uint8)
arduino = NeoPixelController('COM4')
arduino.start()

show_control = ShowControl(show_list, output_points, ARRAY_WIDTH, ARRAY_HEIGHT)
show_control.start_show("Rainbow")

chat = Chat_Interface()
chat.start()

class App:
    response_queue = queue.Queue(1)
    
    def __init__(self, tkroot):
        self.root = tkroot
        self.root.title("Chat 'o' Lantern")

        self.frame = tk.Frame(self.root)
        self.frame.pack()

        # Create an image from the NumPy array and display it
        display_points = np.kron(output_points, np.ones((10, 10, 1), dtype=np.uint8))
        self.image = Image.fromarray(display_points)
        self.photo = ImageTk.PhotoImage(image=self.image)
        self.label = tk.Label(self.frame, image=self.photo)
        self.label.pack()

        self.text = tk.Text(self.frame, height=10)
        self.text.pack(padx=5, pady=5)

        self.entry = tk.Entry(self.frame)
        self.entry.pack(fill=tk.X, pady=5, padx=5)

        self.button = tk.Button(self.frame, text="Send", command=self.send_message)
        self.button.pack(fill=tk.X, pady=5, padx=5)

        self.root.bind('<Return>', self.send_message)
        self.update()
    
    def send_message(self, event=None):
        question = self.entry.get()
        self.text.insert(tk.END, "You: " + question + "\n")
        chat.ask(question, self.response_queue)
        self.entry.delete(0, tk.END)
        show_control.switch_show("Thinking")

    def update(self):          
        if self.response_queue.empty() == False:
            response = self.response_queue.get()
            self.text.insert(tk.END, "Pumpkin: " + response + "\n")
            show_control.switch_show("Rainbow")
        
        display_points = np.kron(output_points, np.ones((DISPLAY_SCALE, DISPLAY_SCALE, 1), dtype=np.uint8))
        self.image = Image.fromarray(display_points)
        self.photo = ImageTk.PhotoImage(image=self.image)
        self.label.configure(image=self.photo)

        arduino.draw(output_points)

        self.root.after(25, self.update)


root = tk.Tk()
app = App(root)
root.mainloop()

arduino.stop()
show_control.stop_show()
chat.stop()
