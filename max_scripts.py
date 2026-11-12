import shutil
import json
import hashlib
from pathlib import Path
import pymxs


# maps 3ds Max PhysicalMaterial and VRayMtl texture properties to your Unreal Master Material parameters
MAX_CHANNEL_MAP = {
    "base_color_map": "BaseColor",               # PhysicalMaterial
    "texmap_diffuse": "BaseColor",               # VRayMtl
    "diffuseMap": "BaseColor",                   # Standardmaterial
    "metalness_map": "Metallic",                 # PhysicalMaterial
    "texmap_metalness": "Metallic",              # VRayMtl
    "roughness_map": "Roughness",                # PhysicalMaterial
    "texmap_reflectionGlossiness": "Roughness",  # VRayMtl
    "bump_map": "Normal",                        # PhysicalMaterial
    "texmap_bump": "Normal",                     # VRayMtl
    "bumpMap": "Normal",                         # Standardmaterial
    "ao_map": "AO"                               # PhysicalMaterial
}


# Convert the texture file to a hash and compare it to any other textures that share the same name
# This is to handle duplicate texture names that are actually different files. If the hash is the same, we can skip copying the file and just remap the material to the existing texture.
def get_file_hash(file_path: Path):
    hasher = hashlib.md5()
    try:
        with file_path.open('rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None


# Iterate the file names to have a number value at the end for duplicates
def generate_unique_path(destination_folder: Path, filename: str) -> Path:
    orig_path = destination_folder / filename
    if not orig_path.exists():
        return orig_path
    
    counter = 1
    name = orig_path.stem
    ext = orig_path.suffix
    new_path = destination_folder / f"{name}_{counter:03d}{ext}"
    
    while new_path.exists():
        counter += 1
        new_path = destination_folder / f"{name}_{counter:03d}{ext}"
    return new_path


def _collect_leaf_materials(mat, collected_set):
    # unwrap multi and sub-Object materials so individual sub-materials are recorded.
    if not mat:
        return
    rt = pymxs.runtime
    if rt.classOf(mat) == rt.Multimaterial:
        for sub_mat in mat.materialList:
            _collect_leaf_materials(sub_mat, collected_set)
    else:
        collected_set.add(mat)


def _extract_bitmap_filename(tex_map):
    #unwraps normal map nodes and extracts the remapped filename.
    if not tex_map:
        return None
    rt = pymxs.runtime

    # unnwrap Normal_Bump or VRayNormalMap wrapper nodes if present
    if rt.isProperty(tex_map, "normal_map") and tex_map.normal_map:
        tex_map = tex_map.normal_map
    elif rt.isProperty(tex_map, "normalMap") and tex_map.normalMap:
        tex_map = tex_map.normalMap

    bmp_class = rt.classOf(tex_map)
    if bmp_class == rt.BitmapTex and tex_map.filename:
        return Path(tex_map.filename).name
    elif hasattr(rt, "VRayBitmap") and bmp_class == rt.VRayBitmap and tex_map.HDRIMapName:
        return Path(tex_map.HDRIMapName).name
    elif hasattr(rt, "VRayHDRI") and bmp_class == rt.VRayHDRI and tex_map.HDRIMapName:
        return Path(tex_map.HDRIMapName).name

    return None


def export_max_metadata(materials_set, asset_root_dir: Path):
    # writes metadata.json matching the format used by Maya and Unreal
    rt = pymxs.runtime
    metadata = {"materials": {}}

    for mat in materials_set:
        if not mat:
            continue

        mat_channels = {}
        for max_prop, unreal_param in MAX_CHANNEL_MAP.items():
            if not rt.isProperty(mat, max_prop):
                continue

            tex_map = rt.getProperty(mat, max_prop)
            remapped_filename = _extract_bitmap_filename(tex_map)

            if remapped_filename:
                mat_channels[unreal_param] = remapped_filename

        metadata["materials"][mat.name] = mat_channels

    meta_file = asset_root_dir / "metadata.json"
    meta_file.write_text(json.dumps(metadata, indent=4))
    print(f"Exported metadata.json to: {meta_file}")


# Points the material shaders to the new location where the texture files will be stored
def repath_selected_textures(destination_folder_str):
    rt = pymxs.runtime
    selected_nodes = list(rt.selection)
    if not selected_nodes:
        print("Nothing selected in 3ds Max.")
        return

    destination_folder = Path(destination_folder_str)
    destination_folder.mkdir(parents=True, exist_ok=True)

    # 1. Gather all materials assigned to the current selection
    scene_materials = set()
    leaf_materials = set()
    for node in selected_nodes:
        if node.material:
            scene_materials.add(node.material)
            _collect_leaf_materials(node.material, leaf_materials)

    # 2. Extract each Bitmap texture instance hidden inside those materials
    all_bitmaps = []
    for mat in scene_materials:
        standard_instances = rt.getClassInstances(rt.BitmapTex, target=mat)
        all_bitmaps.extend(list(standard_instances))
        
        # Find V-Ray bitmaps safely
        if hasattr(rt, "VRayBitmap"):
            vray_instances = rt.getClassInstances(rt.VRayBitmap, target=mat)
            all_bitmaps.extend(list(vray_instances))
        elif hasattr(rt, "VRayHDRI"): 
            vray_hdri_instances = rt.getClassInstances(rt.VRayHDRI, target=mat)
            all_bitmaps.extend(list(vray_hdri_instances))

    # Define and create the tmp directory
    tmp_file_path = destination_folder / "tmp"
    tmp_file_path.mkdir(parents=True, exist_ok=True)

    # Deduplicate the texture instances list
    all_bitmaps = list(set(all_bitmaps))

    # 3. Process, copy, and remap each individual texture file
    for bmp in all_bitmaps:
        bmp_class = rt.classOf(bmp)

        # Check what property name this specific node type uses based on its class
        if bmp_class == rt.BitmapTex:
            full_path_str = bmp.filename
        elif hasattr(rt, "VRayBitmap") and bmp_class == rt.VRayBitmap:
            full_path_str = bmp.HDRIMapName
        elif hasattr(rt, "VRayHDRI") and bmp_class == rt.VRayHDRI:
            full_path_str = bmp.HDRIMapName
        else:
            continue

        if not full_path_str:
            continue
            
        full_path = Path(full_path_str)
        if not full_path.exists():
            print(f"Warning: Missing source file {full_path}")
            continue

        target_path = destination_folder / full_path.name
        skip_copy = False

        if target_path.exists():
            if full_path.resolve() == target_path.resolve():
                continue
            
            if get_file_hash(full_path) == get_file_hash(target_path):
                skip_copy = True
                print(f"Texture identical, skipping copy: {full_path.name}")
            else:
                target_path = generate_unique_path(destination_folder, full_path.name)
                print(f"Name collision resolved. Renaming to: {target_path.name}")

        try:
            # specific destination file path inside the tmp folder
            file_target = tmp_file_path / target_path.name
            
            # Copy to root first
            if not skip_copy:
                shutil.copy2(full_path, target_path)
                print(f"Successfully copied: {target_path.name}")

            if bmp_class == rt.BitmapTex:
                bmp.filename = target_path.as_posix()
                print(f"Remapped Standard slot to: {target_path.name}")
            elif (hasattr(rt, "VRayBitmap") and bmp_class == rt.VRayBitmap) or \
                 (hasattr(rt, "VRayHDRI") and bmp_class == rt.VRayHDRI):
                bmp.HDRIMapName = target_path.as_posix()
                print(f"Remapped V-Ray slot to: {target_path.name}")

            shutil.move(target_path, file_target)

        except Exception as e:
            print(f"Failed processing {full_path.name}: {str(e)}")

    # 4. Write metadata.json into the parent asset folder right after remapping finishes
    export_max_metadata(leaf_materials, destination_folder.parent)