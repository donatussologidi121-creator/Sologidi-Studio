#!/bin/bash
# Double-click this file to start Tamara.
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "Run setup first:  bash setup.sh"
  read -p "Press Enter to close."
  exit 1
fi
.venv/bin/python tamara.py
read -p "Tamara stopped. Press Enter to close."
