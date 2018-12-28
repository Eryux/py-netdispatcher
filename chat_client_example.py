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
import socket
import struct

from netdisp import NetworkListener


class Chat_Client:

    def __init__(self, nickname):
        self.nickname = nickname
        self.server = None

        self.network = NetworkListener()

    def register_callback(self):
        self.network.add_callback(15, self.on_invalid_nickname)
        self.network.add_callback(30, self.on_message_recv)

    def unregister_callback(self):
        self.network.add_callback(15, self.on_invalid_nickname)
        self.network.remove_callback(30, self.on_message_recv)

    def connect(self, ip, port):
        print("Connect to chat server ... ", end="")

        try:
            self.register_callback()
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.connect((ip, port))
        except IOError as e:
            print("{0} : {1}".format(e.errno, e.strerror))
            exit(1)

        print("connected")

        self.network.sock = self.server
        self.network.add_client(self.server)
        self.network.start()

        self.action_join_chat()

    def disconnect(self):
        if self.server is None:
            return
        
        self.unregister_callback()
        self.network.stop = True

        try:
            self.network.join()
        except:
            pass

        try:
            self.server.close()
        except IOError:
            pass
        
        self.server = None

        print("Disconnected from chat server")

    def action_join_chat(self):
        if self.server is None:
            return
            
        print("Joining chat ...")
        print("Write /quit for exiting the chat")

        encoded_nickname = self.nickname.encode('utf-8')
        data = struct.pack('<ci{0}s'.format(len(encoded_nickname)), bytes([10]), len(encoded_nickname), encoded_nickname)
        
        try:
            self.network.send_to_one(self.server, data)
        except IOError as e:
            print("{0} : {1}".format(e.errno, e.strerror))
            self.disconnect()
            exit(1)

    def action_send_message(self, message):
        if self.server is None:
            return

        encoded_message = message.encode('utf-8')
        data = struct.pack('<ci{0}s'.format(len(encoded_message)), bytes([20]), len(encoded_message), encoded_message)

        try:
            self.network.send_to_one(self.server, data)
        except IOError as e:
            print("{0} : {1}".format(e.errno, e.strerror))
            self.disconnect()
            exit(1)

    def on_message_recv(self, data, sender, network):
        try:
            message_len = struct.unpack('<i', data[1:5])[0] # Size of message is an integer on 4 bytes
            encoded_message = struct.unpack('{0}s'.format(message_len), data[5::])[0]
            print(encoded_message.decode('utf-8'))
        except struct.error as e:
            print(e)

    def on_invalid_nickname(self, data, sender, network):
        print("You're nickname isn't valid or somebody already has you're nickname in chat server.")
        self.disconnect()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--nickname', type=str, help='Nickname', required=True)
    parser.add_argument('-s', '--server', type=str, help='Chat server ip:port', required=True)
    args = parser.parse_args()

    # -------------------------------------------

    chat = Chat_Client(args.nickname)

    # Connect to chat server
    ip, port = args.server.split(':')
    chat.connect(ip, int(port))

    # Sending message or quit
    message = ""
    while message != "/quit":
        message = input("")
        chat.action_send_message(message)

    # Disconnect from chat
    chat.disconnect()