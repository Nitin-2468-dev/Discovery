import sys
import subprocess
import zipfile
from pathlib import Path
import os
import shutil
import venv

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _build_wheel(outdir: Path):
    cmd = [sys.executable, "-m", "build", "--wheel", "--outdir", str(outdir)]
    completed = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            f"Wheel build failed: {completed.returncode}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )


@pytest.mark.parametrize("pyver", ["3.11"])
def test_install_wheel_and_imports(tmp_path: Path, pyver):
    # Skip if build tool is not present
    pytest.importorskip("build")

    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()

    _build_wheel(dist_dir)

    wheels = list(dist_dir.glob("*.whl"))
    assert wheels, f"No wheel produced in {dist_dir}"
    wheel = wheels[0]

    # Create a temporary venv and install the wheel into it
    venv_dir = tmp_path / "venv"
    venv.create(venv_dir, with_pip=True)

    if os.name == "nt":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python"

    # Upgrade pip and install the wheel
    completed = subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], capture_output=True, text=True)
    assert completed.returncode == 0, f"Failed to upgrade pip: {completed.stdout}\n{completed.stderr}"

    completed = subprocess.run([str(venv_python), "-m", "pip", "install", "--no-deps", str(wheel)], capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"Failed to pip install wheel: {completed.stdout}\n{completed.stderr}")

    # Run a python snippet inside the venv that imports the package and checks symbols
    check_code = (
        "import sys;"
        "import probe;"
        "import probe.analysis.gaps as gaps;"
        "import probe.analysis.seed_generator as sg;"
        "import probe.analysis.investigator as inv;"
        "ok = hasattr(gaps, 'GapDetector') and (hasattr(sg,'SeedGenerator') or hasattr(sg,'generate_seeds')) and (hasattr(inv,'investigate') or hasattr(inv,'Investigator'));"
        "sys.exit(0 if ok else 2)"
    )

    completed = subprocess.run([str(venv_python), "-c", check_code], capture_output=True, text=True)
    assert completed.returncode == 0, f"Import/symbol check failed in installed wheel: returncode={completed.returncode}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
