[README.md](https://github.com/user-attachments/files/31155241/README.md)
# Asset Library Manager

A desktop application that manages a shared 3D-asset repository and drives Autodesk Maya remotely over a hand-rolled TCP client/server protocol. Built to solve a real production problem: keeping a team's 3D models, textures, and file references consistent and discoverable instead of scattered across individual artists' machines.

**Status:** work in progress. Maya integration is fully implemented; 3ds Max and Unreal Engine support are planned extensions (see [Roadmap](#roadmap)).

---

## Why this exists

In small-to-mid-size 3D production pipelines, "where's the latest version of this asset" and "why are the textures missing" are constant, expensive problems — usually caused by artists saving files in inconsistent locations or moving texture files without updating references. This tool centralizes submission and retrieval so that:

- every asset lives in one predictable place,
- texture references are automatically repointed to a managed location instead of an artist's local drive,
- previous versions are preserved instead of silently overwritten,
- and browsing what already exists doesn't require opening Maya at all.

The same underlying pattern — a lightweight GUI client controlling a heavier content-creation application over a socket — is the part of this project I'd call out to a general software engineering audience, independent of the 3D-industry context.

## Core features (implemented)

**Library browsing**
- Three-level category → subcategory → asset hierarchy, read directly off the filesystem
- Thumbnail preview per asset, with a placeholder image fallback when no thumbnail has been rendered yet
- A first-run bootstrap that generates the starting folder structure from a plain-text template (`starting_library.txt`)

**Asset submission workflow**
- Names and creates a new asset folder, exports the current Maya selection to both `.fbx` and `.ma`
- Detects naming conflicts and prompts the user to archive the existing file (renamed with an incrementing `ARCHIVE_..._00N` suffix) rather than overwrite it — archived versions remain browsable and can still be loaded back into Maya
- Walks the selected objects' shading network (shape → shading group → surface shader → file nodes) to find every texture in use, copies each into a `TEXTURES` folder, and repoints the material to the new location — de-duplicating filenames along the way
- Rotates the previous submission's textures into a single-generation `BACKUP` folder rather than accumulating every past version, to keep storage in check
- Automatically renders a thumbnail (temporary ambient light added and removed around the render) and saves it into the asset folder

**Remote control of Maya**
- `MayaClient` connects to a Maya `commandPort` over raw TCP sockets — Maya is the listener/server, the desktop app is the client
- The hardest part of this integration wasn't the networking, it was Maya's own protocol behavior: a single self-contained expression sent to the port (e.g. `cmds.file(q=True, sn=True)`) evaluates and returns its value over the socket, but multi-statement or multi-step code sent the same way doesn't reliably hand anything back — it can run and still leave the client with no return value and no error, which made failures very hard to diagnose at first
- Rather than fight that constraint, the fix was to work within it: any logic that needs more than one line — like walking a shading network to collect textures — lives in a separate script (`maya_scripts.py`) that gets copied automatically into Maya's own default scripts folder (no manual per-machine setup needed), and is called through a single evaluable expression over the socket, e.g. `assetToolScript.collect_textures(path)`
- Short synchronous timeouts (2s) for quick status checks like "is anything selected," and a longer timeout (30s) specifically around file-export commands, since those can legitimately take longer
- Maya also pads its socket responses with trailing null bytes, which broke downstream string comparisons (like the selection check) until the client stripped them before returning the response

**Other**
- A basic password gate (currently hardcoded — see [Known limitations](#known-limitations)) protects the two actions that affect the whole shared library: changing the base directory and generating a new starting library, so a single artist can't accidentally repoint or duplicate the library for the whole team
- A dependency bootstrap script that checks for required packages on launch and offers to install anything missing

## Architecture

```
asset_library.py     GUI (PySide6) — browsing, submission dialog, admin-gated settings
maya_client.py        Protocol layer — TCP socket client for Maya's commandPort
maya_scripts.py       Deployed into Maya's script folder; runs multi-step logic on request
Maya_Port_Open.py      Run inside Maya to open the commandPort listener
Maya_Port_Close.py     Run inside Maya to close it
requiredChecks.py      Dependency check/bootstrap on launch
settings.ini            Configured base directory for the asset library
starting_library.txt     Template folder structure used on first-time setup
```

The GUI never talks to Maya directly — everything goes through `MayaClient`. That's a deliberate boundary: the plan is to add a parallel client class for 3ds Max (and eventually inject assets directly into Unreal's content browser) without having to touch the GUI or the submission workflow at all.

## Configuration

The library's base directory is read from `settings.ini` at launch rather than hardcoded, specifically so it can be repointed without touching code. The intended deployment is: an admin sets `library_dir` to wherever the shared library actually lives (a network path, in a real studio setup), and every artist's copy of the tool just reads that. This repo ships `settings.example.ini` with a placeholder path — copy it to `settings.ini` and set your own path before running.

## Tech stack

Python · PySide6 (Qt for Python) · raw TCP sockets · Autodesk Maya Python API (`maya.cmds`) via `commandPort` · `configparser` for settings

## Roadmap

- **3ds Max support** — a second client class mirroring `MayaClient`'s interface, so the rest of the app is DCC-agnostic
- **Unreal Engine integration** — push selected assets directly into a connected Unreal project's content browser
- **Submission tracking** — record who submitted/pulled an asset and when, for basic production accountability

## Known limitations

This is a personal/portfolio-stage project, not a hardened production tool, and a couple of things reflect that on purpose for now:
- The admin password is a hardcoded placeholder rather than a real auth/config system
- Error handling around the Maya socket is functional but not exhaustive (e.g. it assumes a well-formed response within the timeout window)

Both are natural next steps if this were adopted by an actual team.

## Running it

1. Copy `settings.example.ini` to `settings.ini` and set `library_dir` to wherever you want the library to live
2. In Maya's Script Editor, run `Maya_Port_Open.py` to open the command port
3. Run `asset_library.py` to launch the tool
