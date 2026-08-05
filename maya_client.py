import socket


class MayaClient:
    """Manages raw TCP socket communication with Autodesk Maya's command port."""
    def __init__(self, host: str = "127.0.0.1", port: int = 7002):
        self.host = host
        self.port = port

    def class_test(self, i_take_input):
        print(f"MayaClient class is working correctly. Input received: {i_take_input}")

    def test_maya_connection(self) -> bool:
        """Briefly opens a socket to check if Maya's port is listening."""
        try:
            with socket.create_connection((self.host, self.port), timeout=2.0) as client:
                #cmd = "print('JUJU WORKS!')"
                cmd = "print('Maya connection test successful'); print('JUJU WORKS!')"
                cmd_final = cmd.encode("utf-8") + b"\n"  # Ensure command ends with newline
                client.sendall(cmd_final)
                return True
        except (socket.timeout, ConnectionRefusedError):
            return False


    def send_command(self, command: str) -> str:
        """Sends a Python string command to Maya and returns the string response."""
        try:
            with socket.create_connection((self.host, self.port), timeout=2.0) as client:
                # Maya expects commands terminated by a newline
                client.sendall(f"{command}\n".encode("utf-8"))
                
                # Fetch response from Maya (optional, but good for error catching)
                response = client.recv(4096).decode("utf-8")
                return response.strip()
        except Exception as e:
            raise ConnectionError(f"Failed to communicate with Maya: {e}")