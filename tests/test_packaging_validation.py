import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_license_file_present_and_non_empty():
    license_file = ROOT / "LICENSE"
    assert license_file.exists(), "LICENSE file is missing at repo root"
    assert license_file.stat().st_size > 0, "LICENSE file is empty"


def _build_wheel(outdir: Path):
    cmd = [sys.executable, "-m", "build", "--wheel", "--outdir", str(outdir)]
    # Retry once on transient build backend errors (empirically observed in CI)
    for attempt in range(2):
        completed = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        if completed.returncode == 0:
            return
        # If this was the first attempt, wait briefly and retry
        if attempt == 0:
            import time

            time.sleep(1)
            continue
        # Otherwise, write build logs into outdir (for CI diagnostic) and raise
        try:
            build_logs = outdir / "build_logs"
            build_logs.mkdir(parents=True, exist_ok=True)
            (build_logs / "build.out").write_text(
                (completed.stdout or "") + "\n\n" + (completed.stderr or "")
            )
        except Exception:
            # best effort write; ignore errors here
            pass


EXPECTED_FILES = [
    "probe/analysis/gaps.py",
    "probe/analysis/seed_generator.py",
    "probe/analysis/investigator.py",
]

EXPECTED_KEYWORDS = {
    "probe/analysis/gaps.py": ["class GapDetector", "def GapDetector"],
    "probe/analysis/seed_generator.py": ["class SeedGenerator", "def generate_seeds"],
    "probe/analysis/investigator.py": ["def investigate", "class Investigator"],
}


def test_wheel_contains_expected_files_and_nonempty(tmp_path: Path):
    # Skip if 'build' isn't available in the environment; CI will have it installed (requirements updated)
    pytest.importorskip("build")

    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    _build_wheel(dist_dir)

    wheels = list(dist_dir.glob("*.whl"))
    assert wheels, f"No wheels found in {dist_dir}"
    wheel = wheels[0]

    with zipfile.ZipFile(wheel, "r") as z:
        names = z.namelist()
        for expected in EXPECTED_FILES:
            matches = [n for n in names if n.endswith(expected)]
            assert matches, f"Expected {expected} in wheel; found: {names[:25]}..."
            # ensure matched file(s) are non-empty and contain expected keywords
            for m in matches:
                data = z.read(m)
                assert len(data) > 10, f"File {m} in wheel appears empty"
                txt = data.decode("utf-8", errors="replace")
                kws = EXPECTED_KEYWORDS.get(expected, [])
                assert any(
                    k in txt for k in kws
                ), f"None of expected keywords {kws} found in {m}"


def test_pyproject_license_has_text_or_license_file_present():
    tomllib = None
    try:
        import tomllib as toml

        tomllib = toml
    except ImportError:
        try:
            import tomli as toml

            tomllib = toml
        except ImportError:
            tomllib = None

    if tomllib is None:
        pytest.skip(
            "tomllib/tomli not available; skipping pyproject license text check"
        )

    p = ROOT / "pyproject.toml"
    assert p.exists(), "pyproject.toml missing"

    with p.open("rb") as fh:
        parsed = tomllib.load(fh)
    project = parsed.get("project", {})
    license_entry = project.get("license")
    assert license_entry, "No [project].license in pyproject.toml"
    if isinstance(license_entry, dict):
        text = license_entry.get("text")
        assert (
            text and text.strip()
        ), "[project].license.text in pyproject.toml is empty"


def test_expected_symbols_present_in_source():
    # Smoke test on source to validate expected exports exist
    import probe.analysis.gaps as gaps

    assert hasattr(gaps, "GapDetector"), "GapDetector not found in probe.analysis.gaps"

    import probe.analysis.seed_generator as sg

    assert hasattr(sg, "SeedGenerator") or hasattr(
        sg, "generate_seeds"
    ), "SeedGenerator or generate_seeds not found in probe.analysis.seed_generator"

    import probe.analysis.investigator as inv

    assert hasattr(inv, "investigate") or hasattr(
        inv, "Investigator"
    ), "investigate or Investigator not found in probe.analysis.investigator"
