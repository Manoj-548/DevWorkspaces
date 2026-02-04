#!/usr/bin/env bash
set -euo pipefail

# ---------- Config ----------
USER="$(whoami)"
METAROOT="$HOME/.devmeta"
LOGDIR="$METAROOT/logs"
BINDIR="$HOME/.local/bin"
WORKROOT="$HOME/DevWorkspaces"
DJANGO="$WORKROOT/DjangoService"
ML="$WORKROOT/ModelBuilding"
SYNC_SCRIPT="$METAROOT/devmeta-sync-inotify.sh"
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_UNIT="$SERVICE_DIR/devmeta-sync.service"
APPROVER="$METAROOT/sync-approve.sh"
DEVMETA="$BINDIR/devmeta"
VINDASH="$BINDIR/vindash"
GPG_KEY=""
GIT_NAME="Manoj M R"
GIT_EMAIL="manojm@indusvision.ai-IV033"
# default excludes (large models excluded)
EXCLUDE_ARGS=(--exclude='venv' --exclude='.git' --exclude='*.pt' --exclude='*.ckpt' --exclude='models' --exclude='checkpoints' --exclude='*.bin' --exclude='*.h5')

mkdir -p "$METAROOT" "$LOGDIR" "$BINDIR" "$WORKROOT" "$SERVICE_DIR" "$METAROOT/conflicts"
chmod 700 "$METAROOT"

echo "=== DevMeta Unified Dev Terminal installer ==="
echo "Office identity will be set to: $GIT_EMAIL"
read -p "Proceed with installation (interactive) ? (Y/N): " ok
if [[ "${ok^^}" != "Y" ]]; then echo "Aborted."; exit 1; fi

# ---------- apt packages ----------
read -p "Install required packages now? (sudo required) (Y/N): " aptyn
if [[ "${aptyn^^}" == "Y" ]]; then
  sudo apt update
  sudo apt install -y python3 python3-venv python3-pip rsync p7zip-full restic git pre-commit jq curl gnupg inotify-tools gh pass openssh-client
fi

# ---------- optional limited sudoers (no repeated password) ----------
echo
echo "OPTIONAL: add a limited sudoers rule so installer/automation commands won't repeatedly ask for your password."
echo "This will only allow your user to run (apt/apt-get/dpkg/systemctl/docker) WITHOUT password."
read -p "Add limited NOPASSWD sudoers for automation commands? (Y/N): " snop
if [[ "${snop^^}" == "Y" ]]; then
  SUDOFILE="/etc/sudoers.d/devmeta-$USER"
  echo "[INFO] creating limited sudoers entry at $SUDOFILE (you will be prompted for sudo now)"
  sudo bash -c "cat > $SUDOFILE <<EOF
# DevMeta limited passwordless sudo for automation commands
$USER ALL=(ALL) NOPASSWD: /usr/bin/apt, /usr/bin/apt-get, /usr/bin/dpkg, /bin/systemctl, /usr/bin/systemctl, /usr/bin/docker
EOF
chmod 0440 $SUDOFILE
echo 'Created limited sudoers entry.'"
fi

# ---------- create workspaces ----------
for p in "$DJANGO" "$ML"; do
  if [[ ! -d "$p" ]]; then
    read -p "Create workspace $p ? (Y/N): " c
    if [[ "${c^^}" == "Y" ]]; then mkdir -p "$p"; echo "[INSTALL] created $p" | tee -a "$LOGDIR/install.log"; fi
  else
    echo "[FOUND] $p"
  fi
done

# ---------- python venvs ----------
PY="$(command -v python3)"
if [[ -z "$PY" ]]; then echo "python3 not found; install and re-run."; exit 1; fi
for ws in "$DJANGO" "$ML"; do
  VENV="$ws/venv"
  if [[ ! -d "$VENV" ]]; then
    read -p "Create python venv at $VENV? (Y/N): " rv
    if [[ "${rv^^}" == "Y" ]]; then $PY -m venv "$VENV"; echo "[INSTALL] venv:$VENV" | tee -a "$LOGDIR/install.log"; fi
  fi
done

# ---------- git config ----------
git config --global user.name "$GIT_NAME"
git config --global user.email "$GIT_EMAIL"
echo "[INSTALL] git global identity set: $GIT_NAME <$GIT_EMAIL>"

