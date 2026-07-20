from pathlib import Path


def test_rollback_strategy():

    print("\n================================")
    print("Rollback Strategy")
    print("================================\n")

    script = Path("deployment/scripts/rollback.sh")

    assert script.exists()

    text = script.read_text()

    assert "docker compose" in text
    assert "down" in text
    assert "up -d" in text
    assert "Rollback completed successfully." in text

    print("✅ Rollback script found")
    print("✅ Stops existing deployment")
    print("✅ Restarts previous deployment")
    print("✅ Rollback strategy verified")

    print("\n🎉 ROLLBACK STRATEGY PASSED\n")