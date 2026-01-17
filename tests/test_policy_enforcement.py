from probe.policy import Mode, PolicyEngine


def test_domain_allowed_behavior():
    public = PolicyEngine(mode=Mode.PUBLIC_GUARDED)
    assert public.domain_allowed("malicious.example") is False
    assert public.domain_allowed("example.com") is True

    edu = PolicyEngine(mode=Mode.educational_open)
    assert edu.domain_allowed("malicious.example") is True


def test_evaluate_query_respects_domain():
    public = PolicyEngine(mode=Mode.PUBLIC_GUARDED)
    decision_public = public.evaluate_query(
        "fetch manual", context={"domain": "malicious.example"}
    )
    assert decision_public["allowed"] is False
    assert "domain" in decision_public["tags"]
    assert "malicious.example" in decision_public["reason"]

    edu = PolicyEngine(mode=Mode.educational_open)
    decision_edu = edu.evaluate_query(
        "fetch manual", context={"domain": "malicious.example"}
    )
    assert decision_edu["allowed"] is True
    assert decision_edu["mode"] == "educational_open"


def test_educational_mode_admin_flag_no_effect_on_domain_allowed():
    # `EDUCATIONAL_OPEN` is permissive by default; `admin_enabled` currently
    # gates additional operational relaxations but does not influence domain checks.
    edu_no_admin = PolicyEngine(mode=Mode.educational_open, admin_enabled=False)
    assert edu_no_admin.domain_allowed("malicious.example") is True

    edu_admin = PolicyEngine(mode=Mode.educational_open, admin_enabled=True)
    assert edu_admin.domain_allowed("malicious.example") is True
