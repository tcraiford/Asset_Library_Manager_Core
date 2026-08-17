from pathlib import Path
import socket
import shutil


class MayaClient:
    """Manages raw TCP socket communication with Autodesk Maya's command port."""
    def __init__(self, host: str = "127.0.0.1", port: int = 7002):
        self.host = host
        self.port = port
        self.collect_file_path = ""



    def test_maya_connection(self) -> bool:
        """Briefly opens a socket to check if Maya's port is listening."""
        try:
            with socket.create_connection((self.host, self.port), timeout=2.0) as client:

                cmd = "print('Maya connection test successful');"
                cmd_final = cmd.encode("utf-8") + b"\n"  # makes sure command ends with newline
                client.sendall(cmd_final)
                cmd = 'import maya.cmds as cmds; import os'
                cmd_final = cmd.encode("utf-8") + b"\n"
                client.sendall(cmd_final)
                return True
        except (socket.timeout, ConnectionRefusedError):
            return False


    def send_command(self, command: str) -> str:
        """Sends a Python string command to Maya and returns the string response."""
        try:
            with socket.create_connection((self.host, self.port), timeout=2.0) as client:
                client.settimeout(30) # allows a half min length of time for a file export but will fail if it takes longer
                # Maya expects commands terminated by a newline
                client.sendall(f"{command}\n".encode("utf-8"))
                
                # get response from Maya
                response = client.recv(4096).decode("utf-8")
                # remove any trailing null bytes from Maya's response
                response = response.replace("\x00", "")
                #print the response from Maya to the console for debugging purposes 
                #print(response)
                return response.strip()
        except Exception as e:
            raise ConnectionError(f"Maya communication timed out: {e}")


    def export_selected_to_fbx(self, file_path: str) -> str:
        # changes the file path to a string with forward slashes so that Maya can read it correctly
        clean_path = Path(file_path).as_posix()

        # exports selected objects in Maya to the specified file path
        cmd = f'cmds.file("{clean_path}", force=True, type="FBX export", exportSelected=True)'
        return cmd

    def export_selected_to_ma(self, file_path: str) -> str:
        clean_path = Path(file_path).as_posix()

        cmd = f'cmds.file("{clean_path}", force=True, type="mayaAscii", exportSelected=True)'
        return cmd

    # render out the thumbnail
    def render_thumbnail(self) -> str:
        # renders the thumbnail and saves it to wherever the project directory is set for the Maya session
        cmd = f'cmds.setAttr("defaultRenderGlobals.imageFormat", 8); cmds.render(["persp"], x=512, y=512)'
        return cmd

    def get_maya_project_directory(self) -> str:
        # gets the set directory for the Maya project and returns it as a string
        cmd = 'cmds.workspace(q=True, rd=True)'
        return cmd

    def create_ambient_light(self) -> str:
        # remembers the current selection, creates the light, then reselects what was previously selected
        cmd = "selection = cmds.ls(selection=True); print(selection); cmds.ambientLight(intensity=10, name='L_Render'); cmds.select('L_Render'); cmds.move(0, 100, 0); cmds.select(selection)"
        return cmd

    def delete_ambient_light(self) -> str:
        # delete the ambient light
        cmd = "cmds.delete('L_Render')"
        return cmd

    def determine_if_selected(self):
        # determines if anything is selected
        cmd = 'bool(cmds.ls(selection=True))'
        return cmd

    def reference_file(self, file_dir: str) -> str:
        if file_dir is None:
            return
        # changes the file path to a string with forward slashes so that Maya can read it correctly
        file_dir = Path(file_dir)
        clean_namespace = file_dir.stem
        clean_path = file_dir.as_posix()
        cmd = f'cmds.file("{clean_path}", reference = True, namespace = "{clean_namespace}")'
        return cmd

    def get_file_name(self):
        # returns the file name of the maya file that is open
        cmd = 'cmds.file(q=True, sn=True)'
        return cmd

    def collect_textures(self, new_asset_dir):
        new_asset_dir= str(Path(new_asset_dir).as_posix())
        cmd= f"import importlib; import maya_scripts; importlib.reload(maya_scripts); assetToolScript = maya_scripts.assetLibraryTools(); assetToolScript.collect_textures('{new_asset_dir}')"
        return cmd

    def test_button(self):
        print('sending instructions to open maya_scripts')
        cmd = f"import importlib; import maya_scripts; importlib.reload(maya_scripts); assetToolScript = maya_scripts.assetLibraryTools(); assetToolScript.make_cube()"
        print('sent instructions')

        return cmd