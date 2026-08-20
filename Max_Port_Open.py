# run this inside of 3ds max to open a port to communicate with the asset library tool



import maxpython

# Port 4004 is widely used for Max Python, but you can change it if needed
PORT_NUMBER = 4004

try:
    maxpython.maxcommandport.open_port(PORT_NUMBER)
    print(f"Success: 3ds Max Python command port {PORT_NUMBER} is now open.")
except Exception as e:
    print(f"Error opening port: {e}")
