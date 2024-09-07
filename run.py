import os
import sys
import venv
import subprocess

def create_venv(venv_path):
    print(f"Creating virtual environment in {venv_path}...")
    venv.create(venv_path, with_pip=True)

def install_requirements(venv_path):
    pip_path = os.path.join(venv_path, 'bin', 'pip') if os.name != 'nt' else os.path.join(venv_path, 'Scripts', 'pip')
    req_file = 'requirements.txt'
    
    if os.path.exists(req_file):
        print("Installing requirements...")
        subprocess.check_call([pip_path, 'install', '-r', req_file])
    else:
        print("No requirements.txt found. Skipping package installation.")

def run_main_script(venv_path, script_path, args):
    python_path = os.path.join(venv_path, 'bin', 'python') if os.name != 'nt' else os.path.join(venv_path, 'Scripts', 'python')
    full_command = [python_path, script_path] + args
    subprocess.check_call(full_command)

if __name__ == "__main__":
    venv_path = ".venv"
    main_script = "src/main.py"

    if not os.path.exists(venv_path):
        create_venv(venv_path)
        install_requirements(venv_path)
    
    run_main_script(venv_path, main_script, sys.argv[1:])