from pathlib import Path


def test_automated_testing_pipeline():

    print("\n================================")
    print("Automated Testing Pipeline")
    print("================================\n")

    workflow = Path(".github/workflows/ci.yml")

    assert workflow.exists()

    text = workflow.read_text()

    # Workflow triggers
    assert "push:" in text
    assert "pull_request:" in text

    # Python setup
    assert "actions/setup-python" in text

    # Bench setup
    assert "bench init" in text
    assert "bench new-site" in text
    assert "install-app heshly_core" in text

    # Test execution
    assert "run-tests --app heshly_core" in text

    # Services
    assert "mariadb" in text
    assert "redis-cache" in text
    assert "redis-queue" in text

    print("✅ GitHub Actions configured")
    print("✅ Python environment configured")
    print("✅ Bench environment configured")
    print("✅ Automated tests configured")
    print("✅ Database and Redis services configured")

    print("\n🎉 AUTOMATED TESTING PIPELINE PASSED\n")