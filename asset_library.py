import shutil
import os
import subprocess
import sys

from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QLineEdit, QMessageBox, QDialog)
from PySide6.QtCore import Qt
from pathlib import Path

# check if all necessary packages are installed and if not, offer to install them
def required_checks():
    required = ["PySide6", "pathlib"]
    missing = []
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

# creates a basic starting library to be built upon. This is a starting point for the asset library
def create_starting_library(base_directory_path): 
    # create a list of subfolders to be created in the starting library
    subfolders = [
        "Hero",
        "Character/Human", "Character/Lion", "Character/Giraffe", "Character/Elephant", "Character/Monkey",
        "Environment/Buildings", "Environment/Lights", "Environment/Furniture", "Environment/Vehicles", "Environment/Machines", "Environment/Structures",
        "Vegetation/Trees", "Vegetation/Grass", "Vegetation/Flowers", "Vegetation/Shrubs", "Vegetation/Plants",
        "Utility"
    ]
    
    base_directory_path = Path(base_directory_path)

    for folder in subfolders:
        full_path = base_directory_path / "Asset_Library" / folder
        full_path.mkdir(parents=True, exist_ok=True)
    
    return base_directory_path

# input validation
def input_validation(answer, valid_options):
    while answer not in valid_options:
        answer = input("Invalid input. Please enter a valid option: ")


def get_folders_in_directory(dir_path):
    dir_path = Path(dir_path)
    folders =  [f for f in dir_path.iterdir() if f.is_dir()]
    return folders

# create a passwrod dialog box that can pop up when protected actions are attempted by user
class PasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Password Required")
        self.resize(300, 100)

        # make the dialog box the only thing the user can interact with until closed
        #self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # create the layout for the password box
        layout = QVBoxLayout()

        # create the pieces that go into the password box
        self.label = QLabel("Please enter the password to proceed")
        layout.addWidget(self.label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter password here...")
        layout.addWidget(self.password_input)

        self.submit_button = QPushButton("Submit")

        self.password_input.returnPressed.connect(self.submit_button.click)
        self.submit_button.clicked.connect(self.accept)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def get_password(self):
        return self.password_input.text()

class AssetLibraryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asset Library Manager")
        self.resize(500, 300)
        self.current_directory = ""

        # password protection for some actions
        self.HARDCODED_PASSWORD = "0000"
        self.is_admin = False

        self.directory_line = QLineEdit()
        self.directory_line.setPlaceholderText("Enter the base directory path here...")
        self.directory_line.returnPressed.connect(self.set_base_directory)
        open_dir_button = QPushButton("Open Directory")
        open_dir_button.clicked.connect(self.open_directory)
        create_library_button = QPushButton("Create Starting Library")
        create_library_button.clicked.connect(self.create_starting_library)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        #layout main_layout is where all the individual widgets and row/collum layouts get added to
        main_layout = QVBoxLayout(central_widget)

        # create a label to be shown at the top of the tool
        description = QLabel("A tool to manage your asset library.")

        # create the directory line layout
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.directory_line)
        dir_layout.addWidget(open_dir_button)
        dir_layout.addWidget(create_library_button)

        # define the positioning of content on the main_layout tool
        main_layout.addWidget(description)
        main_layout.addLayout(dir_layout)


    def create_starting_library(self):
        if self.check_admin_access():
            self.set_base_directory()
            starting_library_path = self.directory_line.text()
            create_starting_library(starting_library_path)

    def set_base_directory(self):
        self.current_directory = self.directory_line.text()
        if not os.path.exists(self.current_directory):
            QMessageBox.warning(self, "Directory Not Found", "The specified directory does not exist.")

    def check_admin_access(self):
        # if already entered password, then access is automatic
        if self.is_admin:
            return True
        
        # if is_admin is false, then we'd skip the return above and continue to this code
        dialog = PasswordDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.get_password() == self.HARDCODED_PASSWORD:
                self.is_admin = True
                QMessageBox.information(self, "Access Granted", "You have access to the admin features.")
                return True
            else:
                QMessageBox.critical(self, "Incorrect Password", "The password entered is incorrect.")
        return False
                

    def open_directory(self):
        directory = self.directory_line.text()
        os.startfile(directory)



subfolder1_contents = ["Hero", "Character", "Environment", "Vegetation", "Utility"]

if __name__ == "__main__":
    required_checks()
    app = QApplication(sys.argv)
    window = AssetLibraryApp()
    window.show()
    app.exec()

    """# establish the base directory
    base_directory = input("Enter the base directory path for the asset library:\n"
    "if one does not exist, this is where it will be created.\n")
    base_directory_path = create_starting_library()"""
