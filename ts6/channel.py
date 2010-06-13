#!/usr/bin/env python

class Channel:
    def __init__(self, name, modes):
        self.name = name
        self.modes = modes
        self.topic = ''
        self.clients = []

    def joined(self, client):
        self.clients.append(client)
        for c in self.clients:
            if not c.conn:
                continue
            c.userJoined(client, self)

    def parted(self, client, message):
        self.clients.remove(client)
        for c in self.clients:
            if not c.conn:
                continue
            c.userParted(client, self, message)
