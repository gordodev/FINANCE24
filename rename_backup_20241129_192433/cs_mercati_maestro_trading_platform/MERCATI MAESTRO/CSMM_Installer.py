import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

# Define the directory structure with subdirectories and files
structure = {
    "bin": [],
    "config": ["app_config.yaml", "database_config.yaml"],
    "data": ["historical_data/", "real_time_data/", "user_data/"],
    "cache": ["market_data_cache/", "user_cache/"],
    "lib": ["external/", "custom/"],
    "logs": ["app.log", "error.log", "access.log"],
    "src": ["components/", "services/", "utils/", "main.py"],
    "tests": ["unit_tests/", "integration_tests/", "test_config.yaml"],
    "docs": ["API_Documentation.txt", "User_Guide.txt"],
    "README.txt": "# CS Mercati Maestro\n\n## Application Purpose\nCS Mercati Maestro is a trading application front end designed to provide comprehensive market data, position management, market surveillance, and compliance functionalities.\n\n## Directory Structure\n- **bin/**: Binaries and executables\n- **config/**: Configuration files\n  - app_config.yaml: Main application configuration\n  - database_config.yaml: Database configuration\n- **data/**: Data files\n  - historical_data/: Historical market data\n  - real_time_data/: Real-time market data\n  - user_data/: User-specific data files\n- **cache/**: Cache files\n  - market_data_cache/: Cached market data\n  - user_cache/: Cached user data\n- **lib/**: Libraries\n  - external/: External libraries\n  - custom/: Custom libraries\n- **logs/**: Log files\n  - app.log: Main application log\n  - error.log: Error log\n  - access.log: Access log\n- **src/**: Source code\n  - components/: Front-end components\n  - services/: Services and business logic\n  - utils/: Utility functions\n  - main.py: Main entry point of the application\n- **tests/**: Test files\n  - unit_tests/: Unit tests\n  - integration_tests/: Integration tests\n  - test_config.yaml: Test configuration\n- **docs/**: Documentation\n  - API_Documentation.txt: API documentation\n  - User_Guide.txt: User guide\n- **README.txt**: Project overview and setup instructions\n"
}

class InstallerApp:
    def __init__(self, root):
        """Initialize the installer application GUI."""
        self.root = root
        self.root.title("CS Mercati Maestro Installer")
        self.create_widgets()

    def create_widgets(self):
        """Create and layout the GUI widgets."""
        tk.Label(self.root, text="CS Mercati Maestro Installer", font=("Helvetica", 16)).pack(pady=10)
        tk.Button(self.root, text="Select Installation Directory", command=self.select_directory).pack(pady=10)
        self.dir_label = tk.Label(self.root, text="", font=("Helvetica", 12))
        self.dir_label.pack(pady=10)
        self.install_button = tk.Button(self.root, text="Install", command=self.install, state=tk.DISABLED)
        self.install_button.pack(pady=10)
        self.uninstall_button = tk.Button(self.root, text="Uninstall", command=self.uninstall, state=tk.DISABLED)
        self.uninstall_button.pack(pady=10)
        self.status_label = tk.Label(self.root, text="", font=("Helvetica", 12))
        self.status_label.pack(pady=10)

    def select_directory(self):
        """Prompt the user to select an installation directory."""
        self.install_dir = filedialog.askdirectory()
        if self.install_dir:
            self.dir_label.config(text=f"Installation Directory: {self.install_dir}")
            self.install_button.config(state=tk.NORMAL)
            self.uninstall_button.config(state=tk.NORMAL)

    def check_existing_directories(self):
        """Check for existing directories in the selected installation path."""
        existing_folders = []
        for folder in structure.keys():
            folder_path = os.path.join(self.install_dir, folder)
            if os.path.exists(folder_path):
                existing_folders.append(folder)
        return existing_folders

    def install(self):
        """Create the directory structure and files."""
        existing_folders = self.check_existing_directories()
        if existing_folders:
            response = messagebox.askyesno(
                "Existing Folders Found",
                f"Found existing folders: {', '.join(existing_folders)}.\nContinue or uninstall?"
            )
            if response:
                self.uninstall()
                if not messagebox.askyesno("Uninstall Completed", "Do you want to install the application?"):
                    self.status_label.config(text="Installation Aborted")
                    return
            else:
                self.status_label.config(text="Installation Aborted")
                return

        # Create directories and files that do not already exist
        missing_structure = {k: v for k, v in structure.items() if k != "README.txt" and not os.path.exists(os.path.join(self.install_dir, k))}
        try:
            for folder, files in missing_structure.items():
                folder_path = os.path.join(self.install_dir, folder)
                os.makedirs(folder_path, exist_ok=True)
                if files:
                    for file in files:
                        if file.endswith("/"):
                            # Create subdirectory
                            os.makedirs(os.path.join(folder_path, file), exist_ok=True)
                        else:
                            # Create empty file
                            open(os.path.join(folder_path, file), 'a').close()

            # Create README.txt with content
            readme_path = os.path.join(self.install_dir, "README.txt")
            with open(readme_path, 'w') as f:
                f.write(structure["README.txt"])

            self.status_label.config(text="Installation Completed Successfully!")
        except PermissionError:
            messagebox.showerror("Permission Error", "Permission denied. Please run the installer as an administrator.")
            self.status_label.config(text="Installation Failed")
        except Exception as e:
            # Handle any other errors that occur during installation
            messagebox.showerror("Installation Error", str(e))
            self.status_label.config(text="Installation Failed")

    def uninstall(self):
        """Remove the application files and directories, excluding the logs directory."""
        try:
            for folder in structure.keys():
                if folder != "logs":
                    folder_path = os.path.join(self.install_dir, folder)
                    if os.path.exists(folder_path):
                        if os.path.isdir(folder_path):
                            shutil.rmtree(folder_path)
                        else:
                            os.remove(folder_path)
            self.status_label.config(text="Uninstallation Completed Successfully!")
        except Exception as e:
            # Handle any errors that occur during uninstallation
            messagebox.showerror("Uninstallation Error", str(e))
            self.status_label.config(text="Uninstallation Failed")

# Run the installer application
if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()
