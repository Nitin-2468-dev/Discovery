import sys
import subprocess
import zipfile
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _build_wheel(outdir: Path):
    cmd = [sys.executable, "-m", "build", "--wheel", "--outdir", str(outdir)]
    # Retry once on transient build backend errors (empirically observed in CI)
    for attempt in range(2):
        completed = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        if completed.returncode == 0:
            return
        if attempt == 0:
            import time

            time.sleep(1)
            continue
        raise RuntimeError(
            f"Wheel build failed: {completed.returncode}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )


def _read_pyproject():
    try:
        import tomllib as toml
    except ImportError:
        try:
            import tomli as toml
        except ImportError:
            pytest.skip("tomllib/tomli required to parse pyproject.toml")
    p = ROOT / "pyproject.toml"
    assert p.exists(), "pyproject.toml missing"
    with p.open("rb") as fh:
        return toml.load(fh)


def _extract_metadata_from_wheel(wheel_path: Path) -> str:
    with zipfile.ZipFile(wheel_path, "r") as z:
        meta_files = [n for n in z.namelist() if n.endswith("/METADATA")]
        assert meta_files, "No METADATA file found in wheel"
        # Prefer first metadata
        data = z.read(meta_files[0])
        return data.decode("utf-8", errors="replace")


def test_pyproject_metadata_has_required_fields():
    parsed = _read_pyproject()
    project = parsed.get("project", {})
    assert project.get("name"), "[project].name is missing"
    assert project.get("version"), "[project].version is missing"
    license_entry = project.get("license")
    assert license_entry, "[project].license is missing"
    # Check classifiers include license classifier if present
    classifiers = project.get("classifiers", [])
    assert any("License ::" in c for c in classifiers), "No license classifier found in [project].classifiers"


def test_wheel_metadata_matches_pyproject(tmp_path: Path):
    parsed = _read_pyproject()
    project = parsed.get("project", {})
    name = project.get("name")
    version = project.get("version")

    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    _build_wheel(dist_dir)

    wheels = list(dist_dir.glob("*.whl"))
    assert wheels, "No wheels found in dist"
    wheel = wheels[0]

    metadata = _extract_metadata_from_wheel(wheel)
    # Extract Name and Version from METADATA
    name_match = re.search(r"^Name: (.+)$", metadata, re.M)
    ver_match = re.search(r"^Version: (.+)$", metadata, re.M)
    assert name_match, "Name not found in wheel METADATA"
    assert ver_match, "Version not found in wheel METADATA"
    # Strip whitespace/newlines robustly (some wheel generators put CRLF)
    wheel_name = name_match.group(1).strip()
    wheel_ver = ver_match.group(1).strip()
    assert wheel_name.lower() == name.lower(), f"Wheel name {wheel_name} does not match pyproject name {name}"
    assert wheel_ver == version, f"Wheel version {wheel_ver} does not match pyproject version {version}"

    # Check license info present in METADATA
    lic_match = re.search(r"^License: (.+)$", metadata, re.M)
    classifier_license = any("License ::" in l for l in metadata.splitlines())
    assert lic_match or classifier_license, "No license information found in wheel METADATA"
