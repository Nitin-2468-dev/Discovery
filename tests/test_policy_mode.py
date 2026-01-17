from probe.policy import Mode, PolicyEngine


def test_mode_alias_and_values():
    # Alias exists and equals the canonical enum member
    assert Mode.educational_open is Mode.EDUCATIONAL_OPEN
    assert Mode.EDUCATIONAL_OPEN.value == "educational_open"


def test_policy_engine_default_and_educational_mode():
    engine = PolicyEngine()  # default should be PUBLIC_GUARDED
    assert engine.mode is Mode.PUBLIC_GUARDED

    engine2 = PolicyEngine(mode=Mode.educational_open)
    assert engine2.mode is Mode.EDUCATIONAL_OPEN

    decision = engine2.evaluate_query("test")
    assert decision["mode"] == "educational_open"
    assert "allowed" in decision
    assert "reason" in decision
