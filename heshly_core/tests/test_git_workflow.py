from pathlib import Path


def test_git_workflow():

    workflow = Path(".github/workflows/ci.yml")

    assert workflow.exists()

    text = workflow.read_text()

    assert "actions/checkout" in text
    assert "actions/setup-python" in text
    assert "bench init" in text
    assert "bench new-site" in text
    assert "install-app heshly_core" in text
    assert "run-tests --app heshly_core" in text

    print("✅ GitHub Actions workflow detected")
    print("✅ Bench initialization configured")
    print("✅ Test site creation configured")
    print("✅ CI test execution configured")