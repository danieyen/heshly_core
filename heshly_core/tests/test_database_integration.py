from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Customer:
    id: str
    name: str


class InMemoryDatabase:

    def __init__(self):

        self.tables = {
            "customers": {}
        }

    def insert(self, table: str, obj):

        self.tables[table][obj.id] = obj

    def get(self, table: str, obj_id: str):

        return self.tables[table].get(obj_id)

    def update(self, table: str, obj):

        self.tables[table][obj.id] = obj

    def delete(self, table: str, obj_id: str):

        return self.tables[table].pop(obj_id, None)

    def count(self, table: str):

        return len(self.tables[table])


def test_database_integration():

    print("\n================================")
    print("Database Integration Test")
    print("================================\n")

    db = InMemoryDatabase()

    customer = Customer(
        id="CUST-001",
        name="John Doe",
    )

    # =====================================
    # Create
    # =====================================

    db.insert(
        "customers",
        customer,
    )

    assert db.count("customers") == 1

    print("✅ Insert")

    # =====================================
    # Read
    # =====================================

    loaded = db.get(
        "customers",
        "CUST-001",
    )

    assert loaded is not None
    assert loaded.name == "John Doe"

    print("✅ Read")

    # =====================================
    # Update
    # =====================================

    loaded.name = "Jane Doe"

    db.update(
        "customers",
        loaded,
    )

    updated = db.get(
        "customers",
        "CUST-001",
    )

    assert updated.name == "Jane Doe"

    print("✅ Update")

    # =====================================
    # Delete
    # =====================================

    db.delete(
        "customers",
        "CUST-001",
    )

    assert db.count("customers") == 0

    print("✅ Delete")

    print("\n🎉 DATABASE INTEGRATION TEST PASSED\n")