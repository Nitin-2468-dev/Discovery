import json

from probe.policy import telemetry


def test_record_denial_writes_jsonl(tmp_path, monkeypatch):
    p = tmp_path / "policy_denials.jsonl"
    monkeypatch.setattr(telemetry, "TELEMETRY_FILE", p)

    # initialize logger to write to this file
    telemetry.init_logger(path=p, max_bytes=1024, backup_count=1)

    decision = {
        "mode": "public_guarded",
        "reason": "domain 'x' disallowed",
        "tags": ["domain"],
        "context": {"domain": "x"},
    }
    telemetry.record_denial(decision)

    assert p.exists()
    lines = p.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 1
    rec = json.loads(lines[-1])
    assert rec["mode"] == "public_guarded"
    assert rec["reason"].startswith("domain 'x'")


def test_upload_to_s3_uses_boto3(monkeypatch, tmp_path):
    p = tmp_path / "policy_denials.jsonl"
    p.write_text("{}\n")
    monkeypatch.setattr(telemetry, "TELEMETRY_FILE", p)

    class DummyS3:
        def upload_file(self, filename, bucket, key):
            assert filename == str(p)
            assert bucket == "my-bucket"
            assert key == "my-key"

    class DummySession:
        def client(self, service):
            assert service == "s3"
            return DummyS3()

    class DummyBoto:
        # boto3.Session is a factory method with uppercase name; keep lowercase helper for lint
        def Session(self, profile_name=None):  # noqa: N802
            return DummySession()

    monkeypatch.setitem(__import__("sys").modules, "boto3", DummyBoto())

    ok = telemetry.upload_to_s3("my-bucket", key="my-key", aws_profile=None)
    assert ok is True
