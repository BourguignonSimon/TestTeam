from pathlib import Path
import json
import pytest

from testteam.storage import TeamStorage


def test_add_and_list_members(tmp_path: Path):
    path = tmp_path / "team.json"
    storage = TeamStorage(path)

    storage.add_member("Alice", "Developer")
    storage.add_member("Bob")

    members = storage.list_members()
    assert members == [
        {"name": "Alice", "role": "Developer"},
        {"name": "Bob", "role": ""},
    ]


def test_duplicate_member_rejected(tmp_path: Path):
    storage = TeamStorage(tmp_path / "team.json")
    storage.add_member("Charlie")
    with pytest.raises(ValueError):
        storage.add_member("charlie")


def test_remove_member(tmp_path: Path):
    storage = TeamStorage(tmp_path / "team.json")
    storage.add_member("Dana")
    removed = storage.remove_member("Dana")
    assert removed["name"] == "Dana"
    assert storage.list_members() == []


def test_remove_missing_member_raises(tmp_path: Path):
    storage = TeamStorage(tmp_path / "team.json")
    with pytest.raises(ValueError):
        storage.remove_member("Eve")


def test_save_invalid_json(tmp_path: Path):
    path = tmp_path / "team.json"
    path.write_text("not json", encoding="utf-8")
    storage = TeamStorage(path)
    with pytest.raises(ValueError):
        storage.load()


def test_load_requires_list(tmp_path: Path):
    path = tmp_path / "team.json"
    path.write_text(json.dumps({"name": "Solo"}), encoding="utf-8")
    storage = TeamStorage(path)
    with pytest.raises(ValueError):
        storage.load()

