"""
Mock Calendar Provider
"""


class MockCalendarService:


    def __init__(self):

        self.events = []



    def create_event(
        self,
        title,
        start,
        end,
    ):

        event = {

            "event_id":
                f"event_{len(self.events)+1}",

            "title": title,

            "start": start,

            "end": end,

            "status": "created",

        }

        self.events.append(
            event
        )

        return event



    def list_events(self):

        return self.events



    def health(self):

        return {

            "service": "calendar",

            "status": "healthy",

        }
