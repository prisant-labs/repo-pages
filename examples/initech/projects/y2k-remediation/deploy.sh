#!/usr/bin/env bash
# Deploy one Y2K fix to one client. Usage: ./deploy.sh <client> <module>
# Prints the steps instead of running them unless DRY_RUN=0.
set -euo pipefail

client="${1:?client name, e.g. first-mutual}"
module="${2:?module name, e.g. interest-calc}"
dry_run="${DRY_RUN:-1}"

run() {
  if [ "$dry_run" = "1" ]; then echo "would run: $*"; else "$@"; fi
}

echo "Deploying $module to $client"
run python3 -m unittest test_date_window
run scp "build/$module.tar" "deploy@$client.example.com:/opt/releases/"
run ssh "deploy@$client.example.com" "cd /opt/releases && ./install $module"
echo "Done. Remember the TPS report. With the new cover sheet."
