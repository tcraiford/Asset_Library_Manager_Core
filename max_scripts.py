import shutil
import hashlib
from pathlib import Path
import pymxs

# convert the textrue file to a hash and compare it to any other textures that share the same name
# this is useful in case you have two different versions of a texture that share the same name
# ie a concrete that is rough, named concrete.jpg and a concrete that is smooth, named concrete.jpg
def get_file_hash(file_path: Path):
    hasher = hashlib.md5()
    try:
        with file_path.open('rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None

# iterate the file names to have a number value at the end for duplicates
def generate_unique_path(destination_folder: Path, filename: str) -> Path:
    orig_path = destination_folder / filename
    if not orig_path.exists():
        return orig_path
        
    counter = 1
    # .stem gets the name without the extension and .suffix gets just the file type at the end (ie .jpg or .png)
    name = orig_path.stem
    ext = orig_path.suffix
    
    new_path = destination_folder / f"{name}_{counter:03d}{ext}"
    # loop until we land on a file iteration value that doesn't exist yet
    while new_path.exists():
        counter += 1
        new_path = destination_folder / f"{name}_{counter:03d}{ext}"
        
    return new_path

# points the material shaders to the new location where the texture files will be stored
def repath_selected_textures(destination_folder_str):
    rt = pymxs.runtime
    
    selected_nodes = list(rt.selection)
    if not selected_nodes:
        print("Nothing selected in 3ds Max.")
        return

    destination_folder = Path(destination_folder_str)
    destination_folder.mkdir(parents=True, exist_ok=True)

    # 1. gather all materials assigned to the current selection
    # create a set and for each node, add all the materials to the set
    scene_materials = set()
    for node in selected_nodes:
        if node.material:
            scene_materials.add(node.material)

    # 2. extract each Bitmap texture instance hidden inside those materials
    # getClassInstances finds all textures across standard, Arnold, Vray, or Multi-Materials
    all_bitmaps = []
    for mat in scene_materials:
        # MaxScript controls the material parsing hierarchy inside this function call
        bitmap_instances = rt.getClassInstances(rt.BitmapTex, target=mat)
        all_bitmaps.extend(list(bitmap_instances))

    # remove duplicates from the texture list
    # if there are multiple objects using the same material, this prevents the hash from having to run multiple times for the same material
    # instead, this says to only consider each material one time, even if that material occurs multiple times. (Note: Materials are not the same as texture fiels)
    all_bitmaps = list(set(all_bitmaps))

    # 3. Process, copy, and remap each individual texture file
    for bmp in all_bitmaps:
        # bmp.filename targets the actual texture path property inside 3ds Max
        full_path_str = bmp.filename
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
            # use .resolve as a safety net because C:\Folder MEANS the same as C:/Folder but would fail in a compairson here without resolving first
            if full_path.resolve() == target_path.resolve():
                continue

            # compare the hashes for any file that has a matching name    
            if get_file_hash(full_path) == get_file_hash(target_path):
                skip_copy = True
                print(f"Texture identical, skipping copy: {full_path.name}")
            else:
                # create a unique name for the new file if it is compositionally different than a previous file with the same name
                target_path = generate_unique_path(destination_folder, full_path.name)
                print(f"Name collision resolved. Renaming to: {target_path.name}")

        try:
            # 1. Define and create the tmp directory cleanly
            tmp_file_path = destination_folder / "tmp"
            tmp_file_path.mkdir(parents=True, exist_ok=True)


            file_target = tmp_file_path / target_path.name

            if not skip_copy:
                shutil.copy2(full_path, target_path)
                print(f"Successfully copied: {target_path.name}")

            # update the material shader to use the root TEXTURES directory
            bmp.filename = target_path.as_posix()
            print(f"Remapped material slot to: {target_path.name}")

            # move file into tmp folder
            shutil.move(target_path, file_target)

        except Exception as e:
            print(f"Failed processing {full_path.name}: {str(e)}")

    # clears out the memory of any leftover bitmaps
    #rt.freeSceneBitmaps()
    # refresh the viewport to show if anything has changed. This could indicate an issue with the texture movement and reassignment
    rt.forceCompleteRedraw()
    