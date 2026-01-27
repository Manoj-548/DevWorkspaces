#!/usr/bin/env python3
"""
Hugging Face Cloud Sync for DevWorkspaces
User: Manoj548
Purpose: Sync backend data (datasets, models, configs) to Hugging Face Hub
"""

import os
import sys
from pathlib import Path

try:
    from huggingface_hub import HfApi, hf_hub_download
except ImportError:
    print("Installing huggingface_hub...")
    os.system("pip install huggingface_hub -q")
    from huggingface_hub import HfApi, hf_hub_download

# Configuration
HF_USER = "Manoj548"
REPO_TYPE = "dataset"  # or "model" for ML models

# Directories to sync
LOCAL_DATA_DIRS = {
    "datasets": "projects/yolov8-poc/data",
    "configs": "infra/",
    "models": "projects/yolov8-poc/",
}

# Ignore patterns
IGNORE_PATTERNS = [
    "*.pyc",
    "__pycache__",
    ".git",
    "*.log",
    "venv",
    ".env",
]


def login():
    """Login to Hugging Face"""
    from huggingface_hub import login
    token = os.environ.get("HF_TOKEN")
    if token:
        login(token=token)
        print("✅ Logged in using HF_TOKEN environment variable")
    else:
        print("⚠️ No HF_TOKEN found. Run 'huggingface-cli login' or set HF_TOKEN env var")
        print("   Get token from: https://huggingface.co/settings/tokens")


def list_repos():
    """List user's repositories"""
    api = HfApi()
    repos = api.list_repos(user=HF_USER, repo_type="both")
    print(f"\n📂 Repositories for @{HF_USER}:")
    for repo in repos:
        print(f"   - {repo.repo_type}: {repo.repo_id}")


def upload_directory(local_path, repo_id, repo_type="dataset"):
    """Upload a directory to Hugging Face"""
    api = HfApi()
    
    local_path = Path(local_path)
    if not local_path.exists():
        print(f"❌ Directory not found: {local_path}")
        return False
    
    print(f"\n📤 Uploading {local_path} to {repo_id} ({repo_type})...")
    
    try:
        api.upload_folder(
            folder_path=str(local_path),
            repo_id=repo_id,
            repo_type=repo_type,
            commit_message=f"Update {local_path.name}",
        )
        print(f"✅ Successfully uploaded {local_path}")
        return True
    except Exception as e:
        print(f"❌ Error uploading {local_path}: {e}")
        return False


def download_file(repo_id, filename, local_path="."):
    """Download a file from Hugging Face"""
    api = HfApi()
    
    print(f"\n📥 Downloading {filename} from {repo_id}...")
    
    try:
        local_file = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            repo_type="dataset",
            local_dir=local_path
        )
        print(f"✅ Downloaded to: {local_file}")
        return local_file
    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")
        return None


def sync_all():
    """Sync all configured directories"""
    login()
    
    print(f"\n🚀 Starting Hugging Face sync for @{HF_USER}")
    print("=" * 50)
    
    success_count = 0
    total = len(LOCAL_DATA_DIRS)
    
    for name, local_path in LOCAL_DATA_DIRS.items():
        repo_id = f"{HF_USER}/{name}"
        
        if os.path.exists(local_path):
            if upload_directory(local_path, repo_id, repo_type="dataset"):
                success_count += 1
        else:
            print(f"⏭️  Skipping {name}: {local_path} not found")
    
    print(f"\n✅ Sync complete: {success_count}/{total} directories uploaded")


def create_sync_script():
    """Create a sync script for easy use"""
    script_content = '''#!/bin/bash
# Hugging Face Sync Script for DevWorkspaces
# User: Manoj548

echo "🤗 Hugging Face Sync - DevWorkspaces"
echo "======================================"

# Set Hugging Face token (get from https://huggingface.co/settings/tokens)
# export HF_TOKEN="your_token_here"

# Sync datasets
echo "📤 Syncing datasets..."
python3 scripts/huggingface_sync.py --sync datasets

# Sync configs
echo "📤 Syncing configs..."
python3 scripts/huggingface_sync.py --sync configs

echo "✅ All data synced to Hugging Face!"
'''
    
    script_path = Path("/home/manoj/DevWorkspaces/scripts/hf_sync.sh")
    script_path.write_text(script_content)
    os.chmod(script_path, 0o755)
    print(f"✅ Created sync script: {script_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Hugging Face Cloud Sync for DevWorkspaces"
    )
    parser.add_argument(
        "--sync",
        choices=["all", "datasets", "configs", "models"],
        default="all",
        help="What to sync (default: all)"
    )
    parser.add_argument(
        "--download",
        metavar="FILE",
        help="Download a file from Hugging Face"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List user's repositories"
    )
    parser.add_argument(
        "--create-script",
        action="store_true",
        help="Create a shell sync script"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_repos()
    elif args.create_script:
        create_sync_script()
    elif args.download:
        download_file(
            repo_id=f"{HF_USER}/{args.download.split('/')[0]}",
            filename=args.download.split('/')[-1]
        )
    elif args.sync:
        sync_all()
    else:
        sync_all()


if __name__ == "__main__":
    main()

