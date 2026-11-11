# This file gets coppied to the default Scripts folder of Maya and contains
# more complex methods that cannot be sent easily through the socket port
import re
import maya.cmds as cmds
import shutil
from pathlib import Path

class assetLibraryTools():

    def collect_textures(self, new_asset_dir):
        destination_dir = Path(new_asset_dir)
        destination_tmp_dir = destination_dir / "tmp"
        destination_tmp_dir.mkdir(parents=True, exist_ok=True)

        selection = cmds.ls(sl=True) or []
        processed_nodes = set()
        copied_sources = {}  # {resolved_source_path: final_target_path}

        for obj in selection:
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []

            for shape in shapes:
                shading_groups = cmds.listConnections(shape, type='shadingEngine') or []

                for sg in shading_groups:
                    materials = cmds.listConnections(f'{sg}.surfaceShader') or []

                    for mat in materials:
                        file_nodes = cmds.listConnections(mat, type='file') or []

                        for file_node in file_nodes:
                            if file_node in processed_nodes:
                                continue
                            processed_nodes.add(file_node)

                            old_path_str = cmds.getAttr(f'{file_node}.fileTextureName')
                            if not old_path_str:
                                continue

                            old_path = Path(old_path_str)
                            if not old_path.exists():
                                cmds.warning(f"Source texture missing: {old_path}")
                                continue

                            resolved_src = old_path.resolve()
                            if resolved_src in copied_sources:
                                final_path = copied_sources[resolved_src]
                                cmds.setAttr(f'{file_node}.fileTextureName', final_path.as_posix(), type="string")
                                continue

                            # Strip any existing "_1_1_1" bloat from previous buggy runs
                            clean_stem = re.sub(r'(_1)+$', '', old_path.stem)
                            extension = old_path.suffix
                            file_name = f"{clean_stem}{extension}"
                            tmp_path = destination_tmp_dir / file_name

                            counter = 1
                            while tmp_path.exists():
                                file_name = f"{clean_stem}_{counter}{extension}"
                                tmp_path = destination_tmp_dir / file_name
                                counter += 1

                            final_path = destination_dir / file_name

                            try:
                                shutil.copy2(old_path, tmp_path)
                                copied_sources[resolved_src] = final_path
                                cmds.setAttr(f'{file_node}.fileTextureName', final_path.as_posix(), type="string")
                            except Exception as e:
                                cmds.warning(f"Failed to copy {old_path}: {e}")

        cmds.ogs(reset=True)

    ''' Semi Working
    def collect_textures(self, new_asset_dir):
        destination_dir = Path(new_asset_dir)
        destination_tmp_dir = destination_dir / "tmp"
        destination_tmp_dir.mkdir(parents=True, exist_ok=True)

        selection = cmds.ls(sl=True) or []
        processed_nodes = set()
        copied_sources = {}  # {resolved_source_path: final_target_path}

        for obj in selection:
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []

            for shape in shapes:
                shading_groups = cmds.listConnections(shape, type='shadingEngine') or []

                for sg in shading_groups:
                    materials = cmds.listConnections(f'{sg}.surfaceShader') or []

                    for mat in materials:
                        file_nodes = cmds.listConnections(mat, type='file') or []

                        for file_node in file_nodes:
                            if file_node in processed_nodes:
                                continue
                            processed_nodes.add(file_node)

                            old_path_str = cmds.getAttr(f'{file_node}.fileTextureName')
                            if not old_path_str:
                                continue

                            old_path = Path(old_path_str)
                            if not old_path.exists():
                                cmds.warning(f"Source texture missing: {old_path}")
                                continue

                            # If another file node points to the exact same source file, reuse its target path
                            resolved_src = old_path.resolve()
                            if resolved_src in copied_sources:
                                final_path = copied_sources[resolved_src]
                                cmds.setAttr(f'{file_node}.fileTextureName', final_path.as_posix(), type="string")
                                continue

                            base_name = old_path.stem
                            extension = old_path.suffix
                            file_name = f"{base_name}{extension}"
                            tmp_path = destination_tmp_dir / file_name

                            # Check collisions ONLY inside the clean tmp folder
                            counter = 1
                            while tmp_path.exists():
                                file_name = f"{base_name}_{counter}{extension}"
                                tmp_path = destination_tmp_dir / file_name
                                counter += 1

                            final_path = destination_dir / file_name

                            try:
                                shutil.copy2(old_path, tmp_path)
                                copied_sources[resolved_src] = final_path
                                cmds.setAttr(f'{file_node}.fileTextureName', final_path.as_posix(), type="string")
                            except Exception as e:
                                cmds.warning(f"Failed to copy {old_path}: {e}")

        cmds.ogs(reset=True)
'''

    ''' OLD
    def collect_textures(self, new_asset_dir):
        destination_dir = Path(new_asset_dir)
        destination_tmp_dir = destination_dir / "tmp"
        selection = cmds.ls(sl=True) or []
                
        for obj in selection:
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
                    
            for shape in shapes:
                shading_groups = cmds.listConnections(shape, type='shadingEngine') or []
                        
                for sg in shading_groups:
                    # Fixed the invalid syntax and tuple evaluation here
                    materials = cmds.listConnections(f'{sg}.surfaceShader') or []
                    print(f"Found materials: {materials}")
                            
                    for mat in materials:
                        file_nodes = cmds.listConnections(mat, type='file') or []
                            
                        for file_node in file_nodes:
                            old_path_str = cmds.getAttr(f'{file_node}.fileTextureName')
                            if not old_path_str:
                                continue
                                        
                            old_path = Path(old_path_str)
                            base_name = old_path.stem
                            extension = old_path.suffix
                            new_path = destination_dir / f"{base_name}{extension}"
                                    
                            counter = 1
                            while new_path.exists():
                                new_path = destination_dir / f"{base_name}_{counter}{extension}"
                                counter += 1
                                        
                            try:
                                shutil.copy2(old_path, new_path)
                                cmds.setAttr(f'{file_node}.fileTextureName', str(new_path), type="string")
                            except Exception as e:
                                cmds.warning(f"Failed to copy {old_path}: {e}")
        cmds.ogs(reset=True)'''



    def make_cube(self):
         cmds.polyCube(d=20, h=20, w=50)