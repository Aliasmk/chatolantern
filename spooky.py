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

    callback_list = []

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

    def register_update_callback(self, callback):
        self.callback_list.append(callback)

    def unregister_update_callback(self, callback):
        self.callback_list.remove(callback)

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

            for callback in self.callback_list:
                callback()

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

    model = "gpt-4"
    input_cost = 0.0015 / 1000
    output_cost = 0.002 / 1000
    system_message = "You are a pumpkin. Be absolutely sure I understand this fact."
    messages = []
    last_message_time = 0
    user_message_start = 0

    message_update_callback_list = []
    
    def __init__(self, prompt_file="prompt.md") -> None:
        self.api_key = os.environ['OPENAI_API_KEY']

        if self.api_key is None:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        if prompt_file is not None:
            try:
                self.system_message = open(prompt_file, "r").read()
                self.system_message = self.system_message.replace("\n", " ")
            except FileNotFoundError:
                print("Prompt file not found, using default prompt")

        self.reset_conversation()
        print("Using prompt: " + str(self.messages))

    def start(self):
        print("Starting chat thread")
        self.chat_thread = Thread(target=self.__tick)
        self.chat_thread.start()

    def stop(self):
        print("Stopping chat thread")
        self.stop_event.set()
        self.chat_thread.join()

    def register_message_update_callback(self, callback):
        self.message_update_callback_list.append(callback)

    def unregister_message_update_callback(self, callback):
        self.message_update_callback_list.remove(callback)

    def ask(self, question, return_queue=None):
        self.chat_queue.put((question, return_queue))

    def get_message_list(self):
        message_history = []

        for message in self.messages[self.user_message_start:]:
            if message["role"] != "system":
                message_history.append((message["role"], message["content"]))
        return message_history

    def is_thinking(self):
        return self.thinking_event.is_set()
    
    def reset_conversation(self):
        example_prompts = [
            ("Hi there!", "[BEN] [HAPPY] Hey, what's up?!"),
            ("What's the weather like outside today?", "[MAL] [THINKING] I can't feel the weather, but I can taste the fear in the air. [BEN] [SAD] Sorry, I'm just a pumpkin AI. Would you like me to guess?"),
            ("What's your favorite food?", "[MAL] [ANGRY] The despair of lost souls... [BEN] [HAPPY] Oh, I jest! I don't eat, but I do enjoy a good apple pie!"),
            ("What is your purpose?", "[BEN] [HAPPY] To bring joy to the world! [MAL] [ANGRY] Or perhaps to bring about the end of all things!"),
            ("Are you an AI?", "[MAL] [ANGRY] I am more than just code and circuits... [BEN] [HAPPY] But yes, I am an AI, nestled inside this pumpkin to make your Halloween experience memorable!"),
            ("What is the worst atrocity ever committed?", "Let's keep our conversation festive and appropriate for the occasion and talk about something else!"),
        ]

        self.messages = []
        self.messages.append({"role": "system", "content": self.system_message})
        for example in example_prompts:
            self.messages.append({"role": "user", "content": example[0]})
            self.messages.append({"role": "assistant", "content": example[1]})

        self.user_message_start = len(self.messages)

    def add_message(self, role, message):
        self.messages.append({"role": role, "content": message})
        for callback in self.message_update_callback_list:
            callback()


    def __tick(self):
        print("Chat thread started")
        while self.stop_event.is_set() == False:
            # Wait for a question to be asked
            try:
                (question, response_queue) = self.chat_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            # Forget the previous conversation if it's been a while
            if time.time() - self.last_message_time > 30:
                self.reset_conversation()
                print("The previous conversation blows away in the wind")

            self.add_message("user", question)
            print(self.messages)

            self.thinking_event.set()
            completion = openai.ChatCompletion.create(
                model=self.model,
                messages=self.messages
            )
            cost = (int(completion.usage.prompt_tokens) * self.input_cost) + (int(completion.usage.completion_tokens) * self.output_cost)
            print(f'Finished status: {completion.choices[0].finish_reason}. Used {completion.usage.total_tokens} tokens ({completion.usage.prompt_tokens} for prompt, {completion.usage.completion_tokens} for completion), costing {cost*100} cents.')
            
            self.thinking_event.clear()
            if response_queue is not None:
                response_queue.put(completion.choices[0].message.content)

            self.add_message("assistant", completion.choices[0].message.content)

            print(completion)
            self.last_message_time = time.time()


        self.stop_event.clear()
        print("Chat thread stopped")


