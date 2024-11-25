import sys
import subprocess

def ensure_pipenv():
    try:
        import pipenv
    except ImportError:
        print("Installing pipenv...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pipenv"])

def install_dependencies():
    print("Installing dependencies with pipenv...")
    subprocess.check_call(["pipenv", "install"])

def run_main_script(args):
    print(f"Arguments passed to main script: {args}")
    full_command = ["pipenv", "run", "python", "-m", "src.main"] + args
    print(f"Running command: {' '.join(full_command)}")
    try:
        subprocess.check_call(full_command)
    except subprocess.CalledProcessError as e:
        print(f"Error running main script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ensure_pipenv()
    install_dependencies()

    # Remove the '--' from sys.argv if present
    args = sys.argv[1:]
    if args and args[0] == "--":
        args = args[1:]

    run_main_script(args)
