"""
Test database lifecycle manager.
"""


class TestDatabase:


    def __init__(self):

        self.connected = False

        self.records = []



    def connect(self):

        self.connected = True

        return True



    def disconnect(self):

        self.connected = False



    def insert(
        self,
        record,
    ):

        self.records.append(
            record
        )

        return record



    def clear(self):

        self.records.clear()



    def count(self):

        return len(
            self.records
        )



    def health(self):

        return {

            "database":
                "test",

            "status":
                "healthy",

        }
