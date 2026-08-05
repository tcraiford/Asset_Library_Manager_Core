import subprocess
import sys

required = ["PySide6", "pathlib"]
missing = []
def check_required_libraries():
    print("Running required libraries check...")

    for package in required:
        try:
            globals()[package] = __import__(package)
        except:
            missing.append(package)
    if missing:
        print(f"Missing libraries: {', '.join(missing)}")
        install_query = input("Do you want to install them now? (y/n): ").strip().lower()
        if install_query == 'y':
            for package in missing:
                subprocess.run(["pip", "install", package])
            print("Installation complete. Relaunching now...")
            subprocess.run([sys.executable, __file__])
            sys.exit()
        else:
            sys.exit("Exiting program. Please install the missing libraries and try again.")