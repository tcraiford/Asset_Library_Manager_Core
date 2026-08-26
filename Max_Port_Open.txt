# creates a counter and ++ the counter each time a command comes through
# counter can be checked by entering this command into 3ds Max's scripting Editor
'''
print(MAX_SOCKET_COUNT)

    '''

import socket
import pymxs
import traceback
import os
from PySide6 import QtCore

# initialize a diagnostic counter globally
# use this to manually test if 3ds max is receiving commands
global MAX_SOCKET_COUNT
MAX_SOCKET_COUNT = 0

if hasattr(pymxs, '_socket_timer'):
    try:
        pymxs._socket_timer.stop()
        pymxs._socket_timer.timeout.disconnect()
    except Exception:
        pass

# innitialize the server to receive commands
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('127.0.0.1', 4004))
server.listen(1)
server.setblocking(False)

def check_socket_tick():
    global MAX_SOCKET_COUNT
    try:
        client_conn, addr = server.accept()
        data = client_conn.recv(4096).decode("utf-8").strip()
        
        # does max see the code being sent in?
        if data:
            MAX_SOCKET_COUNT += 1  # increment the counter immediately
            
            try:
                exec(data, globals())
                client_conn.sendall(b"Success")
            except Exception as e:
                # if the string failed to execute, put a file on the Desktop
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                with open(os.path.join(desktop, "max_socket_error.txt"), "w") as f:
                    f.write(traceback.format_exc())
                client_conn.sendall(f"Crash: {str(e)}".encode("utf-8"))
            finally:
                # force the connection closed so library tool can't freeze
                try:
                    client_conn.shutdown(socket.SHUT_WR)
                    client_conn.close()
                except Exception:
                    pass
    except BlockingIOError:
        pass

pymxs._socket_timer = QtCore.QTimer()
pymxs._socket_timer.timeout.connect(check_socket_tick)
pymxs._socket_timer.start(100)

print("Awaiting commands via socket port...")
