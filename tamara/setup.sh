#!/bin/bash
# One-time setup for Tamara on a Mac. Run:  bash setup.sh
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is missing. Run:  xcode-select --install   then run this script again."
  exit 1
fi

echo "Creating Tamara's private Python environment..."
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo "Created the .env file. Open it (open -e .env) and paste your Anthropic API key."
fi

echo ""
echo "Setup finished. Next: put your API key in .env, then double-click start_tamara.command"
