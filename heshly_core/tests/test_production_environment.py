from heshly_core.config.production import config


def test_production_environment():

    print("\n================================")
    print("Production Environment")
    print("================================\n")

    assert config.environment == "production"

    assert config.debug is False

    assert config.ssl_enabled

    assert config.monitoring_enabled

    assert config.metrics_enabled

    assert config.backup_enabled

    assert config.workers >= 1

    print("Application :", config.app_name)
    print("Environment :", config.environment)
    print("Database    :", config.database_url)
    print("Redis       :", config.redis_url)
    print("Workers     :", config.workers)

    print("\n🎉 PRODUCTION ENVIRONMENT PASSED\n")