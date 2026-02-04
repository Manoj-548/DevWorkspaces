#!/usr/bin/env bash
set -euo pipefail

echo "=== DevDashboard Build Script ==="
echo "Running office_setup.sh..."

# Run with piped inputs for non-interactive setup
echo -e "Y\nY\nY\nY\nY\nY\nY\nskip\nY\nskip\nN" | bash office_setup.sh

echo "Setup complete. Dashboard is ready."

# Optionally open the dashboard
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open dashboard.html
else
  echo "Dashboard HTML file is ready. Open dashboard.html manually."
fi
