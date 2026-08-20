# This class file is imported by the asset_library driver, establishes connection with 3ds Max via socket
# and sends one-liner commands to 3ds Max

import socket

class MaxClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 4004):
        self.host = host
        self.port = port

    def test_max_connection(self):
        try:
            with socket.create_connection((self.host, self.port), timeout=2.0) as client:
                cmd = "print('3ds Max connection test successful')"
                cmd_final = cmd.encode("utf-8") + b"\n"
                client.sendall(cmd_final)

                cmd = 'import pymxs; import os'
                cmd_final = cmd.encode("utf-8") + b"\n"
                client.sendall(cmd_final)

                return True
        except (socket.timeout, ConnectionRefusedError):
            return False

        def send_command(self, command: str) -> str:
            """Sends a Python string command to Max and returns the string response."""
            try:
                with socket.create_connection((self.host, self.port), timeout=30.0) as client:
                    client.sendall(f"{command}\n".encode("utf-8"))

                    #get response from Max
                    response = client.recv(4096).decode("utf-8")
                    # remove any trailing null bytes from Maya's response
                    response = response.replace("\x00", "")
                    response = response.replace("\r", "")
                    return response.strip()
            except Exception as e:
                raise ConnectionError(f"Max communication timed out: {e}")