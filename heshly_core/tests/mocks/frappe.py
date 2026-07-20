"""
Minimal frappe mock for standalone tests.
"""


class MockDB:


    def get_value(
        self,
        *args,
        **kwargs
    ):

        return None



    def exists(
        self,
        *args,
        **kwargs
    ):

        return False



db = MockDB()



def get_all(
    *args,
    **kwargs
):

    return []



def get_doc(
    *args,
    **kwargs
):

    return None
