import os
import sys
import subprocess

def is_project_installed():
    venv_path = ".venv"
    return os.path.exists(venv_path)

def install_project():
    print("Project not installed. Installing...")
    subprocess.check_call([sys.executable, 'setup.py'])

def run_main_script(args):
    venv_path = ".venv"
    python_path = os.path.join(venv_path, 'bin', 'python') if os.name != 'nt' else os.path.join(venv_path, 'Scripts', 'python')
    full_command = [python_path, '-m', 'src.main'] + args
    subprocess.check_call(full_command)

if __name__ == "__main__":
    if not is_project_installed():
        install_project()
    
    run_main_script(sys.argv[1:])
