import os
import shutil
import sys
import configparser

from maya_client import MayaClient
from requiredChecks import check_required_libraries
check_required_libraries()


from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QWidget, QVBoxLayout, QPushButton,
                               QToolButton, QLabel, QLineEdit, QMessageBox, QDialog, QListWidget, QListWidgetItem,
                               QMenu)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from pathlib import Path



# creates a basic starting library to be built upon. This is a starting point for the asset library
def create_starting_library(base_directory_path):
    subfolders = []
    # opens starting_library.txt and saves each line as a new directory to be created
    with open("starting_library.txt", 'r') as file:
        # open the file and read only one line at a time
        for line in file:
            # check if the line is blank
            if line.strip():
                # if it has text, strip the newline from the end and add it to the list
                subfolders.append(line.strip())

    
    base_directory_path = Path(base_directory_path)

    for folder in subfolders:
        full_path = base_directory_path / "Asset_Library" / folder
        full_path.mkdir(parents=True, exist_ok=True)
    
    return base_directory_path


def get_folders_in_directory(dir_path):
    dir_path = Path(dir_path)
    folders =  [f for f in dir_path.iterdir() if f.is_dir()]
    return folders

# create the asset submission window that pops up when the user clicks "Submit New Asset"
class AssetSubmissionDialog(QDialog):
    # accepts the target path as an argument so it can be used to create the new asset folder in the correct location
    def __init__(self, target_path: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Submit New Asset")
        self.maya = MayaClient()

        self.new_asset_dir = target_path

        confirmation_buttons = QHBoxLayout()
        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.submit_asset)
        confirmation_buttons.addWidget(submit_button)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.cancel_submission)
        confirmation_buttons.addWidget(cancel_button)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Target Directory: {self.new_asset_dir}"))
        self.new_asset_name_submission = QLineEdit(placeholderText="Enter new asset name here...")
        layout.addWidget(self.new_asset_name_submission)
        layout.addLayout(confirmation_buttons)


    def cancel_submission(self):
        self.reject()

    # creates the folders for the new asset submission and handles the archival process
    def submit_asset(self):
        new_asset_name = self.new_asset_dir / self.new_asset_name_submission.text()

        # determine if anything is selected
        something_selected = self.maya.send_command(self.maya.determine_if_selected())
        if something_selected == "False":
            QMessageBox.warning(self, "No Selection", "Nothing selected in Maya. Please make a selection and try again.")
            self.close()
            return


        # add /ARCHIVE and /TEXTURES directory and create folder directory
        # this is called before checking if it already exists because it will work whether or not the folder exists already and we
        # need that folder to exist for archival purposees too
        new_asset_archive_folder = new_asset_name / "ARCHIVE"
        new_asset_textures_folder = new_asset_name / "TEXTURES"
        new_asset_archive_folder.mkdir(parents=True, exist_ok=True)
        new_asset_textures_folder.mkdir(parents=True, exist_ok=True)

 
        # checks for pre-existing file and prompts archival
        # new_asset_name is the file's directory but we need to add the actual file's name and type to the end of the path so we specifically target the file within the folder with the matching name
        existing_file_name = self.new_asset_name_submission.text() + ".fbx"
        existing_asset_source = new_asset_name / existing_file_name

        if existing_asset_source.exists():
            response_to_archival = self.prompt_archival()

            if response_to_archival:
                # logic to increment the file number in ARCHIVE to prevent overwriting previous Archive files
                counter = 1
                archived_file_name = f"ARCHIVE_{existing_file_name.replace('.fbx', '')}_{counter:03d}.fbx"

                existing_asset_destination = new_asset_archive_folder / archived_file_name

                # checks if the Archive file version exists and if so, increments by 1 and tries again
                while existing_asset_destination.exists():
                    counter += 1
                    archived_file_name = f"ARCHIVE_{existing_file_name.replace('.fbx', '')}_{counter:03d}.fbx"
                    existing_asset_destination = new_asset_archive_folder / archived_file_name

                shutil.move(existing_asset_source, existing_asset_destination)


            else:
                # cancel asset submission if user does not want to archive an existing file
                QMessageBox.warning(self, "Choose a New Name", "Please choose a different name for the asset submission and try again.")
                return

        

        # closes the dialog box after submission and returns a True flag to the main window that the submission was successful
        self.accept()

    def prompt_archival(self):
        # if asset name already exists, this will prompt if they want to Archive the existing version and submit a new version
        archive_prompt_box = QMessageBox(self)

        archive_prompt_box.setIcon(QMessageBox.Icon.Question)
        archive_prompt_box.setWindowTitle("Archive Existing?")
        archive_prompt_box.setText("Asset already exists. Do you want to archive the existing file and create a new version?")

        # create the buttons
        archive_prompt_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        # default highlight button no to avoid accidental archival
        archive_prompt_box.setDefaultButton(QMessageBox.StandardButton.No)

        response = archive_prompt_box.exec()

        # response is either QMessageBox.StandardButton.Yes or No. If it is Yes, then this will evaluate as True, thus prompt_archival() returns True if user selects Yes button
        return response == QMessageBox.StandardButton.Yes



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
        self.resize(500, 600)
        self.current_directory = ""

        # the directory where a new asset would be created. Assigned in the subcategory_list selection method
        self.new_asset_submission_directory = ""

        # selected asset in asset list
        self.asset_list_selection = ""

        # the list of geometry files found inside sub_subcategory_list
        self.geometry_file_list = []
        # directory of the thumbnail for the selected asset in sub_subcategory_list
        self.thumbnail_dir = ""

        # Instantiate the MayaClient to manage communication with Maya
        # this creates an object called self.maya that can be used to send commands to Maya. It is an instance of the MayaClient class defined in maya_client.py
        self.maya = MayaClient()
        # Flag to track connection status with Maya
        self.connected_to_maya = False  

        # password protection for some actions
        self.HARDCODED_PASSWORD = "0000"
        self.is_admin = False

        # setting up the category lists
        self.category_list = QListWidget()
        self.subcategory_list = QListWidget()
        self.sub_subcategory_list = QListWidget()
        self.asset_folder_contents_list = QListWidget()
        # When a user selects a main category, run the "load_subcategories" method
        # this is just another activation, similar to clicked for a button widget
        self.category_list.itemSelectionChanged.connect(self.load_subcategories)
        # when a user selects a subcategory from the subcategory list, load the sub_subcategories
        self.subcategory_list.itemSelectionChanged.connect(self.load_sub_subcategories)
        # when a user selects an asset folder in the sub_subcategory list, walk and load the contents of that asset folder
        self.sub_subcategory_list.itemSelectionChanged.connect(self.load_asset_folder_contents)
        # when a user selects an asset listed in the asset's folder
        self.asset_folder_contents_list.itemClicked.connect(self.get_selected_asset_path)

        # category list layout
        list_layout = QHBoxLayout()
        list_layout.addWidget(self.category_list)
        list_layout.addWidget(self.subcategory_list)
        list_layout.addWidget(self.sub_subcategory_list)

        # asset folder contents layout
        asset_options_layout = QHBoxLayout()
        asset_options_layout.addWidget(self.asset_folder_contents_list)
        # create and add the thumbnail
        self.preview_thumbnail = QLabel()
        # makes sure the thumbnail scales properly
        self.preview_thumbnail.setScaledContents(True)
        self.preview_thumbnail.setFixedSize(256, 256)
        asset_options_layout.addWidget(self.preview_thumbnail)

        # Control button layout
        control_button_layout = QHBoxLayout()
        maya_test_button = QPushButton("Maya Function Test")
        control_button_layout.addWidget(maya_test_button)
        maya_test_button.clicked.connect(self.do_Maya_test)
        submit_new_asset_button = QPushButton("Submit New Asset")
        control_button_layout.addWidget(submit_new_asset_button)
        submit_new_asset_button.clicked.connect(self.submit_new_asset)
        open_asset_in_maya_button = QPushButton("Open Asset in Maya")
        control_button_layout.addWidget(open_asset_in_maya_button)
        open_asset_in_maya_button.clicked.connect(self.open_asset_in_maya)


        self.directory_line = QLineEdit()
        self.directory_line.setPlaceholderText("Enter the base directory path here...")
        self.directory_line.setReadOnly(True)
        self.directory_line.returnPressed.connect(self.set_base_directory)
        '''create self variable to hold library from settings.ini and then next line
        sets it into the directory_line'''
        self.library_path = self.settings_pull()
        self.directory_line.setText(self.library_path)
        # innitialize the directory. Without this, the lists will remain blank until set_base_directory is called later
        self.set_base_directory()
        open_dir_button = QPushButton("Open Library")
        open_dir_button.clicked.connect(self.open_directory)

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

        # define the positioning of content on the main_layout tool
        main_layout.addWidget(description)
        main_layout.addLayout(dir_layout)
        main_layout.addLayout(control_button_layout)
        main_layout.addLayout(list_layout)
        main_layout.addLayout(asset_options_layout)

        # add gear icon on top right
        self.gear_button = QToolButton(self)
        self.gear_button.setText("⚙")
        self.gear_button.setPopupMode(QToolButton.InstantPopup)

        #dropdown menu options
        gear_menu = QMenu(self)
        # add gear_menu functions here. Format is string for displayed menu option and then the function
        gear_menu.addAction("Connect to Maya", self.set_up_maya_connection)
        gear_menu.addAction("Create Starting Library", self.create_starting_library)
        gear_menu.addAction("Change Library Directory", self.change_directory)
        # tells the gear_button that the menu it is pulling content from is named gear_menu
        self.gear_button.setMenu(gear_menu)
        # position the gear_button top right always
        self.position_gear_button()

    # gets the default maya scripts folder directory
    def get_maya_scripts_dir(self):
        home = Path.home()

        if os.name =='nt': # Windows
            return home / "Documents" / "maya" / "scripts"

        elif os.sys.platform == 'darwin':  # macOS
            return home / "Library" / "Preferences" / "Autodesk" / "maya" / "scripts"
        
        else:  # Linux
            return home / "maya" / "scripts"

    # copies the maya_scripts file to the default maya script folder
    def send_script_to_maya_default_folder(self):
        # maya's default script directory
            script_dir = self.get_maya_scripts_dir()
            # what the file would be called if it already exists in the default directory
            possible_script_dir = script_dir / "maya_scripts.py"
            # directory of THIS file and all the extra bits
            program_dir = Path(__file__).resolve().parent / "maya_scripts.py"
    
            # if the maya_scripts.py file isn't in the main scripts folder, put a copy there
            if not possible_script_dir.is_file():
                script_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(program_dir, script_dir)


    def do_Maya_test(self):
        print('maya function test button pressed')
        self.send_script_to_maya_default_folder()
        self.maya.send_command(self.maya.test_button())
        




    def set_up_maya_connection(self):
        # check if already connected to Maya. If so, do a fresh test of the connection and if it is still good, 
        # tell the user they are already connected. If not, go through the connection process again.
        if not self.connected_to_maya:
            
            # create a message box to tell user to set up connection on Maya side
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Maya Connection Setup")
            msg_box.setText("Please launch Maya and open the port for communication.\nPress 'Continue' once Maya is ready.")
            msg_box.setIcon(QMessageBox.Icon.Information)

            continue_button = msg_box.addButton("Continue", QMessageBox.ButtonRole.AcceptRole)
            msg_box.addButton(QMessageBox.StandardButton.Cancel)
            msg_box.exec()

            if msg_box.clickedButton() == continue_button:
                print("Testing connection...")
                self.maya.test_maya_connection()
            else:
                print("User canceled the operation.")
                return

            if self.maya.test_maya_connection():
                self.connected_to_maya = True


    def open_asset_in_maya(self):
        if not self.connected_to_maya:
            self.set_up_maya_connection()

        file_path = self.get_selected_asset_path()
        print(file_path)

        self.maya.send_command(self.maya.reference_file(file_path))
        

    def submit_new_asset(self):
        if not self.connected_to_maya:
            self.set_up_maya_connection()

        if self.new_asset_submission_directory == "":
            QMessageBox.warning(self, "No Subcategory Selected", "Please select a subcategory type before submitting a new asset.")
            return

        # opens the dialog to create the new asset name and folder
        submission_dialog = AssetSubmissionDialog(self.new_asset_submission_directory, self)
        result = submission_dialog.exec()

        if not result:
            return

        # zoom extents of selection in Maya
        self.maya.send_command("cmds.viewFit()")

        # send script folder to Maya default location for texture collection
        self.send_script_to_maya_default_folder()

        # sends the export_selected_to_fbx command to maya with the asset directory and adds the new asset name to the end of the path.
        # This is done by taking the self.new_asset_submission_directory and adding the new asset name from the submission_dialog to it.
        # The result is a full path to where the new asset will be created in Maya.
        asset_name = f"{submission_dialog.new_asset_name_submission.text()}.fbx"
        asset_directory = self.new_asset_submission_directory / submission_dialog.new_asset_name_submission.text()
        asset_directory_name = asset_directory / asset_name
        self.maya.send_command(self.maya.export_selected_to_fbx(asset_directory_name))
        self.maya.send_command(self.maya.export_selected_to_ma(asset_directory_name))
        print("model exported. Moving to materials now...")

        # remove any old textures and collect textures for model
        #---------------------------------------------------
        textures_folder = asset_directory / "TEXTURES"
        backup_folder = textures_folder / "BACKUP"

        # delete backup_folder if it exists for the asset then create a new empty one
        if backup_folder.exists():
            shutil.rmtree(backup_folder)
        backup_folder.mkdir(parents=True, exist_ok=True)

        # copy all contents of TEXTURES folder that are not a directory into backup_folder
        for item in textures_folder.iterdir():
            if item == backup_folder:
                continue
            if not item.is_dir() and not item.is_symlink():
                shutil.move(item, backup_folder)

        self.maya.send_command(self.maya.collect_textures(textures_folder))

        # get the project directory for Maya where the thumbnail will be rendered to
        maya_project_dir = self.maya.send_command(self.maya.get_maya_project_directory())

        # temporarily create ambient light
        self.maya.send_command(self.maya.create_ambient_light())

        # render the thumbnail
        self.maya.send_command(self.maya.render_thumbnail())

        # delete the temp ambient light
        self.maya.send_command(self.maya.delete_ambient_light())

        # move the rendered thumbnail from the Maya project directory to the new asset folder
        # first get the open maya file name because that is what the image will be named
        maya_file_name = Path(self.maya.send_command(self.maya.get_file_name())).stem
        if maya_file_name == "": # if the project is unsaved, the get_file_name() method returns nothing and the render will be saved as "untitled"
            maya_file_name = "untitled"
        maya_file_name = f"{maya_file_name}.jpg"
        thumbnail_source = Path(maya_project_dir.strip()) / "images" / "tmp" / maya_file_name
        thumbnail_destination = self.new_asset_submission_directory / submission_dialog.new_asset_name_submission.text()
        target_thumbnail_path = thumbnail_destination / "thumbnail.jpg"
        shutil.move(thumbnail_source, target_thumbnail_path)

        # refresh the sub_subcategory_list to show the new asset folder
        self.load_sub_subcategories()


    
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
        if self.check_admin_access():
            self.directory_line.setReadOnly(False)

    # pulls the starting directory from the settings.ini file
    def settings_pull(self):
        # initialize the configparser
        config = configparser.ConfigParser()
        config.read("settings.ini")
        return config["LibraryDirectory"]["library_dir"]

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
        self.asset_folder_contents_list.clear()
        # clear the thumbnail displayed
        self.preview_thumbnail.clear()
        self.preview_thumbnail.setText("Select an asset to view preview")

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
        # wipe the final column clean. We don't want to wipe the column above us
        self.sub_subcategory_list.clear()
        self.asset_folder_contents_list.clear()
        # clear the thumbnail displayed
        self.preview_thumbnail.clear()
        self.preview_thumbnail.setText("Select an asset to view preview")

        # determine which row was highlighted in the subcategory list
        selected_items = self.subcategory_list.selectedItems()

        if selected_items:
            # if something is selected, we tell the code to only look at the first item selected
            chosen_item = selected_items[0]

            # look inside data slot 100 for the selected item and get the directory path
            next_folder_path = chosen_item.data(100)

            # runs the populate_list method and feeds it the file path for the selection we just established and also tells the populate list method we want to send that data to the sub_subcategory_list)
            self.populate_list(next_folder_path, self.sub_subcategory_list)

            # assign the selected subcategory folder's path to a self variable so it can be used to locate where a potential new asset will be created
            self.new_asset_submission_directory = chosen_item.data(100)


    def load_asset_folder_contents(self):
        # wipe the contents of asset_folder_contents_list
        self.asset_folder_contents_list.clear()
        # clear the thumbnail displayed
        self.preview_thumbnail.clear()
        self.preview_thumbnail.setText("Select an asset to view preview")

        # get the selected asset in the sub_subcategory list
        selected_items = self.sub_subcategory_list.selectedItems()

        if selected_items:
            chosen_item = selected_items[0]

            folder_path = chosen_item.data(100)
            # added this line to test
            self.asset_list_selection = chosen_item.data(100)
            
            # clear out any old text each time this is called
            self.asset_folder_contents_list.clear()

            folder_path = Path(folder_path)
            geometry_files = []
            # set jpg_item to false and then, if a jpg is found, it will be set to true. If it is still false after the loop, then we know no jpg was found and we can use a default thumbnail instead
            jpg_item = False

            # walks the asset folder file and looks for the jpg thumbnail and the geo files and adds them to a list each
            for file in folder_path.rglob('*'):
                if file.is_file():
                    # check file extension
                    ext = file.suffix.lower()


                    if ext == ".jpg":
                        # send the jpg's directory to the self.thumbnail_dir variable
                        self.thumbnail_dir = str(file)
                        # create a pixmap of the found jpg and update preview_thumbnail to display it
                        pixmap = QPixmap(Path(self.thumbnail_dir))
                        self.preview_thumbnail.setPixmap(pixmap)
                        jpg_item = True
                    
                    elif ext in (".obj", ".fbx", ".ma", ".mb", ".max"):
                        geometry_files.append(file)
                        # remove the directory and only keep the name of the file
                        item = QListWidgetItem(file.name)

                        # put the full directory and name, combined, into slot 100
                        # this isn't visible to the user but the code reads it when clicked
                        # slot 100 is not a global slot, it is tied to whatever "item" we are on so itemA has a slot 100 and itemB has a slot 100 etc etc etc
                        item.setData(100, file)

                        self.asset_folder_contents_list.addItem(item)

            # use missing thumbnail if no jpg was found in the asset folder
            if jpg_item is not True:
                # get the root directory of the script to use as a fallback thumbnail if no jpg is found
                root_dir = Path(__file__).resolve().parent
                root_dir = root_dir / "thumbnail_Missing.jpg"
                pixmap = QPixmap(root_dir)
                self.preview_thumbnail.setPixmap(pixmap)


    def get_selected_asset_path(self):
        selected_items = self.asset_folder_contents_list.selectedItems()

        if not selected_items:
            return

        chosen_item = selected_items[0]
        file_path = chosen_item.data(100)
        return file_path


    def open_directory(self):
        directory = self.directory_line.text()
        os.startfile(directory)



if __name__ == "__main__":
    #startup()
    app = QApplication(sys.argv)
    window = AssetLibraryApp()
    window.show()
    app.exec()
