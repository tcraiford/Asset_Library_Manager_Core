# This class file is imported by asset_library.py and establishes a connection with Unreal Engine and sends Unreal commands via socket
# NOTE: This class relies on the remote_execution module, which is not included in this repository. The remote_execution module is part of the Unreal Engine Python API and is used to communicate with Unreal Engine over a network socket.
# If you do not have Unreal Engine installed, this class will not be able to connect to Unreal Engine and will not be able to send commands but will still allow you to work with Maya and 3ds Max

from pathlib import Path
import time

try: # if the remote_execution module is not in the main driver directory, then it will not load and unreal commands will be unavailable. This is a workaround to allow the Asset Library Tool to run without Unreal Engine installed. 
    import remote_execution as remote
except ImportError:
    print("remote execution try failed")
    remote = None

class UnrealClient:

    def __init__(self, multicast_ip="239.0.0.1", multicast_port=6766, bind_ip="127.0.0.1"):
        # if the remote_execution module is not available, this allows the UnrealClient class to be instantiated without throwing an error, but it will not be able to connect to Unreal Engine.
        self.remote_exec = None
        if remote is None:
            self.config = None
            print("remote_execution module not found. UnrealClient __init__ failed.")
            return
        # if the remote_execution module is available, this sets up the configuration for the UnrealClient class to connect to Unreal Engine.
        self.config = remote.RemoteExecutionConfig()
        self.config.multicast_group_endpoint = (multicast_ip, multicast_port)
        self.config.multicast_bind_address = bind_ip
        self.remote_exec = None

    def is_available(self):
        # returns True if the remote_execution module is available, otherwise returns False.
        return remote is not None and self.config is not None

    def connect(self, timeout=1.0):
        # starts the listener, discovers active unreal instances, and opens a command channel
        self.remote_exec = remote.RemoteExecution(self.config)
        self.remote_exec.start()


        # returns True if a remote node is found within the timeout period, otherwise returns False
        start_time = time.time()
        while not self.remote_exec.remote_nodes:
            if time.time() - start_time > timeout:
                self.disconnect()
                return False
            time.sleep(0.1)

        target_node = self.remote_exec.remote_nodes[0]
        self.remote_exec.open_command_connection(target_node["node_id"])
        return True

    # attempt to connect to Unreal Engine and send a command. If connection fails, return an error message. Always disconnect after sending the command, regardless of success or failure.
    def send_command(self, command: str) -> str:
        if not self.connect():
            return "Failed to connect to Unreal Engine."

        try:
            response = self.remote_exec.run_command(command, unattended=True, exec_mode=remote.MODE_EXEC_FILE)
            return response

        finally: # disconnect from Unreal Engine after sending the command, regardless of success or failure
            self.disconnect()

    def disconnect(self):
        # closes the command connection and stops the remote execution listener
        if self.remote_exec:
            self.remote_exec.close_command_connection()
            self.remote_exec.stop()
            self.remote_exec = None

    def send_asset_to_unreal(
        self,
        asset_name: str,
        fbx_path: str,
        master_mat_path: str = "/Game/Assets/M_AssetLibrary_Master"
    ):
        fbx_path_obj = Path(fbx_path)
        clean_fbx = fbx_path_obj.as_posix()
        clean_tex_dir = (fbx_path_obj.parent / "TEXTURES").as_posix()

        cmd = ( # this is the command that will be sent to Unreal Engine to import the asset. It is a Python script that will be executed in Unreal Engine's Python environment. It was built and tested in unreal before being implemented here
            "import unreal, json, re, traceback\n"
            "from pathlib import Path\n"
            "def norm_key(name):\n"
            "    return re.sub(r'[^a-zA-Z0-9]', '', str(name)).lower()\n"
            "def sanitize_ue_name(name):\n"
            "    return re.sub(r'[^a-zA-Z0-9_]', '_', str(name))\n"
            "def import_library_asset(asset_name, fbx_path, textures_dir, master_mat_path):\n"
            "    base_dest = f'/Game/Assets/{asset_name}'\n"
            "    tex_dest = f'{base_dest}/Textures'\n"
            "    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()\n"
            "    meta_file = Path(fbx_path).parent / 'metadata.json'\n"
            "    meta_data = json.loads(meta_file.read_text()) if meta_file.exists() else {}\n"
            "    raw_materials_meta = meta_data.get('materials', {})\n"
            "    materials_meta = {norm_key(k): v for k, v in raw_materials_meta.items()}\n"
            "    tex_tasks = []\n"
            "    if Path(textures_dir).exists():\n"
            "        for tex_file in Path(textures_dir).glob('*.*'):\n"
            "            if tex_file.is_file():\n"
            "                task = unreal.AssetImportTask()\n"
            "                task.filename = str(tex_file)\n"
            "                task.destination_path = tex_dest\n"
            "                task.automated = True\n"
            "                task.save = True\n"
            "                tex_tasks.append(task)\n"
            "    if tex_tasks:\n"
            "        asset_tools.import_asset_tasks(tex_tasks)\n"
            "    imported_tex_map = {}\n"
            "    if unreal.EditorAssetLibrary.does_directory_exist(tex_dest):\n"
            "        for asset_path in unreal.EditorAssetLibrary.list_assets(tex_dest, recursive=False):\n"
            "            tex_obj = unreal.EditorAssetLibrary.load_asset(asset_path)\n"
            "            if isinstance(tex_obj, unreal.Texture2D):\n"
            "                import_data = tex_obj.get_editor_property('asset_import_data')\n"
            "                src_file = import_data.get_first_filename() if import_data else ''\n"
            "                if src_file:\n"
            "                    imported_tex_map[Path(src_file).name] = tex_obj\n"
            "                imported_tex_map[tex_obj.get_name()] = tex_obj\n"
            "    fbx_options = unreal.FbxImportUI()\n"
            "    fbx_options.import_mesh = True\n"
            "    fbx_options.import_materials = False\n"
            "    fbx_options.import_textures = False\n"
            "    fbx_options.static_mesh_import_data.combine_meshes = False\n"
            "    fbx_options.static_mesh_import_data.build_nanite = True\n"
            "    mesh_task = unreal.AssetImportTask()\n"
            "    mesh_task.filename = str(fbx_path)\n"
            "    mesh_task.destination_path = base_dest\n"
            "    mesh_task.automated = True\n"
            "    mesh_task.save = True\n"
            "    mesh_task.options = fbx_options\n"
            "    asset_tools.import_asset_tasks([mesh_task])\n"
            "    master_mat = unreal.EditorAssetLibrary.load_asset(master_mat_path)\n"
            "    if not master_mat:\n"
            "        unreal.log_error(f'Master Material not found at: {master_mat_path}')\n"
            "        return\n"
            "    mi_factory = unreal.MaterialInstanceConstantFactoryNew()\n"
            "    base_assets = unreal.EditorAssetLibrary.list_assets(base_dest, recursive=False) if unreal.EditorAssetLibrary.does_directory_exist(base_dest) else []\n"
            "    for obj_path in base_assets:\n"
            "        static_mesh = unreal.EditorAssetLibrary.load_asset(obj_path)\n"
            "        if not isinstance(static_mesh, unreal.StaticMesh):\n"
            "            continue\n"
            "        static_materials = static_mesh.get_editor_property('static_materials')\n"
            "        for slot_index, static_mat in enumerate(static_materials):\n"
            "            slot_name = str(static_mat.material_slot_name)\n"
            "            clean_slot_name = sanitize_ue_name(slot_name)\n"
            "            mi_name = f'MI_{asset_name}_{clean_slot_name}'\n"
            "            mi_path = f'{base_dest}/{mi_name}'\n"
            "            mi_asset = unreal.EditorAssetLibrary.load_asset(mi_path)\n"
            "            if not mi_asset:\n"
            "                mi_asset = asset_tools.create_asset(mi_name, base_dest, unreal.MaterialInstanceConstant, mi_factory)\n"
            "            if mi_asset:\n"
            "                mi_asset.set_editor_property('parent', master_mat)\n"
            "                slot_textures = materials_meta.get(norm_key(slot_name), {})\n"
            "                unreal.log(f'Slot [{slot_name}] matched textures: {slot_textures}')\n"
            "                for channel, tex_filename in slot_textures.items():\n"
            "                    tex_obj = imported_tex_map.get(tex_filename) or imported_tex_map.get(Path(tex_filename).stem)\n"
            "                    if tex_obj:\n"
            "                        if channel in ('Normal', 'Roughness', 'Metallic', 'AO'):\n"
            "                            tex_obj.set_editor_property('srgb', False)\n"
            "                            if channel == 'Normal':\n"
            "                                tex_obj.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)\n"
            "                            unreal.EditorAssetLibrary.save_loaded_asset(tex_obj)\n"
            "                        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi_asset, channel, tex_obj)\n"
            "                        unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(mi_asset, f'Use_{channel}_Map', True)\n"
            "                unreal.EditorAssetLibrary.save_loaded_asset(mi_asset)\n"
            "                static_mesh.set_material(slot_index, mi_asset)\n"
            "        unreal.EditorAssetLibrary.save_loaded_asset(static_mesh)\n"
            "try:\n"
            f"    import_library_asset('{asset_name}', '{clean_fbx}', '{clean_tex_dir}', '{master_mat_path}')\n"
            "except Exception:\n"
            "    unreal.log_error(traceback.format_exc())\n"
            "    print(traceback.format_exc())\n"
        )

        print(f"Sending import command to Unreal for: {clean_fbx}")
        return self.send_command(cmd)