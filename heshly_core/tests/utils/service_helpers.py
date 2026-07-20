"""
Helpers for initializing services.
"""


def check_service_health(
    services,
):

    results = {}

    for name, service in services.items():

        results[name] = (
            service.health()
        )

    return results



def all_services_healthy(
    services,
):

    results = check_service_health(
        services
    )

    return all(
        item["status"] == "healthy"
        for item in results.values()
    )
