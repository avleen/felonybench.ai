#!/usr/bin/env bash
# Everything CI checks. Run it before pushing.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m pytest -q
python3 -m scripts.validate

cd site
npm ci
npm test
npm run build
cd ..

python3 -m scripts.check_site
echo "All checks passed."
