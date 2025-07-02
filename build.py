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
            "--noconfirm",
            "--name=volsuite",
            "src/volsuite/main.py",
            "--hidden-import=scipy._cyutility",
        ],
        check=True,
    )


clean()
build()
