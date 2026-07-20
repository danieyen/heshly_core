"""
Mock AI Provider
"""


class MockAIService:


    def __init__(self):

        self.requests = []



    def generate_response(
        self,
        message,
    ):

        response = {

            "input":
                message,

            "response":
                "How can I help you?",

            "confidence":
                0.95,

        }

        self.requests.append(
            response
        )

        return response



    def health(self):

        return {

            "service": "ai",

            "status": "healthy",

        }
