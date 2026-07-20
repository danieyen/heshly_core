from pathlib import Path


def test_docker_production():

    print("\n================================")
    print("Docker Production Setup")
    print("================================\n")

    dockerfile = Path("Dockerfile.production")

    compose = Path("docker-compose.production.yml")

    assert dockerfile.exists()

    assert compose.exists()

    assert "gunicorn" in dockerfile.read_text()

    assert "mysql" in compose.read_text()

    assert "redis" in compose.read_text()

    assert "restart: unless-stopped" in compose.read_text()

    print("✅ Dockerfile.production found")

    print("✅ docker-compose.production.yml found")

    print("✅ Production services configured")

    print("\n🎉 DOCKER PRODUCTION SETUP PASSED\n")