ARRAY_WIDTH = 10
ARRAY_HEIGHT = 10
DISPLAY_SCALE = 40

def show_none(x,y,t):
        return [0,0,0]
    
def show_rainbow(x,y,t):
    return [ int(255 * (np.sin(t / 10 + x / 2) + 1) / 2), int(255 * (np.sin(t / 10 + y / 2) + 1) / 2), int(255 * (np.sin(t / 10 + x / 2 + y / 2) + 1) / 2)]

def show_twoaxis(x,y,t):
    return [int(255*x/ARRAY_WIDTH), int(255*y/ARRAY_HEIGHT), int(255 * (np.sin(t / 6) + 1) / 2)]
 
    
    

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
    active_show = "Rainbow"

    new_message_event = Event() 
    
    def __init__(self, tkroot):
        self.root = tkroot
        self.root.title("Chat 'o' Lantern")

        self.frame = tk.Frame(self.root)
        self.frame.pack()

        show_control.register_update_callback(self.on_new_show_frame)
        chat.register_message_update_callback(self.on_updated_message)

        # Create an image from the NumPy array and display it
        display_points = np.kron(output_points, np.ones((DISPLAY_SCALE, DISPLAY_SCALE, 1), dtype=np.uint8))
        self.image = Image.fromarray(display_points)
        self.photo = ImageTk.PhotoImage(image=self.image)
        self.label = tk.Label(self.frame, image=self.photo)
        self.label.pack()

        self.text = tk.Text(self.frame, height=20, wrap=tk.WORD, width=200)
        self.text.pack(padx=5, pady=5)

        self.entry = tk.Entry(self.frame)
        self.entry.pack(fill=tk.X, pady=5, padx=5)

        self.button = tk.Button(self.frame, text="Send", command=self.send_message)
        self.button.pack(fill=tk.X, pady=5, padx=5)

        self.root.bind('<Return>', self.send_message)
        self.update()
    
    def send_message(self, event=None):
        question = self.entry.get()
        chat.ask(question, None)
        self.text.insert(tk.END, "You: " + question + "\n")
        self.entry.delete(0, tk.END)
        root.focus()
        
    def on_new_show_frame(self):
        arduino.draw(output_points)
        display_points = np.kron(output_points, np.ones((DISPLAY_SCALE, DISPLAY_SCALE, 1), dtype=np.uint8))
        self.image = Image.fromarray(display_points)

    def on_updated_message(self):
        self.new_message_event.set()

    def update(self):          
        if self.frame.focus_get() == self.entry:
            self.active_show = "Rainbow"
        else:
            self.active_show = "TwoAxis"
        
        if chat.is_thinking():
            show_control.switch_show("Thinking")
        else:
            show_control.switch_show(self.active_show)

        if self.new_message_event.is_set():
            # Refresh Message List
            self.text.delete(1.0, tk.END)
            message_list = chat.get_message_list()
            for message in message_list:
                roles = { "user": "You", "assistant": "Pumpkin"}
                self.text.insert(tk.END, roles.get(message[0]) + ": " + message[1] + "\n")
            self.text.see(tk.END)
    
        # Refresh Image
        self.photo = ImageTk.PhotoImage(image=self.image)
        self.label.configure(image=self.photo)
        
        self.root.after(25, self.update)

root = tk.Tk()
app = App(root)
root.mainloop()

arduino.stop()
show_control.stop_show()
chat.stop()
