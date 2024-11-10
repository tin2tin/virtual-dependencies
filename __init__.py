import os
import sys
import venv
import subprocess
import bpy
import importlib
from typing import Optional

# DEBUG setting to control print statements
DEBUG = False  # Set to True for debugging (prints enabled), False to disable prints


def debug_print(*args, **kwargs):
    """Conditional print function based on the DEBUG variable."""
    if DEBUG:
        print(*args, **kwargs)


# Add-on Info Block
bl_info = {
    "name": "Verv_Req Add-On",
    "blender": (3, 6, 0),
    "category": "System",
    "author": "Your Name",
    "version": (1, 0, 0),
    "description": "A Blender add-on for managing a virtual environment and installing Python dependencies.",
    "license": "GPL-3.0",
}


def addon_script_path() -> str:
    """Return the path where the add-on script is located (addon directory)."""
    addon_path = os.path.dirname(__file__)  # Use __file__ to get the script directory
    debug_print(f"Addon script path is: {addon_path}")
    return addon_path


def venv_path(env_name="Verv_Req_env") -> str:
    """Define the path for the virtual environment directory in the add-on's folder."""
    addon_path = addon_script_path()
    env_path = os.path.join(addon_path, env_name)  # Create virtual environment relative to add-on script
    debug_print(f"Virtual environment path is: {env_path}")
    return env_path


def python_exec() -> str:
    """Return the path to the Python executable in the virtual environment if it exists."""
    env_python = os.path.join(venv_path(), 'Scripts', 'python.exe') if os.name == 'nt' else os.path.join(venv_path(), 'bin', 'python')
    debug_print(f"Python executable in the virtual environment is: {env_python}")
    return env_python if os.path.exists(env_python) else sys.executable


def create_venv(env_name="Verv_Req_env"):
    """Create a virtual environment if it doesn't exist."""
    env_dir = venv_path(env_name)
    if not os.path.exists(env_dir):
        venv.create(env_dir, with_pip=True)
        debug_print(f"Virtual environment created at {env_dir}")
        ensure_pip_installed()  # Ensure pip is available after environment creation
    else:
        debug_print("Virtual environment already exists.")


def ensure_pip_installed():
    """Ensure pip is installed in the virtual environment."""
    python_exe = python_exec()
    subprocess.run([python_exe, '-m', 'ensurepip'])
    debug_print("Ensured that pip is installed.")


def install_packages(override: Optional[bool] = False):
    """Install or update packages from the requirements.txt file."""
    create_venv()  # Ensure the virtual environment exists before installation
    
    python_exe = python_exec()
    requirements_txt = os.path.join(addon_script_path(), "requirements.txt")
    target = venv_path()

    # Ensure pip is installed
    ensure_pip_installed()
    
    # Upgrade pip
    subprocess.run([python_exe, '-m', 'pip', 'install', '--upgrade', 'pip'])

    # Install dependencies with or without override
    if override:
        subprocess.run([python_exe, '-m', 'pip', 'install', '--upgrade', '--force-reinstall', '-r', requirements_txt, '--target', target])
    else:
        subprocess.run([python_exe, '-m', 'pip', 'install', '--upgrade', '-r', requirements_txt, '--target', target])

    # Add the virtual environment’s directory to sys.path
    add_virtualenv_to_syspath()

    # Check if all dependencies are installed
    check_dependencies_installed()


def add_virtualenv_to_syspath():
    """Add the virtual environment's directory to sys.path."""
    env_dir = venv_path()

    # Add the virtual environment directory to sys.path for imports
    if os.path.exists(env_dir):
        sys.path.append(env_dir)
        debug_print(f"Added virtual environment directory to sys.path: {env_dir}")
    else:
        debug_print(f"Virtual environment directory not found at: {env_dir}")


def check_dependencies_installed() -> bool:
    """Check if all the packages in the requirements.txt file are importable."""
    requirements_txt = os.path.join(addon_script_path(), "requirements.txt")
    
    if not os.path.exists(requirements_txt):
        debug_print(f"Requirements file '{requirements_txt}' not found.")
        return False

    with open(requirements_txt, 'r') as file:
        packages = file.readlines()

    missing_packages = []
    
    # Check if each package is importable
    for package in packages:
        package_name = package.strip()
        if package_name:  # Avoid empty lines
            try:
                importlib.import_module(package_name)
                debug_print(f"Package '{package_name}' is already installed and importable.")
            except ImportError:
                missing_packages.append(package_name)
                debug_print(f"Package '{package_name}' is missing or not importable.")

    if missing_packages:
        debug_print(f"Missing or non-importable packages: {', '.join(missing_packages)}")
        return False
    return True


def uninstall_packages():
    """Uninstall all packages listed in the requirements.txt file."""
    python_exe = python_exec()
    requirements_txt = os.path.join(addon_script_path(), "requirements.txt")

    if not os.path.exists(requirements_txt):
        debug_print("Requirements file not found for uninstallation.")
        return

    # Ensure pip is installed before running uninstall
    ensure_pip_installed()

    with open(requirements_txt, 'r') as file:
        packages = file.readlines()

    for package in packages:
        package_name = package.strip()
        if package_name:  # Avoid empty lines
            subprocess.run([python_exe, '-m', 'pip', 'uninstall', '-y', package_name])
            debug_print(f"Uninstalled package: {package_name}")


# Panel for Add-On Preferences
class Verv_ReqPreferencesPanel(bpy.types.Panel):
    bl_label = "Verv_Req Add-On"
    bl_idname = "PREFERENCES_PT_Verv_Req"
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_category = "Add-ons"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Manage virtual environment and dependencies:")

        # Install Dependencies Button
        layout.operator("verv_req.install_dependencies", text="Install Dependencies")

        # Uninstall Dependencies Button
        layout.operator("verv_req.uninstall_dependencies", text="Uninstall Dependencies")

        # Check Dependencies Button
        layout.operator("verv_req.check_dependencies", text="Check Dependencies")


# Operators for install, uninstall, and check dependencies
class InstallDependenciesOperator(bpy.types.Operator):
    bl_idname = "verv_req.install_dependencies"  # Updated the bl_idname here to match the class name
    bl_label = "Install Dependencies"

    def execute(self, context):
        install_packages(override=True)  # You can change `override` to `False` as needed
        return {'FINISHED'}


class UninstallDependenciesOperator(bpy.types.Operator):
    bl_idname = "verv_req.uninstall_dependencies"  # Updated the bl_idname here to match the class name
    bl_label = "Uninstall Dependencies"

    def execute(self, context):
        uninstall_packages()
        return {'FINISHED'}


class CheckDependenciesOperator(bpy.types.Operator):
    bl_idname = "verv_req.check_dependencies"  # Updated the bl_idname here to match the class name
    bl_label = "Check Dependencies"

    def execute(self, context):
        check_dependencies_installed()
        return {'FINISHED'}


# Registering the panel and operators
def register():
    bpy.utils.register_class(Verv_ReqPreferencesPanel)
    bpy.utils.register_class(InstallDependenciesOperator)
    bpy.utils.register_class(UninstallDependenciesOperator)
    bpy.utils.register_class(CheckDependenciesOperator)


def unregister():
    bpy.utils.unregister_class(Verv_ReqPreferencesPanel)
    bpy.utils.unregister_class(InstallDependenciesOperator)
    bpy.utils.unregister_class(UninstallDependenciesOperator)
    bpy.utils.unregister_class(CheckDependenciesOperator)


if __name__ == "__main__":
    register()
