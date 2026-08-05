import maya.cmds as cmds

port_name = ":7002"

# Close the port
cmds.commandPort(name=port_name, close=True)

# Verify the port closed
is_open = cmds.commandPort(port_name, query=True)

if is_open:
    print(f"{port_name} is open")
else:
    print(f"{port_name} is closed")

# Error: RuntimeError: file <maya console> line 6: Command port ':7002' does not exist.
