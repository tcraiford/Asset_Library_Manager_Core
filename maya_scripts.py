# This file gets coppied to the default Scripts folder of Maya and contains
# more complex methods that cannot be sent easily through the socket port
import maya.cmds as cmds
import shutil
from pathlib import Path

class assetLibraryTools():


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
        cmds.ogs(reset=True)



    def make_cube(self):
         cmds.polyCube(d=20, h=20, w=50)