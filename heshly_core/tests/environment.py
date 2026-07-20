"""
Heshly Core Test Environment Manager
"""

import os
from pathlib import Path


class TestEnvironment:


    def __init__(self):

        self.environment = (
            os.getenv(
                "ENVIRONMENT",
                "test"
            )
        )

        self.is_test = (
            self.environment == "test"
        )

        self.database = os.getenv(
            "DATABASE_NAME",
            "heshly_test"
        )

        self.debug = True



    def validate(self):

        if not self.is_test:

            raise RuntimeError(
                "Tests must run in test environment"
            )

        return True



    def settings(self):

        return {

            "environment":
                self.environment,

            "database":
                self.database,

            "debug":
                self.debug,

        }



    def health(self):

        return {

            "environment":
                self.environment,

            "status":
                "healthy",

        }
