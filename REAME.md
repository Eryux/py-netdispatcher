# Python netdispatcher

Python netdispatcher is a generic class for handling and dispatch TCP socket message through your code using a callback system.

### Requirement(s)

* Python 3.x

### Usage

* Import `netdist` to your python code

* Instantiate a `NetworkListener` class

* Register your callback with `NetworkListener.add_callback`, `NetworkListener.add_client_callback.append` and `NetworkListener.del_client_callback.append`

* Start listener thread with `NetworkListener.start`

* Add client to your listener with `NetworkListener.add_client` or with the `ConnectionService` class

* Let your program running

* When you want to exit your program, unregister callback with `NetworkListener.remove_callback`, `NetworkListener.add_client_callback.remove` and `NetworkListener.add_client_callback.remove`

* Stop properly the listener with `NetworkListener.stop = True` and `NetworkListener.join`

For more details about usage, take a look to the chat example.

### Example

* Chat server : chat_server_example.py
```
usage: chat_server_example.py [-h] -l LISTEN [-v VERBOSE]

optional arguments:
  -h, --help            show this help message and exit
  -l LISTEN, --listen LISTEN
                        Listening ip:port
  -v VERBOSE, --verbose VERBOSE
                        Verbosity 0/1 (usefull for debug)
```

* /quit : Close server


* Chat client : chat_client_example.py
```
usage: chat_client_example.py [-h] -n NICKNAME -s SERVER

optional arguments:
  -h, --help            show this help message and exit
  -n NICKNAME, --nickname NICKNAME
                        Nickname
  -s SERVER, --server SERVER
                        Chat server ip:port
```

* /w or /pm [nickname] [message] : Send a private message
* /me [message] : Send an action message
* /quit : Leave chat and close client

### License

MIT License