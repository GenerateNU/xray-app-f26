python := ".venv/bin/python"

# show all commands
default:
    @just --list

# make the venv and install everything
setup:
    python3 -m venv .venv
    {{python}} -m pip install --upgrade pip
    {{python}} -m pip install -r requirements.txt

# launch the app
run:
    {{python}} app/src/main.py