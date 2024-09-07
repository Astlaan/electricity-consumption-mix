import os
import sys
import subprocess

def is_project_installed(venv_path=".venv"):
    return os.path.exists(venv_path)

def install_project():
    print("Project not installed. Installing...")
    try:
        subprocess.check_call([sys.executable, 'setup.py'])
    except subprocess.CalledProcessError as e:
        print(f"Error installing project: {e}")
        sys.exit(1)

def run_main_script(args, venv_path=".venv", main_script='src.main'):
    python_path = os.path.join(venv_path, 'bin', 'python') if os.name != 'nt' else os.path.join(venv_path, 'Scripts', 'python')
    full_command = [python_path, '-m', main_script] + args
    print(f"Running command: {' '.join(full_command)}")  # Debug print
    try:
        subprocess.check_call(full_command)
    except subprocess.CalledProcessError as e:
        print(f"Error running main script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    venv_path = ".venv"
    if not is_project_installed(venv_path):
        install_project()
    
    # Remove the '--' from sys.argv if present
    args = sys.argv[1:]
    if args and args[0] == '--':
        args = args[1:]
    
    print(f"Arguments passed to main script: {args}")  # Debug print
    run_main_script(args, venv_path)
