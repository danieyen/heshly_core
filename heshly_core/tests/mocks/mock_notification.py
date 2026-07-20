"""
Mock Email/SMS Notification Provider
"""


class MockNotificationService:


    def __init__(self):

        self.notifications = []



    def send(
        self,
        recipient,
        message,
    ):

        notification = {

            "recipient":
                recipient,

            "message":
                message,

            "status":
                "sent",

        }

        self.notifications.append(
            notification
        )

        return notification



    def health(self):

        return {

            "service":
                "notification",

            "status":
                "healthy",

        }
