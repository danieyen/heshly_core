"""
Test object factories.
"""

from uuid import uuid4
from datetime import datetime, UTC



def generate_id(prefix):

    return (
        f"{prefix}_{uuid4().hex[:8]}"
    )



def generate_tenant_id():

    return generate_id(
        "tenant"
    )



def generate_user_id():

    return generate_id(
        "user"
    )



def generate_customer_id():

    return generate_id(
        "customer"
    )



def generate_timestamp():

    return datetime.now(UTC)



def build_event(
    event_type="test",
):

    return {

        "event_id": generate_id(
            "event"
        ),

        "event_type": event_type,

        "created_at":
            generate_timestamp(),

    }