# ---------- GPG for commit signing (optional) ----------
echo
read -p "Would you like to create a GPG key for commit signing or use an existing one? (new/existing/skip): " gopt
if [[ "${gopt,,}" == "existing" ]]; then
  gpg --list-secret-keys --keyid-format LONG
  read -p "Enter GPG key id/email to use: " GPG_KEY
  git config --global user.signingkey "$GPG_KEY"
  git config --global commit.gpgsign true
  echo "[INSTALL] configured git to sign commits with $GPG_KEY"
elif [[ "${gopt,,}" == "new" ]]; then
  cat > /tmp/gpgbatch <<'GPGBAT'
Key-Type: default
Key-Length: 4096
Subkey-Type: default
Name-Real: Manoj M R
Name-Email: manojm@indusvision.ai
Expire-Date: 0
%no-protection
%commit
GPGBAT
  gpg --batch --generate-key /tmp/gpgbatch
  rm -f /tmp/gpgbatch
  GPG_KEY="$(gpg --list-secret-keys --keyid-format LONG | awk '/sec/{print $2}' | head -n1)"
  git config --global user.signingkey "$GPG_KEY"
  git config --global commit.gpgsign true
  echo "[INSTALL] generated and configured GPG key: $GPG_KEY"
fi

# ---------- SSH key (for GitHub) ----------
if [[ ! -f "$HOME/.ssh/id_ed25519" ]]; then
  read -p "Generate a new SSH keypair for Git (id_ed25519)? (Y/N): " sk
  if [[ "${sk^^}" == "Y" ]]; then
    ssh-keygen -t ed25519 -C "$GIT_EMAIL" -f "$HOME/.ssh/id_ed25519" -N ""
    echo "[INSTALL] generated SSH key at ~/.ssh/id_ed25519"
  fi
else
  echo "SSH key already exists: ~/.ssh/id_ed25519"
fi

# ---------- GitHub auth (PAT or gh) ----------
echo
echo "Authenticate to GitHub: you can use the 'gh auth login' interactive flow (recommended) OR provide a Personal Access Token (PAT)."
read -p "Use gh interactive login or provide PAT? (gh/pat/skip): " ghopt
if [[ "${ghopt,,}" == "gh" ]]; then
  if command -v gh >/dev/null 2>&1; then
    gh auth login
    # add SSH key to GitHub (if present)
    if [[ -f "$HOME/.ssh/id_ed25519.pub" ]]; then
      read -p "Upload local SSH public key to GitHub now? (Y/N): " upk
      if [[ "${upk^^}" == "Y" ]]; then
        gh ssh-key add "$HOME/.ssh/id_ed25519.pub" --title "devmeta-$(hostname)-$(date +%Y%m%d)"
        echo "[INSTALL] uploaded SSH pubkey to GitHub"
      fi
    fi
  else
    echo "gh not installed; skip. You can run 'gh auth login' manually later."
  fi
elif [[ "${ghopt,,}" == "pat" ]]; then
  read -s -p "Enter GitHub Personal Access Token (scopes: repo, admin:public_key optional): " GHTOKEN; echo
  # store token in pass if available, otherwise in local file (restricted)
  if command -v pass >/dev/null 2>&1; then
    pass insert -m devmeta/github/token <<< "$GHTOKEN"
    echo "[INSTALL] stored GH token in pass"
  else
    mkdir -p "$METAROOT"
    echo "GITHUB_TOKEN=$GHTOKEN" > "$METAROOT/credentials"
    chmod 600 "$METAROOT/credentials"
    echo "[WARN] stored GH token in $METAROOT/credentials (use pass for better security)"
  fi
fi

# ---------- Docker login (store in pass) ----------
if command -v docker >/dev/null 2>&1; then
  read -p "Do you want to save Docker Hub credentials to pass and perform docker login now? (Y/N): " dockopt
  if [[ "${dockopt^^}" == "Y" ]]; then
    read -p "Docker Hub username: " DUSER
    read -s -p "Docker Hub password/token: " DPASS; echo
    if command -v pass >/dev/null 2>&1; then
      pass insert -m devmeta/docker/username <<< "$DUSER"
      pass insert -m devmeta/docker/token <<< "$DPASS"
      echo "$DPASS" | docker login --username "$DUSER" --password-stdin
      echo "[INSTALL] docker login done and credentials stored in pass"
    else
      echo "[WARN] pass not available; skipping secure storage"
    fi
  fi
fi

