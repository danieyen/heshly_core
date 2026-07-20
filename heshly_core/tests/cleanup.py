"""
Test cleanup utilities.
"""


class TestCleanup:


    def __init__(self):

        self.resources = []



    def register(
        self,
        resource,
    ):

        self.resources.append(
            resource
        )



    def cleanup(self):

        for resource in self.resources:

            if hasattr(
                resource,
                "clear"
            ):

                resource.clear()



        self.resources.clear()



    def health(self):

        return {

            "status":
                "healthy",

        }
