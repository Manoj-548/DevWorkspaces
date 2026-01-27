#!/bin/bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🔧 Setting up DevWorkspace at $ROOT_DIR"

cd "$ROOT_DIR"

# core dirs
mkdir -p storage logs backups

SERVICES_DIR="$ROOT_DIR/services"

for svc in django_api backend ml dashboard; do
  echo "📦 Bootstrapping $svc..."

  cd "$SERVICES_DIR/$svc"

  if [ ! -f requirements.txt ]; then
    echo "⚠️  No requirements.txt in $svc — skipping pip install"
  else
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
  fi

done

cd "$ROOT_DIR/infra"

docker compose build

echo "✅ Done."
echo "👉 Run: docker compose up"
