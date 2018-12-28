# coding: utf8
"""
MIT License

Copyright (c) 2018, Candia Nicolas

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

import socket
import select
import time

from threading import Thread

def print_verbose(msg, level):
    if level > 0:
        print(msg)
				
class NetworkListener(Thread):

    def __init__(self):
        Thread.__init__(self)

        self.verbose = 0

        self.sock = None
        self.clients = []

        self.callbacks = {}
        self.add_client_callback = []
        self.del_client_callback = []

        self.delta_time = 1.0 / 60
        self.stop = False

    def add_callback(self, m_type, call_function):
        if m_type not in self.callbacks:
            self.callbacks[m_type] = []
        self.callbacks[m_type].append(call_function)

    def remove_callback(self, m_type, call_function):
        if m_type in self.callbacks:
            if call_function in self.callbacks[m_type]:
                self.callbacks[m_type].remove(call_function)

    def add_client(self, client):
        self.clients.append(client)
        for c in self.add_client_callback:
            c(client, self)

    def remove_client(self, client, close = True):
        if client not in self.clients:
            return

        for c in self.del_client_callback:
            c(client, self)

        if close:
            try:
                client.shutdown(socket.SHUT_RDWR)
                client.close()
            except IOError:
                pass

            print_verbose("Client disconnected.", self.verbose)

        self.clients.remove(client)

    def remove_all(self):
        for c in self.clients:
            self.remove_client(c)
        
    def run(self):
        print_verbose("Listener service start ...", self.verbose)

        while not self.stop:
            start = time.time()

            if self.sock is None or not self.clients:
                time.sleep(1)
                continue

            r_c, w_c, e_c = select.select(self.clients, self.clients, [], 1)

            for reader in r_c:
                try:
                    b_data = reader.recv(1024)
                    if not b_data:
                        self.remove_client(reader)
                    else:
                        self.dispatch(b_data, reader)
                except ConnectionResetError:
                    self.remove_client(reader)
                except ConnectionAbortedError:
                    self.remove_client(reader)
                except IOError:
                    pass

            for error in e_c:
                self.remove_client(error)

            time.sleep(max(self.delta_time - (time.time() - start), 0))

        print_verbose("Listener service stoped", self.verbose)

    def dispatch(self, message, sock_from):
        msg_type = message[0]
        if msg_type not in self.callbacks:
            return

        for c in self.callbacks[msg_type]:
            c(message, sock_from, self)

    def send_to_many(self, receivers, message):
        r_c, w_c, e_c = select.select(receivers, receivers, [], 1)

        for writer in w_c:
            writer.send(message)

    def send_to_one(self, receiver, message):
        receiver.send(message)

class ConnectionService(Thread):

    def __init__(self, host, port, listener):
        Thread.__init__(self)

        self.verbose = 0

        self.port = port
        self.host = host
        self.listener = listener

        self.sock = None
        self.stop = False

    def connect_client(self, client):
        print_verbose("Client connected.", self.verbose)
        self.listener.add_client(client)

    def run(self):
        print_verbose("Connection service start ...", self.verbose)
		
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind((self.host, int(self.port)))
            self.sock.setblocking(0)
            self.sock.listen(5)
            self.listener.sock = self.sock
        except IOError as e:
            print_verbose("Connection service start failed !\n" + e.errno + " : " + e.strerror, self.verbose)
            return
        
        print_verbose("Waiting for client", self.verbose)
        while not self.stop:
            try:
                client, address = self.sock.accept()
                self.connect_client(client)
            except IOError:
                pass
            time.sleep(1)

        print_verbose("Stopping connection service ...", self.verbose)