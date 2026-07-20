def test_environment(
    test_env,
):

    assert (
        test_env.is_test
        is True
    )

    assert (
        test_env.health()["status"]
        ==
        "healthy"
    )



def test_database(
    test_database,
):

    test_database.insert(
        {
            "id":1
        }
    )

    assert (
        test_database.count()
        ==
        1
    )



def test_cleanup(
    cleanup,
):

    cleanup.register(
        []
    )

    cleanup.cleanup()

    assert True
