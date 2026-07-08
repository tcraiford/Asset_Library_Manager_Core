import shutil
import os
import subprocess
import sys

from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QWidget, QVBoxLayout, QPushButton,
                               QToolButton, QLabel, QLineEdit, QMessageBox, QDialog, QListWidget, QListWidgetItem,
                               QMenu)
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

        # setting up the category lists
        self.category_list = QListWidget()
        self.subcategory_list = QListWidget()
        self.sub_subcategory_list = QListWidget()
        # When a user selects a main category, run the "load_subcategories" method
        # this is just another activation, similar to clicked for a button widget
        self.category_list.itemSelectionChanged.connect(self.load_subcategories)
        # when a user selects a subcategory from the subcategory list, load the sub_subcategories
        self.subcategory_list.itemSelectionChanged.connect(self.load_sub_subcategories)

        # category list layout
        list_layout = QHBoxLayout()
        list_layout.addWidget(self.category_list)
        list_layout.addWidget(self.subcategory_list)
        list_layout.addWidget(self.sub_subcategory_list)

        self.directory_line = QLineEdit()
        self.directory_line.setPlaceholderText("Enter the base directory path here...")
        self.directory_line.setReadOnly(True)
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
        main_layout.addLayout(list_layout)

        # add gear icon on top right
        self.gear_button = QToolButton(self)
        self.gear_button.setText("⚙")
        self.gear_button.setPopupMode(QToolButton.InstantPopup)

        #dropdown menu options
        gear_menu = QMenu(self)
        # add gear_menu functions here. Format is string for displayed menu option and then the function
        gear_menu.addAction("Create Starting Library", self.create_starting_library)
        gear_menu.addAction("Change Library Directory", self.change_directory)
        # tells the gear_button that the menu it is pulling content from is named gear_menu
        self.gear_button.setMenu(gear_menu)
        # position the gear_button top right always
        self.position_gear_button()
    
    def position_gear_button(self):
        # calculate the x position of the button (window width - button width - margin)
        x_pos = self.width() - 25 - 10
        self.gear_button.setGeometry(x_pos, 10 , 25, 25)

    # built in event in Qt that DOES NOT NEED TO BE CALLED. It is called automatically
    def resizeEvent(self, event):
        # recalculate position of gear_button when window is resized
        self.position_gear_button()
        super().resizeEvent(event)

    def change_directory(self):
        self.check_admin_access()
        self.directory_line.setReadOnly(False)

    def create_starting_library(self):
        if self.check_admin_access():
            self.set_base_directory()
            starting_library_path = self.directory_line.text()
            create_starting_library(starting_library_path)
            # creates variable new path and adds "Asset_Library" to the "pathed" self.directory_line
            new_path = Path(self.directory_line.text()) / "Asset_Library"
            # converts new_path from a Path to plain text and plugs it into the directory_line
            self.directory_line.setText(str(new_path))
            self.set_base_directory()

    def set_base_directory(self):
        self.current_directory = self.directory_line.text()
        if not os.path.exists(self.current_directory):
            QMessageBox.warning(self, "Directory Not Found", "The specified directory does not exist.")

        else:
            # innitiates the first list box
            self.populate_list(Path(self.current_directory), self.category_list)

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

    """this method clears the list_widget from any leftovers. It then looks at the directory and all its contents and says it only cares if the contents item is a folder.
    It then takes each folder and removes the file directory from it so it is only the name of the folder but then stores that removed directory bit into slot 100 for that specific folder.
    This way, we only see the folder's name but that folder still has its directory stored to it."""            
    def populate_list(self, folder_path, list_widget):
        # clear out any old text each time this is called
        list_widget.clear()

        folder_path = Path(folder_path)
        # looks at all items in this directory
        for path in sorted(folder_path.iterdir()):
            # .is_dir only passes true if the item inside this folder is a folder
            if path.is_dir():
                # remove the directory and only keep the name of the found item
                item = QListWidgetItem(path.name)

                # put the full directory and name, combined, into slot 100
                # this isn't visible to the user but the code reads it when clicked
                # slot 100 is not a global slot, it is tied to whatever "item" we are on so itemA has a slot 100 and itemB has a slot 100 etc etc etc
                item.setData(100, path)

                list_widget.addItem(item)

    """These are the methods that are called when a folder in the lists is selected that tells the next list what to display. They are called by the itemSelectionChanged action inside __innit__"""
    def load_subcategories(self):
        # wipe downstream columns clean so if you change your category selection, it doesn't get confused by your subcategory selection data
        self.subcategory_list.clear()
        self.sub_subcategory_list.clear()

        # get whatever item is currently selected
        selected_items = self.category_list.selectedItems()

        if selected_items:
            # if multiple lines are selected, it only returns the first
            chosen_item = selected_items[0]

            # look inside data slot 100 for the selected item and get the directory path
            next_folder_path = chosen_item.data(100)

            # runs the populate_list method and feeds it the file path for the selected folder we just established and also tells the populate_list method we want to send that data to the subcategory_list
            self.populate_list(next_folder_path, self.subcategory_list)

    """This follows the same logic as load_subcategories but it triggers when an item in column 2 is clicked, clears out only column 3, and populates column 3. """
    def load_sub_subcategories(self):
        # wipe only the final column clean. We don't want to wipe the column above us
        self.sub_subcategory_list.clear()

        # determine which row was highlighted in the subcategory list
        selected_items = self.subcategory_list.selectedItems()

        if selected_items:
            # if something is selected, we tell the code to only look at the first item selected
            chosen_item = selected_items[0]

            # look inside data slot 100 for the selected item and get the directory path
            next_folder_path = chosen_item.data(100)

            # runs the populate_list method and feeds it the file path for the selection we just established and also tells the populate list method we want to send that data to the sub_subcategory_list)
            self.populate_list(next_folder_path, self.sub_subcategory_list)

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
