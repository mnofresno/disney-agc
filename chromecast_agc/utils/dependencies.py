"""Dependency management and auto-installation."""

import os
import subprocess
import sys


def get_platform_dependencies():
    """Get dependencies based on platform."""
    import platform

    is_macos = platform.system() == "Darwin"
    if is_macos:
        return ["numpy", "sounddevice", "pychromecast", "pynput"]
    else:
        return ["numpy", "sounddevice", "pychromecast", "keyboard"]


def check_dependencies():
    """Check if dependencies are installed."""
    dependencies = get_platform_dependencies()
    missing = []

    for dep in dependencies:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)

    return len(missing) == 0


def install_dependencies():
    """Install dependencies using different methods."""
    print("Installing necessary dependencies...")

    dependencies = get_platform_dependencies()

    if subprocess.run(["which", "pipx"], capture_output=True).returncode == 0:
        print("Using pipx to install dependencies...")
        try:
            venv_path = os.path.join(os.path.expanduser("~"), ".local", "chromecast_venv")
            if not os.path.exists(venv_path):
                subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
            pip_path = os.path.join(venv_path, "bin", "pip")
            subprocess.run([pip_path, "install"] + dependencies, check=True)
            site_packages = os.path.join(
                venv_path,
                "lib",
                f"python{sys.version_info.major}.{sys.version_info.minor}",
                "site-packages",
            )
            if os.path.exists(site_packages):
                sys.path.insert(0, site_packages)
        except subprocess.CalledProcessError:
            pass

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user"] + dependencies,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        print("⚠️  Using --break-system-packages (may require permissions)")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--break-system-packages"] + dependencies,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing dependencies: {e}")
            print("\nPlease install manually:")
            print(f"  pip3 install --user {' '.join(dependencies)}")
            sys.exit(1)
