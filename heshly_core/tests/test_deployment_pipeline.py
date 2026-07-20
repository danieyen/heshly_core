from pathlib import Path


def test_deployment_pipeline():

    print("\n================================")
    print("Deployment Pipeline")
    print("================================\n")

    workflow = Path(".github/workflows/ci.yml")
    compose = Path("docker-compose.production.yml")
    dockerfile = Path("Dockerfile.production")

    assert workflow.exists()
    assert compose.exists()
    assert dockerfile.exists()

    workflow_text = workflow.read_text()
    compose_text = compose.read_text()
    docker_text = dockerfile.read_text()

    # Build
    assert "bench build" in workflow_text

    # Tests
    assert "run-tests --app heshly_core" in workflow_text

    # Production image
    assert "gunicorn" in docker_text

    # Production services
    assert "restart: unless-stopped" in compose_text
    assert "heshly" in compose_text
    assert "nginx" in compose_text
    assert "mysql" in compose_text
    assert "redis" in compose_text

    print("✅ CI workflow detected")
    print("✅ Production Dockerfile detected")
    print("✅ Docker Compose detected")
    print("✅ Production services configured")
    print("✅ Deployment pipeline verified")

    print("\n🎉 DEPLOYMENT PIPELINE PASSED\n")