import subprocess
import shutil
from pathlib import Path


# Remove old build/ dist/ directories and .spec file.
def clean():
    print("Removing old directories and files...")
    for file in ["build", "dist", "volsuite.spec"]:
        path = Path(file)
        if path.exists():
            print(f"Removing: {path}...")
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()


# Build the executable using pyinstaller.
def build():
    subprocess.run(
        [
            "pyinstaller",
            "src/volsuite/main.py",
            "--noconfirm",
            "--name=volsuite",
            "--hidden-import=scipy._cyutility",
            "--onefile",
        ],
        check=True,
    )


clean()
build()
