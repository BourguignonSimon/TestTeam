"""Command-line interface for managing a team roster."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .storage import TeamStorage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage team roster entries")
    parser.add_argument(
        "--file",
        default=Path("data/team.json"),
        type=Path,
        help="Path to the team data file (default: data/team.json)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new team member")
    add_parser.add_argument("name", help="Member name")
    add_parser.add_argument("role", nargs="?", default="", help="Member role")

    remove_parser = subparsers.add_parser("remove", help="Remove a team member")
    remove_parser.add_argument("name", help="Member name")

    subparsers.add_parser("list", help="List all team members")

    return parser


def handle_add(storage: TeamStorage, args: argparse.Namespace) -> str:
    member = storage.add_member(args.name, args.role)
    role_suffix = f" ({member['role']})" if member["role"] else ""
    return f"Added {member['name']}{role_suffix}."


def handle_remove(storage: TeamStorage, args: argparse.Namespace) -> str:
    member = storage.remove_member(args.name)
    role_suffix = f" ({member['role']})" if member["role"] else ""
    return f"Removed {member['name']}{role_suffix}."


def handle_list(storage: TeamStorage, args: argparse.Namespace) -> str:
    members: List[dict] = storage.list_members()
    if not members:
        return "No team members found."
    lines = ["Team members:"]
    for member in members:
        role_suffix = f" - {member['role']}" if member["role"] else ""
        lines.append(f"- {member['name']}{role_suffix}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> str:
    parser = build_parser()
    args = parser.parse_args(argv)
    storage = TeamStorage(args.file)

    handlers = {
        "add": handle_add,
        "remove": handle_remove,
        "list": handle_list,
    }
    handler = handlers[args.command]
    message = handler(storage, args)
    print(message)
    return message


if __name__ == "__main__":  # pragma: no cover
    main()

