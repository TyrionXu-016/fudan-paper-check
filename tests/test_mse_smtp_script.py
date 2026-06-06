from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_smtp_acceptance_reuses_existing_test_mailbox() -> None:
    script = (ROOT / "scripts" / "mse_acceptance_smtp.sh").read_text(encoding="utf-8")

    assert "auth_token()" in script
    assert 'if [[ "$code" == "409" ]]' in script
    assert "$API/v1/auth/login" in script
    assert "MSE_ACCEPTANCE_PASSWORD" in script
