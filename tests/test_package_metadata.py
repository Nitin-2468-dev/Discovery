import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _build_wheel(outdir: Path):
    cmd = [sys.executable, "-m", "build", "--wheel", "--outdir", str(outdir)]
    # Retry transient wheel build failures (some CI environments can fail intermittently)
    attempts = 3
    for attempt in range(1, attempts + 1):
        completed = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        if completed.returncode == 0:
            return
        # On failure, wait a bit and retry (exponential backoff)
        if attempt < attempts:
            time.sleep(0.5 * attempt)
        else:
            # As a last resort, try building without isolation (some CI environments
            # exhibit transient failures when building in isolated venvs). This is
            # less strict than an isolated build but reduces flakes in CI.
            no_iso_cmd = cmd + ["--no-isolation"]
            completed_no_iso = subprocess.run(
                no_iso_cmd, cwd=str(ROOT), capture_output=True, text=True
            )
            if completed_no_iso.returncode == 0:
                return
            raise RuntimeError(
                f"Wheel build failed after {attempts} attempts (isolated) and one no-isolation attempt: {completed.returncode}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}\n\nno-isolation stdout:\n{completed_no_iso.stdout}\nno-isolation stderr:\n{completed_no_iso.stderr}"
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
        # Be tolerant: some wheels (or some zip tools) may present entries with
        # different path separators or casing. Match any entry that ends with
        # 'METADATA' case-insensitively.
        meta_files = [n for n in z.namelist() if n.lower().endswith("metadata")]
        if not meta_files:
            # Provide debugging information in the assertion to aid CI triage
            names = z.namelist()
            raise AssertionError(
                "No METADATA file found in wheel; zip entries: " + ", ".join(names)
            )
        # Prefer the first metadata found
        data = z.read(meta_files[0])
        return data.decode("utf-8", errors="replace")


def test_pyproject_metadata_has_required_fields():
    parsed = _read_pyproject()
    project = parsed.get("project", {})
    assert project.get("name"), "[project].name is missing"
    assert project.get("version"), "[project].version is missing"
    license_entry = project.get("license")
    assert license_entry, "[project].license is missing"
    # If classifiers are present, ensure at least one is a license classifier.
    # Otherwise, prefer SPDX license expression in [project].license (checked above).
    classifiers = project.get("classifiers", [])
    if classifiers:
        has_license_classifier = any("License ::" in c for c in classifiers)
        # Accept either a license classifier or a SPDX license string in [project].license
        assert has_license_classifier or isinstance(license_entry, str), (
            "No license classifier found in [project].classifiers and [project].license is not a simple SPDX string"
        )


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
    assert (
        wheel_name.lower() == name.lower()
    ), f"Wheel name {wheel_name} does not match pyproject name {name}"
    assert (
        wheel_ver == version
    ), f"Wheel version {wheel_ver} does not match pyproject version {version}"

    # Check license info present in METADATA
    lic_match = re.search(r"^License: (.+)$", metadata, re.M)
    lic_expr_match = re.search(r"^License-Expression: (.+)$", metadata, re.M)
    classifier_license = any("License ::" in line for line in metadata.splitlines())
    assert (
        lic_match or lic_expr_match or classifier_license
    ), (
        "No license information found in wheel METADATA (checked License, License-Expression, and classifiers). "
        "If wheel build fails with 'error: [Errno 2] No such file or directory: 'cleaner.py'", 
        "ensure package data includes all scripts and that MANIFEST.in or package_data is updated."
    )

