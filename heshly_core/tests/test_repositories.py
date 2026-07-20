from heshly_core.repositories.base_repository import BaseRepository


class DummyEntity:

    def __init__(self, entity_id: str, name: str):
        self.id = entity_id
        self.name = name


class MemoryRepository(BaseRepository[DummyEntity]):

    def __init__(self):
        self._items = {}

    def save(self, entity):
        self._items[entity.id] = entity
        return entity

    def get(self, entity_id):
        return self._items.get(entity_id)

    def list(self):
        return list(self._items.values())

    def delete(self, entity_id):
        return self._items.pop(entity_id, None) is not None

    def exists(self, entity_id):
        return entity_id in self._items

    def count(self):
        return len(self._items)

    def clear(self):
        self._items.clear()


def test_base_repository():

    print("\n================================")
    print("Repository Tests")
    print("================================\n")

    repo = MemoryRepository()

    item = DummyEntity("1", "Test")

    repo.save(item)

    assert repo.count() == 1
    assert repo.exists("1")

    loaded = repo.get("1")

    assert loaded is not None
    assert loaded.name == "Test"

    assert len(repo.list()) == 1

    assert repo.delete("1") is True

    assert repo.count() == 0

    repo.save(DummyEntity("2", "A"))
    repo.save(DummyEntity("3", "B"))

    assert repo.count() == 2

    repo.clear()

    assert repo.count() == 0

    print("✅ Repository CRUD")
    print("\n🎉 REPOSITORY TESTS PASSED\n")