#!/usr/bin/env bash
# Build a single-file Linux executable with PyInstaller.
# Run from the repository root or with `bash scripts/build_linux.sh` inside WSL.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Keep the Linux environment outside the project when the checkout is on a
# Windows drive mounted into WSL (uv cannot reliably replace a Windows venv).
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/.cache/abramyan-exam-venv}"

echo "==> Syncing Python environment ($UV_PROJECT_ENVIRONMENT)"
uv sync --extra dev

echo "==> Building sandbox helper"
rm -rf build/runner-dist build/runner-work build/spec
uv run pyinstaller \
  --clean --noconfirm --onefile \
  --name exam-runner \
  --paths . \
  --distpath build/runner-dist \
  --workpath build/runner-work \
  --specpath build/spec \
  app/sandbox_runner.py

echo "==> Building exam application"
rm -rf build/app-work build/app-spec dist
uv run pyinstaller \
  --clean --noconfirm --onefile \
  --name abramyan-exam \
  --paths . \
  --collect-submodules uvicorn \
  --collect-submodules anyio \
  --hidden-import python_multipart \
  --add-data "$ROOT/app/templates:app/templates" \
  --add-data "$ROOT/app/static:app/static" \
  --add-data "$ROOT/app/content/tasks.json:app/content" \
  --add-data "$ROOT/build/runner-dist/exam-runner:." \
  --distpath dist \
  --workpath build/app-work \
  --specpath build/app-spec \
  app/__main__.py

chmod +x dist/abramyan-exam
mkdir -p release
cp dist/abramyan-exam release/abramyan-exam-linux-x86_64
chmod +x release/abramyan-exam-linux-x86_64
(cd release && sha256sum abramyan-exam-linux-x86_64 > SHA256SUMS)
echo
echo "==> Built: $ROOT/release/abramyan-exam-linux-x86_64"
ls -lh release/abramyan-exam-linux-x86_64
echo "==> SHA256"
cat release/SHA256SUMS
