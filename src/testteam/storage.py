"""Storage helpers for team roster data."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Dict


class TeamStorage:
    """Persist and retrieve team member data.

    Data is stored as a list of dictionaries with ``name`` and ``role`` keys.
    The storage format is intentionally simple JSON so the file can be inspected
    and edited by hand when needed.
    """

    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> List[Dict[str, str]]:
        if not self.path.exists():
            return []
        try:
            with self.path.open("r", encoding="utf-8") as fp:
                data = json.load(fp)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in {self.path}")

        if not isinstance(data, list):
            raise ValueError("Team data must be a list of objects")

        normalized = []
        for member in data:
            if not isinstance(member, dict):
                raise ValueError("Team entries must be objects")
            name = str(member.get("name", "")).strip()
            role = str(member.get("role", "")).strip()
            if not name:
                raise ValueError("Team member missing name")
            normalized.append({"name": name, "role": role})
        return normalized

    def save(self, members: Iterable[Dict[str, str]]) -> None:
        members_list = [
            {"name": m.get("name", "").strip(), "role": m.get("role", "").strip()}
            for m in members
        ]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fp:
            json.dump(members_list, fp, indent=2)

    def add_member(self, name: str, role: str = "") -> Dict[str, str]:
        name = name.strip()
        role = role.strip()
        if not name:
            raise ValueError("Name cannot be empty")

        members = self.load()
        existing = {m["name"].lower(): m for m in members}
        if name.lower() in existing:
            raise ValueError(f"Member '{name}' already exists")

        new_member = {"name": name, "role": role}
        members.append(new_member)
        self.save(members)
        return new_member

    def remove_member(self, name: str) -> Dict[str, str]:
        name = name.strip()
        if not name:
            raise ValueError("Name cannot be empty")

        members = self.load()
        remaining = []
        removed = None
        for member in members:
            if member["name"].lower() == name.lower():
                removed = member
            else:
                remaining.append(member)

        if removed is None:
            raise ValueError(f"Member '{name}' not found")

        self.save(remaining)
        return removed

    def list_members(self) -> List[Dict[str, str]]:
        return self.load()