# ---------- create inotify sync script (excludes large model folders by default) ----------
cat > "$SYNC_SCRIPT" <<'INOT'
#!/usr/bin/env bash
set -euo pipefail
D1="$HOME/DevWorkspaces/DjangoService"
D2="$HOME/DevWorkspaces/ModelBuilding"
LOG="$HOME/.devmeta/logs/sync-inotify.log"
CONFLICTS="$HOME/.devmeta/conflicts/conflicts.txt"
mkdir -p "$(dirname "$LOG")" "$(dirname "$CONFLICTS")"
# default excludes to avoid model churn — can be edited later
EXCLUDE_ARGS=(--exclude='venv' --exclude='.git' --exclude='*.pt' --exclude='*.ckpt' --exclude='models' --exclude='checkpoints' --exclude='*.bin' --exclude='*.h5')
record_conflict(){ echo "$1|$2" >> "$CONFLICTS"; echo "[CONFLICT] $(date) $1 -> $2" >> "$LOG"; }
# initial reconcile: copy only missing files; record conflicts if differing
reconcile_once(){
  while IFS= read -r -d '' f; do
    rel="${f#$D1/}"; tgt="$D2/$rel"
    # skip excluded patterns via simple check (rsync-style exclusion optional)
    if [[ "$f" == *".pt" ]] || [[ "$f" == *".ckpt" ]] || [[ "$f" == */models/* ]] || [[ "$f" == */checkpoints/* ]]; then continue; fi
    if [[ ! -e "$tgt" ]]; then mkdir -p "$(dirname "$tgt")"; cp -p "$f" "$tgt" || true; echo "[SYNC] $(date) copied $rel D1->D2" >> "$LOG"; else
      shash="$(sha256sum "$f" | cut -d' ' -f1 2>/dev/null || echo '')"
      thash="$(sha256sum "$tgt" | cut -d' ' -f1 2>/dev/null || echo '')"
      [[ -n "$shash" && -n "$thash" && "$shash" != "$thash" ]] && record_conflict "$f" "$tgt"
    fi
  done < <(find "$D1" -type f -print0)
  while IFS= read -r -d '' f; do
    rel="${f#$D2/}"; tgt="$D1/$rel"
    if [[ "$f" == *".pt" ]] || [[ "$f" == *".ckpt" ]] || [[ "$f" == */models/* ]] || [[ "$f" == */checkpoints/* ]]; then continue; fi
    if [[ ! -e "$tgt" ]]; then mkdir -p "$(dirname "$tgt")"; cp -p "$f" "$tgt" || true; echo "[SYNC] $(date) copied $rel D2->D1" >> "$LOG"; else
      shash="$(sha256sum "$f" | cut -d' ' -f1 2>/dev/null || echo '')"
      thash="$(sha256sum "$tgt" | cut -d' ' -f1 2>/dev/null || echo '')"
      [[ -n "$shash" && -n "$thash" && "$shash" != "$thash" ]] && record_conflict "$f" "$tgt"
    fi
  done < <(find "$D2" -type f -print0)
}
reconcile_once
# inotify loop
inotifywait -m -r -e close_write,create,delete,move --format '%w%f %e' "$D1" "$D2" | while read -r file event; do
  if [[ "$file" == "$D1/"* ]]; then rel="${file#$D1/}"; other="$D2/$rel"; src="$file"; tgt="$other"
    if [[ "$event" == *DELETE* ]]; then echo "[SYNC] $(date) delete $rel" >> "$LOG"; continue; fi
    if [[ "$src" == *".pt" ]] || [[ "$src" == *".ckpt" ]] || [[ "$src" == */models/* ]] || [[ "$src" == */checkpoints/* ]]; then continue; fi
    if [[ ! -e "$tgt" ]]; then mkdir -p "$(dirname "$tgt")"; cp -p "$src" "$tgt" || true; echo "[SYNC] $(date) copied $rel D1->D2" >> "$LOG"
    else shash="$(sha256sum "$src" | cut -d' ' -f1 2>/dev/null || echo '')"; thash="$(sha256sum "$tgt" | cut -d' ' -f1 2>/dev/null || echo '')"
      [[ -n "$shash" && -n "$thash" && "$shash" != "$thash" ]] && record_conflict "$src" "$tgt"
    fi
  elif [[ "$file" == "$D2/"* ]]; then rel="${file#$D2/}"; other="$D1/$rel"; src="$file"; tgt="$other"
    if [[ "$event" == *DELETE* ]]; then echo "[SYNC] $(date) delete $rel" >> "$LOG"; continue; fi
    if [[ "$src" == *".pt" ]] || [[ "$src" == *".ckpt" ]] || [[ "$src" == */models/* ]] || [[ "$src" == */checkpoints/* ]]; then continue; fi
    if [[ ! -e "$tgt" ]]; then mkdir -p "$(dirname "$tgt")"; cp -p "$src" "$tgt" || true; echo "[SYNC] $(date) copied $rel D2->D1" >> "$LOG"
    else shash="$(sha256sum "$src" | cut -d' ' -f1 2>/dev/null || echo '')"; thash="$(sha256sum "$tgt" | cut -d' ' -f1 2>/dev/null || echo '')"
      [[ -n "$shash" && -n "$thash" && "$shash" != "$thash" ]] && record_conflict "$src" "$tgt"
    fi
  fi
done
INOT
chmod +x "$SYNC_SCRIPT"
echo "[INSTALL] wrote sync script: $SYNC_SCRIPT"

# ---------- systemd user unit ----------
cat > "$SERVICE_UNIT" <<UNIT
[Unit]
Description=DevMeta inotify Sync Service (user)
After=network-online.target

[Service]
Type=simple
ExecStart=$SYNC_SCRIPT
Restart=always
RestartSec=5
Environment=HOME=$HOME

[Install]
WantedBy=default.target
UNIT

# enable service
if command -v systemctl >/dev/null 2>&1 && systemctl --user --version >/dev/null 2>&1; then
  systemctl --user daemon-reload || true
  systemctl --user enable --now devmeta-sync.service || true
  echo "[SERVICE] devmeta-sync.service enabled (user)"
else
  echo "[WARN] systemd user not available. Start: $SYNC_SCRIPT manually or enable systemd in WSL."
fi

# ---------- conflict approver ----------
cat > "$APPROVER" <<'AP'
#!/usr/bin/env bash
set -euo pipefail
CONFLICTS="$HOME/.devmeta/conflicts/conflicts.txt"
LOG="$HOME/.devmeta/logs/sync.log"
if [[ ! -f "$CONFLICTS" ]]; then echo "No conflicts."; exit 0; fi
nl -ba "$CONFLICTS"
while IFS= read -r line; do
  IFS='|' read -r src tgt <<< "$line"
  rel="${src#*/DevWorkspaces/}"
  echo
  echo "Conflict: $rel"
  echo "1) Keep source -> copy $src -> $tgt"
  echo "2) Keep target -> copy $tgt -> $src"
  echo "3) Skip"
  read -p "Choose [1/2/3]: " ch
  case "$ch" in
    1) mkdir -p "$(dirname "$tgt")"; cp -p "$src" "$tgt"; echo "[RESOLVE] $(date) $rel kept source" >> "$LOG";;
    2) mkdir -p "$(dirname "$src")"; cp -p "$tgt" "$src"; echo "[RESOLVE] $(date) $rel kept target" >> "$LOG";;
    *) echo "[RESOLVE] $(date) $rel skipped" >> "$LOG";;
  esac
