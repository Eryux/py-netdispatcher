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

import argparse
import struct

from netdisp import NetworkListener, ConnectionService


class Chat_User:

    def __init__(self, sock):
        self.nickname = ''
        self.sock = sock
        self.joined = False

class Chat_Server:

    def __init__(self, network):
        self.network = network
        self.users = []

        self.register_callback()

    def register_callback(self):
        self.network.add_client_callback.append(self.on_user_connect)
        self.network.del_client_callback.append(self.on_user_disconnect)
        self.network.add_callback(10, self.on_user_join)
        self.network.add_callback(20, self.on_message_recv)

    def unregister_callback(self):
        self.network.add_client_callback.remove(self.on_user_connect)
        self.network.del_client_callback.remove(self.on_user_disconnect)
        self.network.remove_callback(10, self.on_user_join)
        self.network.remove_callback(20, self.on_message_recv)

    def action_send_message(self, from_user, message):
        if from_user is not None:
            message = "{0} : {1}".format(from_user.nickname, message)

        print(message)

        encoded_message = message.encode('utf-8')
        data = struct.pack('<ci{0}s'.format(len(encoded_message)), bytes([30]), len(encoded_message), encoded_message)
        target = [u.sock for u in self.users if u.joined]

        if len(target) > 0:
            try:
                self.network.send_to_many(target, data)
            except IOError as e:
                print("{0} : {1}".format(e.errno, e.strerror))

    def action_send_private_message(self, from_user, to_user, message):
        print("From {0} to {1} : {2}".format(from_user.nickname, to_user.nickname, message))

        encoded_message = "From {0} : {1}".format(from_user.nickname, message).encode('utf-8')
        data = struct.pack('<ci{0}s'.format(len(encoded_message)), bytes([30]), len(encoded_message), encoded_message)

        try:
            self.network.send_to_one(to_user.sock, data)
        except IOError as e:
            print("{0} : {1}".format(e.errno, e.strerror))

        encoded_message = "To {0} : {1}".format(to_user.nickname, message).encode('utf-8')
        data = struct.pack('<ci{0}s'.format(len(encoded_message)), bytes([30]), len(encoded_message), encoded_message)

        try:
            self.network.send_to_one(from_user.sock, data)
        except IOError as e:
            print("{0} : {1}".format(e.errno, e.strerror))

    def action_invalid_nickname(self, client):
        data = struct.pack('c', bytes([15]))

        try:
            self.network.send_to_one(client, data)
        except IOError as e:
            print("{0} : {1}".format(e.errno, e.strerror))

    def on_user_connect(self, client, network):
        self.users.append(Chat_User(client))

    def on_user_disconnect(self, client, network):
        user = self.get_user_by_sock(client)
        if user is not None and user in self.users:
            self.users.remove(user)
            self.action_send_message(None, "{0} disconnected.".format(user.nickname))

    def on_user_join(self, data, client, network):
        user = self.get_user_by_sock(client)

        if user is None:
            return

        try:
            message_len = struct.unpack('<i', data[1:5])[0] # Size of message is an integer on 4 bytes
            encoded_nickname = struct.unpack('{0}s'.format(message_len), data[5::])[0]
            nickname = encoded_nickname.decode('utf-8')

            # Verify if nickname is valid (if isn't already used by another user)
            used_nickname = [u.nickname for u in self.users]
            if nickname in used_nickname:
                self.action_invalid_nickname(user.sock)
                self.users.remove(user)
            else:
                user.nickname = nickname
                user.joined = True
                self.action_send_message(None, "{0} joined the chat".format(nickname))
        except struct.error as e:
            print(e)

    def on_message_recv(self, data, client, network):
        from_user = self.get_user_by_sock(client)

        if from_user is None or from_user.joined is False:
            return

        message = ''

        try:
            message_len = struct.unpack('<i', data[1:5])[0]
            encoded_message = struct.unpack('{0}s'.format(message_len), data[5::])[0]
            message = encoded_message.decode('utf-8')
        except struct.error as e:
            print(e)
            return

        if len(message) > 0:
            if message[0] == '/': # Has command
                args = message.split(' ')

                if (args[0] == '/w' or args[0] == '/pm') and len(args) > 1: # Private message
                    to_user = self.get_user_by_nickname(args[1])
                    if to_user is not None:
                        message = message[(len(args[0]) + len(args[1]) + 2)::]
                        self.action_send_private_message(from_user, to_user, message)
                elif args[0] == '/me': # Action message
                    message = '* {0} {1} * '.format(from_user.nickname, message[(len(args[0]) + 1)::])
                    self.action_send_message(None, message)
                elif args[0] == '/quit': # Quit command, do nothing
                    pass
                else:
                    self.action_send_message(from_user, message)
            else:
                self.action_send_message(from_user, message)

    def get_user_by_nickname(self, nickname):
        for u in self.users:
            if u.nickname == nickname:
                return u
        return None

    def get_user_by_sock(self, sock):
        for u in self.users:
            if u.sock == sock:
                return u
        return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--listen', type=str, help='Listening ip:port', required=True)
    parser.add_argument('-v', '--verbose', type=int, help='Verbosity 0/1 (usefull for debug)', default=0)
    args = parser.parse_args()

    # -------------------------------------------
    
    ip, port = args.listen.split(':')

    listener = NetworkListener()
    listener.verbose = args.verbose
    listener.start()

    chat = Chat_Server(listener)

    conn = ConnectionService(ip, int(port), listener)
    conn.verbose = args.verbose
    conn.start()

    print("Server started at {0} on port {1}".format(ip, port))

    command = ""
    while command != "/quit":
        command = input("")

    # Stopping server
    chat.action_send_message(None, "Chat server shutting down")
    chat.unregister_callback()

    listener.stop = True
    listener.join()

    conn.stop = True
    conn.join()