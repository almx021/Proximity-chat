# Proximity Chat

# Requirements
- Python 3.12 or superior
- Pyro5 (run `pip install Pyro5`)
- Redis-py (run `pip install redis`)
- A Redis broker running on localhost:6379

# How to Run
**Disclaimer**: The keyword `python` must be understood as _the keyword to access python in your O.S._. For instance, if you are running `Debian`, it must be understood as `python3`

- Open a terminal on root folder and run `python -m Pyro5.nameserver` once
- Open a terminal on root folder and run `python server.py` once
- Open any terminals on root folder and run as many `python main.py` as you want. These are your app clients that will communicate with each other
- The latitude, longitude distances are calculated as a simulation of real distances, meaning that any latitude/longitude longer than 0.001 from you target lat/lon will make it past the 200 meters range that's necessary to communicate with another client

## Stopping the application
- To finish the application, close all open tkinter windows and press `Ctrl+C` on the command lines that are running the server and the pyro nameserver