done < "$CONFLICTS"
rm -f "$CONFLICTS"
echo "Conflicts resolved."
AP
chmod +x "$APPROVER"
echo "[INSTALL] wrote conflict approver: $APPROVER"

# ---------- pre-commit config ----------
PRECOMMIT_CFG="$METAROOT/pre-commit-config.yaml"
cat > "$PRECOMMIT_CFG" <<'PC'
repos:
- repo: https://github.com/psf/black
  rev: stable
  hooks:
  - id: black
    language_version: python3
- repo: https://github.com/pycqa/ruff
  rev: stable
  hooks:
  - id: ruff
    args: [--fix]
- repo: https://github.com/pre-commit/mirrors-isort
  rev: v5.12.0
  hooks:
  - id: isort
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v4.4.0
  hooks:
  - id: check-added-large-files
    args: ['--maxkb=10240']
PC

for repo in "$DJANGO" "$ML"; do
  if [[ -d "$repo" ]]; then
    cp "$PRECOMMIT_CFG" "$repo/.pre-commit-config.yaml"
    (cd "$repo" && pre-commit install) || echo "[WARN] pre-commit install failed in $repo"
    echo "[INSTALL] pre-commit configured at $repo"
  fi
done

# ---------- git init ----------
for repo in "$DJANGO" "$ML"; do
  if [[ ! -d "$repo/.git" ]]; then
    git -C "$repo" init
    git -C "$repo" config user.name "$GIT_NAME"
    git -C "$repo" config user.email "$GIT_EMAIL"
    echo "[devmeta] git initialized at $repo"
  else
    echo "[devmeta] git exists at $repo"
  fi
