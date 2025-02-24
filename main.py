from paho.mqtt import client as mqtt
from random import randint
from threading import Thread
from time import sleep
from tkinter.scrolledtext import ScrolledText

import Pyro5.api
import Pyro5.server
import tkinter as tk

class User:
    BGCOLOR = '#243256'
    DEFAULT_BOLD_FONT_12 = ("TkDefaultFont", 12, "bold")
    DEFAULT_BOLD_FONT_16 = ("TkDefaultFont", 16, "bold")
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Proximity chat")
        self.root.geometry("800x600")
        self.root.configure(bg=User.BGCOLOR)
        self.root.protocol("WM_DELETE_WINDOW", self.finish)
        
        self.validator = root.register(self._validate_number)

        self._username = ''
        self.__current_chat = None
        self.__connected = False

        self.load_application()
 
    def show_error_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        error_Frame = tk.Frame(self.root, bg=User.BGCOLOR)
        error_Frame.pack(expand=True)

        tk.Label(error_Frame, text="It was not possible to connect", bg=User.BGCOLOR, fg='white', font=User.DEFAULT_BOLD_FONT_16).pack()

    def show_start_screen(self, position=None):
        lat, lon = None, None
        if position:
            lat, lon = position
        for widget in self.root.winfo_children():
            widget.destroy()

        self.start_frame = tk.Frame(self.root, bg=User.BGCOLOR)
        self.start_frame.pack(expand=True)

        username_frame = tk.Frame(self.start_frame, bg=User.BGCOLOR)
        username_frame.pack(anchor='w')
        username_label = tk.Label(username_frame, text="USERNAME", anchor="w", bg=User.BGCOLOR, fg='white', font=User.DEFAULT_BOLD_FONT_12)
        username_label.pack(side=tk.LEFT)
        username_input = tk.Entry(username_frame)
        username_input.pack(padx=7, side=tk.LEFT)

        latitude_frame = tk.Frame(self.start_frame, bg=User.BGCOLOR)
        latitude_frame.pack(pady=10, anchor='w')
        latitude_label = tk.Label(latitude_frame, text="LATITUDE", anchor="w", bg=User.BGCOLOR, fg='white', font=User.DEFAULT_BOLD_FONT_12)
        latitude_label.pack(side=tk.LEFT)
        latitude_input = tk.Entry(latitude_frame, validate="key", validatecommand=(self.validator, "%P"))
        latitude_input.pack(padx=20, side=tk.LEFT)
        if lat:
            latitude_input.insert(0, lat)

        longitude_frame = tk.Frame(self.start_frame, bg=User.BGCOLOR)
        longitude_frame.pack(anchor='w')
        longitude_label = tk.Label(longitude_frame, text="LONGITUDE", anchor="w", bg=User.BGCOLOR, fg='white', font=User.DEFAULT_BOLD_FONT_12)
        longitude_label.pack(side=tk.LEFT)
        longitude_input = tk.Entry(longitude_frame, validate="key", validatecommand=(self.validator, "%P"))
        longitude_input.pack(padx=5, side=tk.LEFT)
        if lon:
            longitude_input.insert(0, lon)

        enter_button = tk.Button(self.start_frame, text="START", font=("Arial", 12, "bold"), command=lambda: self.login(username_input.get(), latitude_input.get(), longitude_input.get()))
        enter_button.pack(pady=20)

    def load_application(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        text_list = ("Loading.", "Loading..", "Loading...")
        idx = 0

        loading_frame = tk.Frame(self.root, bg="#243256")
        loading_frame.pack(expand=True)       

        loading_label = tk.Label(loading_frame, text="", font=("Arial", 16, "bold"), bg="#243256", fg="white")
        loading_label.pack()

        def update_text():
            nonlocal idx
            if not self.__connected:
                loading_label.config(text=text_list[idx])
                idx = (idx + 1) % len(text_list)
                root.after(500, update_text) 
            elif self.__connected == 1:
                self.server._pyroClaimOwnership()
                self.show_start_screen()
            elif self.__connected == 2:
                self.show_error_screen()
                
        Thread(target=self.connect, daemon=True).start()
        update_text()

    def login(self, username: str, latitude: str, longitude: str):
        if any([
            username.strip() == '',
            latitude.strip() == '',
            longitude.strip() == ''
        ]):
            return
        
        self._username = username.strip()
        self.set_location(latitude, longitude)

        login_ok = self.server.add_user({self.get_username(): self.get_location()})
        if not login_ok:
            self.__connected = 2
            self._username = None
            self.show_start_screen(self.get_location())
            self._current_latitude = None
            self._current_longitude = None
            warning_label = tk.Label(self.start_frame, text='INVALID USERNAME', fg='red', bg=User.BGCOLOR, font=User.DEFAULT_BOLD_FONT_12)
            warning_label.pack()
            return
        
        self.show_main_screen()
        Thread(target=self._check_location, daemon=True).start()

    def show_main_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.main_frame = tk.Frame(root, bg=User.BGCOLOR)
        self.main_frame.pack(fill=tk.BOTH)

        menu_frame = tk.Frame(self.main_frame, bg=User.BGCOLOR)
        menu_frame.pack(side=tk.LEFT, fill=tk.Y)

        contact_list_frame = tk.Frame(menu_frame, bg=User.BGCOLOR)
        contact_list_frame.pack(side=tk.TOP, fill=tk.Y)

        contact_list_info_label = tk.Label(contact_list_frame, text="CONTACTS", bg=User.BGCOLOR, fg="WHITE", font=User.DEFAULT_BOLD_FONT_12)
        contact_list_info_label.pack(side=tk.TOP, fill=tk.Y, pady=1)

        self.contacts_array = []
        self.contact_list = tk.Listbox(contact_list_frame, width=30, height=21)
        self.contact_list.bind("<<ListboxSelect>>", self.open_chat)
        self.contact_list.bind("<Button-1>", self._block_null)
        self.contact_list.pack(side=tk.TOP, fill=tk.Y, padx=10, pady=10)

        self.lat_long_frame = tk.Frame(menu_frame, bg=User.BGCOLOR)
        self.lat_long_frame.pack()

        latitude, longitude = self.get_location()

        self.latitude_label = tk.Label(self.lat_long_frame, text="LATITUDE", bg=User.BGCOLOR, fg='white', font=User.DEFAULT_BOLD_FONT_12)
        self.latitude_label.pack()
        self.latitude_entry = tk.Entry(self.lat_long_frame, validate="key", validatecommand=(self.validator, "%P"))
        self.latitude_entry.bind("<Return>", self.update_location)
        self.latitude_entry.insert(0, latitude)
        self.latitude_entry.pack()

        self.longitude_label = tk.Label(self.lat_long_frame, text="LONGITUDE", fg='white', bg=User.BGCOLOR, font=User.DEFAULT_BOLD_FONT_12)
        self.longitude_label.pack(pady=(5, 0))
        
        self.longitude_entry = tk.Entry(self.lat_long_frame, validate="key", validatecommand=(self.validator, "%P"))
        self.longitude_entry.bind("<Return>", self.update_location)
        self.longitude_entry.insert(0, longitude)
        self.longitude_entry.pack()

        self.lat_long_button = tk.Button(self.lat_long_frame, text="Update location", command=self.update_location)
        self.lat_long_button.pack(pady=10)

        self.lat_long_button = tk.Button(self.lat_long_frame, text="Reset location", command=self.reset_location)
        self.lat_long_button.pack()

        self.update_contact_list()

    def _block_null(self, event):
        index = self.contact_list.nearest(event.y)
        if self.contact_list.get(index) == '':
            self.contact_list.selection_clear(index)
            if self.__current_chat:
                self.contact_list.selection_set(self.__current_chat[0])
            return "break"

    def _validate_number(self, value):
        return value.replace(".", "", 1).isdigit() or value == ""

    def generate_chat(self):
        self.chat_box_frame = tk.Frame(self.main_frame, bg=User.BGCOLOR)
        self.chat_box_frame.pack(side=tk.LEFT, fill=tk.BOTH)

        chat_box_label = tk.Label(self.chat_box_frame, text="CHAT", bg=User.BGCOLOR, fg="WHITE", font=User.DEFAULT_BOLD_FONT_12)
        chat_box_label.pack(side=tk.TOP, fill=tk.Y, pady=1)

        self.chat_box = ScrolledText(self.chat_box_frame, width=68, height=30)
        self.chat_box.pack(side=tk.TOP, fill=tk.BOTH, pady=10)
        self.chat_box.config(state='disabled')

        self.input_frame = tk.Frame(self.chat_box_frame, bg=User.BGCOLOR, width=58)
        self.input_frame.pack(side=tk.TOP, fill=tk.X, anchor='w')

        self.input_entry = tk.Entry(self.input_frame, font=("Roboto", 10))
        self.input_entry.bind("<Return>", self._send_message)
        self.input_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        send_button = tk.Button(self.input_frame, text="Send", command=self._send_message)
        send_button.pack(side=tk.RIGHT, padx=5, pady=5)

    def _send_message(self, event=None):
        message = self.input_entry.get().strip()
        if message == '':
            return
        
        self.input_entry.delete(0, tk.END)
        self.write_message(message, True)

    def write_message(self, message, message_sender=False):
        sender = "FRIEND" if not message_sender else "YOU"

        self.chat_box.config(state="normal")

        if len(self.chat_box.get('1.0', '1.2')) > 1 and self.chat_box.get(tk.END) != '\n':
            self.chat_box.insert(tk.END, '\n')
        self.chat_box.insert(tk.END, f"{sender}: {message}")

        self.chat_box.config(state="disabled")
        self.chat_box.see(tk.END)

    def open_chat(self, event):
        selector = self.contact_list.curselection()
        if selector:
            index = selector[0]
            value = self.contact_list.get(index)
            if (value == '') or (self.__current_chat is not None and self.__current_chat[1] == value):
                return
            if hasattr(self, "chat_box_frame"):
                self.chat_box_frame.destroy()

            self.__current_chat = [index, value]
            self.generate_chat()

    def _check_location(self):
        while True:
            sleep(120)
            self.update_location()

    def update_location(self):
        lat, long = self.latitude_entry.get(), self.longitude_entry.get()

        if lat.strip() == '' or long.strip() == '':
            self.reset_location()
            return

        self.set_location(lat, long)
        self.server.update_user({self.get_username(): self.get_location()})
        self.update_contact_list()

    def reset_location(self):
        self.latitude_entry.delete(0, tk.END)
        self.latitude_entry.insert(0, self.get_location()[0])
        self.longitude_entry.delete(0, tk.END)
        self.longitude_entry.insert(0, self.get_location()[1])

    def update_contact_list(self):
        users = self.get_reachable_users()
        self.contact_list.delete(0, tk.END)
        self.contact_list.insert(tk.END, *users)
    
    def get_reachable_users(self) -> dict:
        users = self.server.get_nearby_users(self.get_username(), self.get_location())
        users.append('')
        return users

    def connect(self):
        try:
            self.daemon = Pyro5.server.Daemon('localhost')
            self.ns = Pyro5.api.locate_ns('localhost')
            self.uri = self.daemon.register(self)
            self.ns.register("client" + str(randint(0, 1000)), self.uri)

            self.server = Pyro5.api.Proxy("PYRONAME:server")
            self.server._Proxy__pyroCreateConnection()
        except Exception:
            self.__connected = 2
            return

        self.daemon_thread = Thread(target=self._listener_thread, args=(), daemon=True)
        self.daemon_thread.start()
        
        self.__connected = 1

    def _listener_thread(self):
        self.daemon.requestLoop()
        self.daemon.close()

    def finish(self):
        self.root.destroy()
        if hasattr(self, 'server') and self.__connected not in (None, 2):
            self.server.release_user(self.get_username())
            self.server._pyroRelease()

    def get_username(self):
        return self._username

    def get_location(self, as_string=False):
        if as_string:
            return str(self._current_latitude), str(self._current_longitude)
        return self._current_latitude, self._current_longitude

    def set_location(self, latitude, longitude):
        self._current_latitude = float(latitude)
        self._current_longitude = float(longitude)

if __name__ == '__main__':
    root = tk.Tk()
    User(root)
    root.mainloop()