import json
from pathlib import Path

from testteam import cli
from testteam.storage import TeamStorage


def run_cli(tmp_path: Path, args: list[str]):
    file_path = tmp_path / "team.json"
    argv = ["--file", str(file_path), *args]
    return cli.main(argv)


def test_cli_add_and_list(tmp_path):
    message = run_cli(tmp_path, ["add", "Alice", "Manager"])
    assert "Added Alice (Manager)." == message

    message = run_cli(tmp_path, ["list"])
    assert "Team members:" in message
    assert "- Alice - Manager" in message


def test_cli_remove(tmp_path):
    storage = TeamStorage(tmp_path / "team.json")
    storage.add_member("Bob", "Engineer")

    message = run_cli(tmp_path, ["remove", "Bob"])
    assert "Removed Bob (Engineer)." == message


def test_cli_list_empty(tmp_path):
    message = run_cli(tmp_path, ["list"])
    assert message == "No team members found."

