import shutil
import hashlib
from pathlib import Path
import pymxs

current_tool_dir = r"C:\Users\traiford\Desktop\Work\0Personal\AssetLibraryTool"
clean_path = r"C:\Users\traiford\Desktop\Work\0Personal\AssetLibraryTool\Asset_Library\Environment\Buildings\a\TEXTURES"
clean_path = Path(clean_path).as_posix()

# Convert the texture file to a hash and compare it to any other textures that share the same name
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
    for node in selected_nodes:
        if node.material:
            scene_materials.add(node.material)

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
        # FIX: Get the true class object using rt.classOf()
        bmp_class = rt.classOf(bmp)
        class_name = str(bmp_class).lower() # Safely handles the object-to-string format

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

        # --- CONFLICT RESOLUTION LOGIC ---
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
            # Explicit destination file path inside the tmp folder
            file_target = tmp_file_path / target_path.name
            
            # Copy to root first
            if not skip_copy:
                shutil.copy2(full_path, target_path)
                print(f"Successfully copied: {target_path.name}")

            # FIX: Remap using the class evaluations we verified above
            if bmp_class == rt.BitmapTex:
                bmp.filename = target_path.as_posix()
                print(f"Remapped Standard slot to: {target_path.name}")
            elif (hasattr(rt, "VRayBitmap") and bmp_class == rt.VRayBitmap) or \
                 (hasattr(rt, "VRayHDRI") and bmp_class == rt.VRayHDRI):
                bmp.HDRIMapName = target_path.as_posix()
                print(f"Remapped V-Ray slot to: {target_path.name}")

            # Safely move this processed file to the isolation chamber
            shutil.move(target_path, file_target)

        except Exception as e:
            print(f"Failed processing {full_path.name}: {str(e)}")
