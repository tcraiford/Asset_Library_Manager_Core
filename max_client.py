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
            cmd = f'from pymxs import runtime as rt\nrt.saveMaxFile("{clean_path}", selectedOnly=True)'
            return cmd

    def export_selected_as_fbx(self, file_path: str) -> str:
        clean_path = Path(file_path).as_posix()
        cmd = f'import pymxs\npymxs.runtime.FBXExporterSetParam("ResetExport")\npymxs.runtime.exportFile("{clean_path}", pymxs.runtime.Name("noPrompt"), selectedOnly=True, using=pymxs.runtime.FBXEXP)'
        return cmd

    def render_thumbnail(self, file_path):
        file_path_object = Path(file_path)
        filename_path = file_path_object / "thumbnail.jpg"
        clean_path = filename_path.as_posix()

        # uses the scanline render
        cmd = f"import pymxs\nrt = pymxs.runtime\nrt.renderers.current = rt.Default_Scanline_Renderer()\nrt.render(outputSize=rt.Point2(512, 512), outputFile='{clean_path}', vfb=False)"

        return cmd

    def collect_textures(self, file_path):
        clean_path = file_path.as_posix()

        # get current file location so max knows where to load the max_scripts.py class from
        # do this instead of having to inject the class file into a scripts folder like we did for Maya
        current_tool_dir = Path(__file__).resolve().parent.as_posix()

        cmd = f"import sys, importlib\nsys.path.append('{current_tool_dir}') if '{current_tool_dir}' not in sys.path else None\nimport max_scripts\nimportlib.reload(max_scripts)\nmax_scripts.repath_selected_textures('{clean_path}')"
        return cmd


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

    def zoom_extents(self):
        cmd = 'import pymxs\npymxs.runtime.execute("max tool zoomextents")'

        return cmd




