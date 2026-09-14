# Asset Library Manager

This is a desktop application that manages a shared 3d asset repository and drives Maya and 3ds Max remotely over a TCP client/server protocol using socket ports in python. Built to solve a real production problem: keeping a team’s 3d models, textures, and file references consistent and discoverable instead of scattered across individual artist’s machines.

## How to Use

1. Change the *settings.example.ini* to *settings.ini* and set “library\_dir” to wherever you want the library to live  
2. Open the port:  
   1. For Maya, run the *Maya\_Port\_Open.py* in the script editor, set to python  
   2. For Max, run the *Max\_Port\_Open.py* in a new script inside of Max, set to python  
3. Run *asset\_library.py* to launch the tool

## Why is it needed?

In 3d production pipelines, “where’s the latest version of this asset” and “why are the textures missing” are constant, expensive problems, frequently caused by artists saving files in inconsistent locations or moving files without updating references. This tool centralizes submission and retrieval so that:  
 \- every asset lives in one predictable place that any other artist can access  
\- texture references are automatically redirected to a managed location instead of scattered on an artist’s local hard drive which would make them inaccessible for anyone else  
\- previous versions are archived instead of being overwritten  
\- all model submissions can be browsed to and previewed without needing Maya or 3ds Max

If a scene points all of its references to hundreds of assets, textures and models, and someone accidentally moves a file or accidentally misspells a version update, the scene will no longer be able to load in that asset and hours of potential work can be lost. This tool removes any potential for breaking animation scenes.

## Features

### Library Browsing

* Three-level category \-\> subcategory \-\> asset hierarchy, read directly from the filesystem  
* Thumbnail preview per asset, generated at time of asset submission and with a placeholder fallback when no thumbnail has been rendered yet  
* A first-run bootstrap that generates the starting folder structure from a text file template that can be modified by whoever is setting up the asset library to suit the studio’s needs (*starting\_library.txt*)

### Asset Submission Workflow

* Names and creates the new asset folder in the selected subcategory and exports the selection from either Maya or 3ds Max as an FBX and scene file (.fbx and .ma/.max)  
* Detects if an asset by that name already exists and asks if the user wants to create a new version of that asset or choose a different name for a fresh asset submission  
* If versioning up an asset, the previous version is renamed to “ARCHIVE\_” as a prefix and a version number as the suffix and moved into the ARCHIVE folder for that asset in the library  
* Identifies any texture files associated with the model being submitted and copies them to the asset’s TEXTURES folder and redirects the model to point to that library submission location instead of scattered across the artist’s local hard drive while moving the previous texture image files into a one-generation BACKUP folder (this is to prevent archiving hundreds of image files over the many versions of the model)  
* Automatically render a thumbnail of the model submission to be displayed in the Asset Library Tool

### Asset Pulling Workflow
* User can browse through the library of submitted assets with the tool and import the current version or an ARCHIVED version of the asset into their active Maya or 3ds Max scene
* When an asset is opened in the modeling software via the library tool, it is duplicated from the library into their active session but the original is never directly opened. This prevents artists from making unwanted changes to a file and using the modeling software's "Save" to make changes to the published file. If they make changes and publish the model with the library tool, it will create a new version of the asset, but the original version that was pulled will be preserved

### Remote Control of Maya and 3ds Max

* MayaClient and MaxClient connect to the commandPort and Scripting Listener over raw TCP sockets. Maya/Max are the listener/server while the desktop app is the client  
* The hardest part wasn’t establishing the networking, it was Maya and Max’s protocol behavior: a single self-contained expression sent to the port would evaluate and return its value over the socket, but multi-step code sent the same way doesn’t send anything back. It can run and still leave the client with no return value and no error. These silent failures were extremely difficult to diagnose  
* More complex methods that needed to utilize loops and if/else statements were unable to be reliably sent through the socket port due to newlines and indentation often breaking how Maya and Max executed code and since anything sent through the ports needed to be a string. The solution was to put more complex methods into their own class file and have it placed where Maya can load it or have Max load it directly from the tool’s directory and use the string sent through the socket port to load, instantiate, and execute the methods from that class file rather than trying to format it all to pass through the port  
* The tool uses short timeouts for quick commands while using longer timeouts for commands that are expected to potentially take longer such as file exports  
* Maya also pads its socket responses with trailing null bytes which broke downstream string comparisons so these needed to be cleaned

### Other

* A basic password gate (currently hardcoded. See Known Limitations) protects the actions that can affect the whole shared library, including changing the base directory and generating a new starting library, so an artist cannot accidentally repoint or duplicate the library for the whole team  
* A dependency bootstrap script checks for required packages on launch and offers to install anything missing

## Architecture

asset\_library.py     GUI (PySide6) — browsing, submission dialog, admin-gated settings  
maya\_client.py        Protocol layer — TCP socket client for Maya's commandPort  
maya\_scripts.py       Deployed into Maya's script folder; runs multi-step logic on request  
Maya\_Port\_Open.py      Run inside Maya to open the commandPort listener  
Maya\_Port\_Close.py     Run inside Maya to close it  
max\_client.py		Protocol layer — TCP socket client for Max’s script listener  
Max\_scripts.py	Loaded by 3ds Max directly from the tool’s location  
Max\_Port\_Open.py	Run inside 3ds Max to begin listening for commands  
requiredChecks.py      Dependency check/bootstrap on launch  
settings.ini            Configured base directory for the asset library  
starting\_library.txt     Template folder structure used on first-time setup

The user only needs to open the port in their modeling software and select the assets they want to be submitted. After that, everything is handled through the standalone tool.

## Configuration

The library’s base directory is read from *settings.ini* at launch rather than hardcoded, specifically so it can be repointed without touching code. The intended deployment is an admin can set this to point to wherever the shared library actually lives (a network path in a real studio setup), and every artist’s copy of the tool just reads that. This repo ships *settings.example.ini* with a placeholder path. It needs to be renamed to *settings.ini* and set to the desired path for your team before running.

## Tech Stack

Python, PySide6 (QT for Python), raw TCP sockets, Autodesk Maya Python API (maya.cmds) via commandPort, Autodesk 3ds Max Python API (pymxs)

## Future Updates

* Submission tracking with an SQL Database \- record who submitted/pulled an asset and when, for basic production accountability  
* Unreal Engine integration- push selected assets directly into a connected Unreal project’s content browser


## Known Limitations

This is a personal/portfolio-stage project, not a hardened production tool and a couple of things reflect that on purpose for now:

* The admin password is a hardcoded placeholder rather than a real auth/config system  
* Error handling around the Maya and Max sockets is functional but not exhaustive

While this is used in a few studios, both are natural next steps if this becomes a marketed product.

