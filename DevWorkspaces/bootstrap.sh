#!/usr/bin/env bash
set -e

echo "=============================="
echo "🚀 Bootstrapping Dev Workspace"
echo "=============================="

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essentials
echo "🔧 Installing base tools..."
sudo apt install -y \
  build-essential \
  curl \
  git \
  wget \
  unzip \
  ca-certificates \
  software-properties-common \
  gnupg \
  lsb-release

# Install Python + pip + venv
echo "🐍 Installing Python tools..."
sudo apt install -y python3 python3-pip python3-venv

# Install Docker if not present
if ! command -v docker &> /dev/null; then
  echo "🐳 Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker $USER
else
  echo "🐳 Docker already installed."
fi

# Install docker-compose plugin if needed
if ! docker compose version &> /dev/null; then
  echo "📦 Installing docker-compose plugin..."
  sudo apt install -y docker-compose-plugin
fi

# Create venv if not exists
if [ ! -d "venv" ]; then
  echo "📂 Creating Python virtual environment..."
  python3 -m venv venv
fi

# Activate venv
echo "⚡ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python deps if requirements.txt exists
if [ -f "requirements.txt" ]; then
  echo "📜 Installing Python requirements..."
  pip install -r requirements.txt
else
  echo "⚠️ requirements.txt not found – skipping."
fi

# Django migrations if manage.py exists
if [ -f "manage.py" ]; then
  echo "🗄️ Running Django migrations..."
  python manage.py migrate || true
fi

echo "=============================="
echo "✅ Bootstrap complete!"
echo "Restart terminal if Docker group was added."
echo "=============================="
