"""
Common test assertions.
"""


def assert_success(result):

    assert result is not None, (
        "Expected result but got None"
    )



def assert_healthy(service):

    health = service.health()

    assert health["status"] == "healthy", (
        f"Service unhealthy: {health}"
    )



def assert_has_fields(
    data,
    fields,
):

    for field in fields:

        assert field in data, (
            f"Missing field: {field}"
        )



def assert_status(
    response,
    expected,
):

    assert response["status"] == expected, (
        f"Expected {expected}, got {response['status']}"
    )
