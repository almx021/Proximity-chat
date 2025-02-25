from typing import TypeAlias

import math
import Pyro5.api
import Pyro5.server
import tkinter as tk

user_data: TypeAlias = dict[str, tuple[float, float]]


class Server(object):
    def __init__(self, daemon):
        self.__daemon = daemon
        self.__active_users:  user_data = {}

    @Pyro5.api.expose
    def add_user(self, data: user_data):
        if data.keys() <= self.__active_users.keys():
            return False
        self.__active_users.update(data)
        return self.__active_users

    @Pyro5.api.expose
    def update_user(self, data: user_data):
        self.__active_users.update(data)

    @Pyro5.api.expose
    def release_user(self, user):
        del self.__active_users[user]

    @Pyro5.api.expose
    def get_nearby_users(self, username, location):
        referential_latitude, referential_longitude = location
        nearby_users = []

        METERS_PER_DEGREE_OF_LATITUDE = 111320
        METERS_PER_DEGREE_OF_LONGITUDE = METERS_PER_DEGREE_OF_LATITUDE * math.cos(math.radians(referential_latitude))
        for user, position in self.__active_users.items():
            if user == username:
                continue

            delta_lat = (position[0] - referential_latitude) * METERS_PER_DEGREE_OF_LATITUDE
            delta_long = (position[1] - referential_longitude) * METERS_PER_DEGREE_OF_LONGITUDE

            distance = math.sqrt(delta_lat**2 + delta_long**2)
            if distance <= 200:
                nearby_users.append(user)
                
        return nearby_users

if __name__ == '__main__':
    with Pyro5.api.Daemon('localhost') as daemon:
        with Pyro5.api.locate_ns('localhost') as ns:
            server = Server(daemon)
            uri = daemon.register(server)
            ns.register("server", uri)
            print(f"Server Ready. URI: {uri}")
            daemon.requestLoop()
            daemon.close()