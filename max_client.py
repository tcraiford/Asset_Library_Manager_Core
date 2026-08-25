# This class file is imported by the asset_library driver, establishes connection with 3ds Max via socket
# and sends one-liner commands to 3ds Max

import socket
from pathlib import Path

class MaxClient:

    def __init__(self, host: str = "127.0.0.1", port: int = 4004):
        self.host = host
        self.port = port
        self.client = None



    def send_command(self, command: str) -> str:
        print("send command innitiated")
        try:
            # create, connect, sednd, and close immediately
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 30 second timeout. May need to make dynamic
            client.settimeout(30.0)
            client.connect((self.host, self.port))
            print("Successfully opened a a channel to 3ds Max.")

            print("Sending command to 3ds Max")
            client.sendall(command.encode("utf-8"))

            print("Command sent. Awaiting response from Max...")
            response = client.recv(4096).decode("utf-8")
            print("Response received. Closing connection.")
            client.close()
            return response
        except Exception as e:
            return f"Failed to communicate with Max: {e}"



    def create_cube(self):
        # Using a clean triple-quoted string instead of semicolons avoids exec() scope bugs
        cmd = "import pymxs\nrt = pymxs.runtime\ntest_cube = rt.Box(length=10.0, width=10.0, height=10.0, pos=rt.Point3(0,0,0), name='DUMBCUBE')\nrt.redrawViews()"

        return cmd



    def export_selected_as_max(self, file_path: str) -> str:
            clean_path = Path(file_path).as_posix()
            cmd = f'from pymxs import runtime as rt; rt.saveMaxFile("{clean_path}", selectedOnly=True)'
            return cmd

    '''def import_asset(self, file_path: str) -> str:
        path_obj = Path(file_path)
        clean_path = path_obj.as_posix()
        print(f"The clean path is: {clean_path}")
        suffix = path_obj.suffix.lower()

        if suffix == ".max":
            cmd = (f"import pymxs\nrt = pymxs.runtime\nrt.mergeMAXFile('{clean_path}', select=True, quiet=True)")


        else:
            cmd = (f"import pymxs\nrt = pymxs.runtime\nrt.FBXImporterSetParam('ShowWarnings', False)\nrt.importFile('{clean_path}', rt.Name('noPrompt'))")

        return cmd'''

    def import_asset(self, file_path: str) -> str:
        path_obj = Path(file_path)
        
        clean_path = path_obj.as_posix()
        print(f"The clean path is: {clean_path}")
        
        suffix = path_obj.suffix.lower()
        
        if suffix == ".max":
            cmd = f'import pymxs\nrt = pymxs.runtime\nrt.mergeMAXFile("{clean_path}", rt.Name("select"), quiet=True)\nrt.redrawViews()'
        else:
            cmd = f"import pymxs\nrt = pymxs.runtime\nrt.FBXImporterSetParam('ShowWarnings', False)\nrt.importFile('{clean_path}', rt.Name('noPrompt'))\nrt.redrawViews()"
            
        return cmd





