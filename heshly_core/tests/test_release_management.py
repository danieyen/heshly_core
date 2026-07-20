from pathlib import Path


def test_release_management():

    print("\n================================")
    print("Release Management")
    print("================================\n")

    version = Path("VERSION")
    changelog = Path("CHANGELOG.md")
    script = Path("deployment/scripts/release.sh")

    assert version.exists()
    assert changelog.exists()
    assert script.exists()

    assert version.read_text().strip()

    script_text = script.read_text()

    assert "git tag" in script_text
    assert "docker compose" in script_text
    assert "VERSION" in script_text

    print("✅ VERSION file found")
    print("✅ CHANGELOG found")
    print("✅ Release script found")
    print("✅ Git tagging configured")
    print("✅ Release management verified")

    print("\n🎉 RELEASE MANAGEMENT PASSED\n")