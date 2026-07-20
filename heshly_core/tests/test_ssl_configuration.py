from pathlib import Path


def test_ssl_configuration():

    print("\n================================")
    print("SSL/TLS Configuration")
    print("================================\n")

    ssl_conf = Path(
        "deployment/nginx/ssl.conf"
    )

    compose = Path(
        "docker-compose.production.yml"
    )

    cert = Path(
        "deployment/ssl/fullchain.pem"
    )

    key = Path(
        "deployment/ssl/privkey.pem"
    )

    assert ssl_conf.exists()

    assert compose.exists()

    assert cert.exists()

    assert key.exists()

    text = ssl_conf.read_text()

    assert "listen 443 ssl" in text

    assert "TLSv1.2" in text

    assert "TLSv1.3" in text

    assert "Strict-Transport-Security" in text

    compose_text = compose.read_text()

    assert '"443:443"' in compose_text

    print("✅ SSL configuration found")

    print("✅ HTTPS enabled")

    print("✅ Certificates configured")

    print("✅ TLS security headers configured")

    print("\n🎉 SSL/TLS SETUP PASSED\n")