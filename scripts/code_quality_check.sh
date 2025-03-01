#!/bin/bash
set -e

cd "$(dirname "$0")/.."
folder=argus
ruff format --check $folder
ruff check $folder
mypy $folder