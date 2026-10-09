"""Run Extension Host regressions against the exact installable VSIX."""

import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(
    prefix="package-", dir=repo / ".vscode-test"
) as directory:
    root = Path(directory).resolve()
    with zipfile.ZipFile(sys.argv[1]) as package:
        for entry in package.infolist():
            if not entry.filename.startswith("extension/") or entry.is_dir():
                continue
            destination = (root / entry.filename).resolve()
            if not destination.is_relative_to(root):
                raise ValueError("Archive entry escapes the package directory")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(package.read(entry))
    subprocess.run(
        ["node", str(repo / "tests/run-extension-tests.cjs")],
        env={**os.environ, "VSCODE_EXTENSION_ROOT": str(root / "extension")},
        cwd=repo,
        check=True,
    )
