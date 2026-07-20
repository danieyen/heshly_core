from pathlib import Path


def test_nginx_configuration():

    print("\n================================")
    print("Nginx Configuration")
    print("================================\n")

    nginx = Path(
        "deployment/nginx/nginx.conf"
    )

    compose = Path(
        "docker-compose.production.yml"
    )

    assert nginx.exists()

    assert compose.exists()

    nginx_text = nginx.read_text()

    compose_text = compose.read_text()

    assert "proxy_pass" in nginx_text

    assert "listen 80" in nginx_text

    assert "upstream" in nginx_text

    assert "nginx:" in compose_text

    assert "container_name: heshly-nginx" in compose_text

    print("✅ nginx.conf found")

    print("✅ Reverse proxy configured")

    print("✅ Docker integration configured")

    print("\n🎉 NGINX CONFIGURATION PASSED\n")