def test_gaps_exports():
    import importlib
    import inspect

    try:
        m = importlib.import_module("probe.analysis.gaps")
    except Exception as e:
        raise AssertionError(f"Failed to import probe.analysis.gaps: {e}")

    # Basic module metadata for CI diagnostics
    module_file = getattr(m, "__file__", None)
    members = [n for n in dir(m) if not n.startswith("_")]

    if "GapDetector" not in members:
        src_info = None
        if module_file:
            try:
                with open(module_file, "r", encoding="utf-8") as fh:
                    content = fh.read()
                src_info = {
                    "module_file": module_file,
                    "starts_with": content[:200],
                    "len": len(content),
                }
            except Exception as e:
                src_info = {"module_file": module_file, "error_reading": str(e)}

        raise AssertionError(
            f"GapDetector not exported; module members: {members}; module_file: {module_file}; src_info: {src_info}"
        )

    # Also sanity-check that the class can be inspected
    assert inspect.isclass(getattr(m, "GapDetector"))
