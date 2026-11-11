# This file gets coppied to the default Scripts folder of Maya and contains
# more complex methods that cannot be sent easily through the socket port
import json
import re
import shutil
from pathlib import Path
import maya.cmds as cmds


class assetLibraryTools():

    # Maps common Maya shader attributes (Standard Surface, Arnold, Lambert/Blinn)
    # to your Unreal Master Material parameter names
    CHANNEL_MAP = {
        "baseColor": "BaseColor",
        "color": "BaseColor",
        "metalness": "Metallic",
        "specularRoughness": "Roughness",
        "normalCamera": "Normal",
        "ambientOcclusion": "AO"
    }

    def collect_textures(self, new_asset_dir):
        destination_dir = Path(new_asset_dir)
        destination_tmp_dir = destination_dir / "tmp"
        destination_tmp_dir.mkdir(parents=True, exist_ok=True)

        selection = cmds.ls(sl=True) or []
        processed_nodes = set()
        copied_sources = {}      # {resolved_source_path: final_target_path}
        collected_materials = set()

        for obj in selection:
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []

            for shape in shapes:
                shading_groups = cmds.listConnections(shape, type='shadingEngine') or []

                for sg in shading_groups:
                    materials = cmds.listConnections(f'{sg}.surfaceShader') or []

                    for mat in materials:
                        collected_materials.add(mat)

                        # listHistory finds file nodes even if they pass through bump2d or aiNormalMap
                        history = cmds.listHistory(mat, pruneDagObjects=True) or []
                        file_nodes = cmds.ls(history, type='file') or []

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

        # Export the channel mapping JSON right after textures are remapped
        self.export_metadata(collected_materials, destination_dir.parent)
        cmds.ogs(reset=True)

    def export_metadata(self, materials, asset_root_dir):
        # writes metadata.json mapping each Maya material's shader slots to the remapped texture filenames.
        metadata = {"materials": {}}

        for mat in materials:
            mat_channels = {}

            for maya_attr, unreal_param in self.CHANNEL_MAP.items():
                full_attr = f"{mat}.{maya_attr}"
                if not cmds.objExists(full_attr):
                    continue

                # Check if THIS specific attribute actually has an incoming connection
                incoming = cmds.listConnections(full_attr, source=True, destination=False) or []
                if not incoming:
                    continue

                # Trace upstream ONLY from the connected node (e.g. file -> bump2d -> normalCamera)
                history = cmds.listHistory(incoming, future=False, pruneDagObjects=True) or []
                file_nodes = cmds.ls(history, type="file") or []

                if file_nodes:
                    remapped_path = cmds.getAttr(f"{file_nodes[0]}.fileTextureName")
                    if remapped_path:
                        mat_channels[unreal_param] = Path(remapped_path).name

            metadata["materials"][mat] = mat_channels

        meta_file = Path(asset_root_dir) / "metadata.json"
        meta_file.write_text(json.dumps(metadata, indent=4))
