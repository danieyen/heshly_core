"""
API testing helpers.
"""


def validate_response(
    response,
    expected_status=None,
):

    assert response is not None


    if expected_status:

        assert (
            response["status"]
            ==
            expected_status
        )


    return True
