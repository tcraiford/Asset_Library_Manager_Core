import maya.cmds as cmds

port_name = ":7002"

# only open the port if it isn't already open
if not cmds.commandPort(port_name, query=True):
    cmds.commandPort(name=port_name, sourceType="python")
    print("Command port opened on", port_name)
else:
    print("Command port already open on", port_name)