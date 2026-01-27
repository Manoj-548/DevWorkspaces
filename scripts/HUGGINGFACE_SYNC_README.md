# Hugging Face Cloud Sync for DevWorkspaces

This module provides cloud sync functionality for your datasets and configs using Hugging Face Hub.

## User Configuration

**Username:** `Manoj548`

## Setup

### 1. Install Dependencies
```bash
pip install huggingface_hub
```

### 2. Login to Hugging Face
```bash
# Option A: CLI Login
huggingface-cli login

# Option B: Environment Variable
export HF_TOKEN="your_token_here"

# Option C: Get token from
# https://huggingface.co/settings/tokens
```

### 3. Run Sync

```bash
# Sync all configured directories
python3 scripts/huggingface_sync.py --sync all

# Sync specific category
python3 scripts/huggingface_sync.py --sync datasets
python3 scripts/huggingface_sync.py --sync configs
python3 scripts/huggingface_sync.py --sync models

# List your repositories
python3 scripts/huggingface_sync.py --list

# Create shell sync script
python3 scripts/huggingface_sync.py --create-script
```

### 4. Use Shell Script
```bash
chmod +x scripts/hf_sync.sh
./scripts/hf_sync.sh
```

## Directories Configured for Sync

| Local Path | HF Repository | Type |
|------------|---------------|------|
| `projects/yolov8-poc/data` | `Manoj548/datasets` | dataset |
| `infra/` | `Manoj548/configs` | dataset |
| `projects/yolov8-poc/` | `Manoj548/models` | model |

## Repositories Created

Once you run the sync, the following repositories will be created:
- `Manoj548/datasets` - Your YOLOv8 datasets
- `Manoj548/configs` - Infrastructure configs
- `Manoj548/models` - Trained models and weights

## CI/CD Integration

Add to your `.github/workflows` to auto-sync on push:

```yaml
name: Sync to Hugging Face

on:
  push:
    branches: [main]

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install huggingface_hub
      - name: Sync to Hugging Face
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
        run: python3 scripts/huggingface_sync.py --sync all
```

**Note:** Store your Hugging Face token in GitHub Secrets as `HF_TOKEN`.

