from datetime import datetime, UTC
from uuid import uuid4


def tenant_fixture():

    return {
        "tenant_id": "tenant001",
        "name": "Test Business",
        "email": "test@business.com",
        "created_at": datetime.now(UTC),
    }



def user_fixture():

    return {
        "user_id": "user001",
        "tenant_id": "tenant001",
        "name": "Test User",
        "email": "user@test.com",
        "role": "admin",
    }



def customer_fixture():

    return {
        "customer_id": "customer001",
        "tenant_id": "tenant001",
        "name": "John Doe",
        "phone": "+254700000000",
        "email": "john@test.com",
    }



def appointment_fixture():

    return {
        "appointment_id": "appointment001",
        "tenant_id": "tenant001",
        "customer_id": "customer001",
        "service": "Consultation",
        "status": "confirmed",
    }



def lead_fixture():

    return {
        "lead_id": "lead001",
        "tenant_id": "tenant001",
        "name": "Potential Customer",
        "status": "new",
    }
