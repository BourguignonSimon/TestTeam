# TestTeam

A small Python utility for managing a team roster. The project provides a CLI that stores team members in a JSON file so the data is easy to inspect and share.

## Features
- Add members with an optional role
- Remove members by name
- List current members in a friendly format
- Configurable storage path (defaults to `data/team.json`)

## Setup
Create and activate a virtual environment and install the package in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage
Run the CLI via the installed script or module entry point:

```bash
testteam --help
```

Examples:

```bash
# add members
python -m testteam.cli add "Ada Lovelace" "Lead Engineer"
python -m testteam.cli add "Grace Hopper"

# list
python -m testteam.cli list

# remove
python -m testteam.cli remove "Grace Hopper"
```

All commands support the `--file` flag to change where data is stored.

## Development
Install dev dependencies and run tests:

```bash
pip install -e .
pip install pytest
pytest
```

