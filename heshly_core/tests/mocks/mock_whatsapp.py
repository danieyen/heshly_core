"""
Mock WhatsApp Provider
"""


class MockWhatsAppService:


    def __init__(self):

        self.messages = []



    def send_message(
        self,
        phone,
        message,
    ):

        record = {

            "phone": phone,

            "message": message,

            "status": "sent",

        }

        self.messages.append(
            record
        )

        return record



    def get_messages(self):

        return self.messages



    def health(self):

        return {

            "service": "whatsapp",

            "status": "healthy",

        }
