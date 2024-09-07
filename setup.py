import os
import venv
import subprocess
from setuptools import setup, find_packages

def create_venv(venv_path):
    print(f"Creating virtual environment in {venv_path}...")
    venv.create(venv_path, with_pip=True)

def install_requirements(venv_path):
    pip_path = os.path.join(venv_path, 'bin', 'pip') if os.name != 'nt' else os.path.join(venv_path, 'Scripts', 'pip')
    req_file = 'requirements.txt'
    print("Installing project and dependencies...")
    subprocess.check_call([pip_path, 'install', '-r', req_file])
    subprocess.check_call([pip_path, 'install', '-e', '.'])

def setup_project():
    venv_path = ".venv"
    if not os.path.exists(venv_path):
        create_venv(venv_path)
        install_requirements(venv_path)

if __name__ == "__main__":
    setup_project()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name="electricity_mix_calculator",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=required,
)
