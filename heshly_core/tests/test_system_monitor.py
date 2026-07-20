from heshly_core.services.admin.system_monitor import (
    SystemMonitor,
)


class MockService:

    def health(self):

        return {

            "service":
                "mock_service",

            "status":
                "healthy",

        }



def run_test():

    print("\n================================")
    print("System Monitor Test")
    print("================================\n")


    monitor = SystemMonitor()


    monitor.register_service(

        "mock_service",

        MockService()

    )


    print("✅ Service registered")


    result = monitor.check_service(
        "mock_service"
    )


    assert result["status"] == "healthy"

    print("✅ Service health checked")


    report = monitor.health_report()


    assert (
        "mock_service"
        in report["services"]
    )

    print("✅ Health report generated")


    status = monitor.system_status()


    assert status["status"] == "healthy"

    print("✅ System status healthy")


    assert (
        monitor.health()["status"]
        ==
        "healthy"
    )

    print("✅ Monitor health")


    print(
        "\n🎉 SYSTEM MONITOR TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()