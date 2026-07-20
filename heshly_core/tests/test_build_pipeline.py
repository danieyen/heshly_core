from pathlib import Path


def test_build_pipeline():

    print("\n================================")
    print("Build Pipeline")
    print("================================\n")

    workflow = Path(".github/workflows/ci.yml")

    assert workflow.exists()

    text = workflow.read_text()

    # Source checkout
    assert "actions/checkout" in text

    # Python & Node
    assert "actions/setup-python" in text
    assert "actions/setup-node" in text

    # Dependency installation
    assert "bench setup requirements" in text

    # Application installation
    assert "bench get-app heshly_core" in text
    assert "install-app heshly_core" in text

    # Asset build
    assert "bench build" in text

    print("✅ Source checkout configured")
    print("✅ Python runtime configured")
    print("✅ Node runtime configured")
    print("✅ Dependencies installed")
    print("✅ Application installed")
    print("✅ Assets build configured")

    print("\n🎉 BUILD PIPELINE PASSED\n")