done

# ---------- devmeta CLI ----------
cat > "$DEVMETA" <<'DM'
#!/usr/bin/env bash
set -euo pipefail
METAROOT="$HOME/.devmeta"
DJANGO="$HOME/DevWorkspaces/DjangoService"
ML="$HOME/DevWorkspaces/ModelBuilding"
case "${1:-help}" in
  sync-approve) bash "$METAROOT/sync-approve.sh" ;;
  list-conflicts) if [[ -f "$METAROOT/conflicts/conflicts.txt" ]]; then nl -ba "$METAROOT/conflicts/conflicts.txt"; else echo "No conflicts."; fi ;;
  docker-login) if command -v pass >/dev/null 2>&1; then DOCKER_USER=$(pass show devmeta/docker/username 2>/dev/null || echo ""); DOCKER_PASS=$(pass show devmeta/docker/token 2>/dev/null || echo ""); if [[ -n "$DOCKER_USER" && -n "$DOCKER_PASS" ]]; then echo "$DOCKER_PASS" | docker login --username "$DOCKER_USER" --password-stdin; else echo "Docker creds not in pass"; fi; else echo "pass not available"; fi ;;
  backup-local) ws="$2"; if [[ "$ws" == "django" ]]; then src="$DJANGO"; elif [[ "$ws" == "ml" ]]; then src="$ML"; else echo "Usage: devmeta backup-local <django|ml>"; exit 2; fi; outdir="$HOME/DevWorkspaces/backups"; mkdir -p "$outdir"; name="$(basename "$src")_$(date +%Y%m%d_%H%M).7z"; if command -v 7z >/dev/null 2>&1; then 7z a -t7z -mx=9 -m0=lzma2 -mmt=on "$outdir/$name" "$src"; else tar -czf "$outdir/$name.tar.gz" -C "$(dirname "$src")" "$(basename "$src")"; fi; echo "Backup: $outdir/$name"; ;;
  help|*) cat <<U
devmeta - helper
Commands:
  sync-approve       : interactively resolve sync conflicts
  list-conflicts     : list pending conflicts
  docker-login       : docker login using pass stored creds
  backup-local <ws>  : backup django|ml
  help
U
;;
esac
DM
chmod +x "$DEVMETA"
echo "[INSTALL] wrote devmeta CLI: $DEVMETA"

# ---------- vindash ----------
cat > "$VINDASH" <<'VD'
#!/usr/bin/env bash
set -euo pipefail
DEVMETA="$HOME/.local/bin/devmeta"
echo "Vindash — Unified Dev Dashboard (Office: manojm@indusvision.ai - IV033)"
PS3="Choose: "
options=("Open Django (code .)" "Open ML (code .)" "List conflicts" "Resolve conflicts" "Backup local" "Docker login (pass)" "Exit")
select opt in "${options[@]}"; do
  case $REPLY in
    1) cd "$HOME/DevWorkspaces/DjangoService"; command -v code >/dev/null 2>&1 && code . || pwd; break;;
    2) cd "$HOME/DevWorkspaces/ModelBuilding"; command -v code >/dev/null 2>&1 && code . || pwd; break;;
    3) $DEVMETA list-conflicts; break;;
    4) $DEVMETA sync-approve; break;;
    5) read -p "Which (django|ml): " w; $DEVMETA backup-local "$w"; break;;
    6) $DEVMETA docker-login; break;;
    7) exit 0;;
    *) echo "Invalid";;
  esac
done
VD
chmod +x "$VINDASH"
echo "[INSTALL] wrote vindash: $VINDASH"

# ---------- PATH ----------
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.profile"
  export PATH="$HOME/.local/bin:$PATH"
fi

echo
echo "=== COMPLETE ==="
echo "Run: 'systemctl --user status devmeta-sync' to check service (if systemd enabled)."
echo "Start dashboard: vindash"
echo "Resolve conflicts: devmeta sync-approve"
echo "Git identity: $GIT_NAME <$GIT_EMAIL>"
echo "Logs: $LOGDIR"
