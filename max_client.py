# This class file is imported by the asset_library driver, establishes connection with 3ds Max via socket
# and sends one-liner commands to 3ds Max

import socket
from pathlib import Path

class MaxClient:

    def __init__(self, host: str = "127.0.0.1", port: int = 4004):
        self.host = host
        self.port = port
        self.client = None



    def connect_to_max(self):
        """Establishes a single, permanent connection channel to Max"""
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.host, self.port))
            print("Successfully opened a persistent channel to 3ds Max.")
            return True
        except Exception as e:
            print(f"Failed to connect to 3ds Max: {e}")
            self.client = None
            return False

    def send_command(self, command: str) -> str:
        """Sends a command through the existing live socket"""
        if not self.client:
            raise ConnectionError("No active socket connection to 3ds Max. Call connect_to_max() first.")
        
        try:
            # Send payload down the active pipe
            self.client.sendall(command.encode("utf-8"))
            
            # Read response from the live pipe
            response = self.client.recv(4096).decode("utf-8")
            return response.strip()
        except Exception as e:
            self.disconnect_from_max()
            raise ConnectionError(f"Max communication broken: {e}")

    def disconnect_from_max(self):
        """Clean closure signal sent to Max when closing your standalone tool."""
        if self.client:
            try:
                self.client.sendall(b"DISCONNECT")
                self.client.close()
            except:
                pass
            self.client = None
            print("Disconnected socket cleanly.")



    def create_cube(self):
        cmd = ("import pymxs; " \
        "rt = pymxs.runtime; " \
        "test_cube = rt.Box(length=10.0, width=10.0, height=10.0, pos=rt.Point3(0,0,0), name='DUMBCUBE'); " \
        "rt.redrawViews()"
        )
        
        return cmd

    def export_selected_as_max(self, file_path: str) -> str:
            clean_path = Path(file_path).as_posix()
            cmd = f'from pymxs import runtime as rt; rt.saveMaxFile("{clean_path}", selectedOnly=True)'
            return cmd






