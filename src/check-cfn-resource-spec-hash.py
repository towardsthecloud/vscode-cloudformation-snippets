#!/usr/bin/env python3
"""Download a specification snapshot without advancing the released hash."""

import argparse
import hashlib
import json
import os
from pathlib import Path

from cfn_spec import download_spec, validate_spec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=Path(".vscode-test/resource-specification.json"),
    )
    parser.add_argument(
        "--hash-file", type=Path, default=Path("src/current-cfn-spec-hash")
    )
    parser.add_argument("--local", type=Path)
    args = parser.parse_args()
    content = args.local.read_bytes() if args.local else download_spec()
    validate_spec(json.loads(content))
    digest = hashlib.sha256(content).hexdigest()
    updated = (
        not args.hash_file.exists() or digest != args.hash_file.read_text().strip()
    )
    args.snapshot.parent.mkdir(parents=True, exist_ok=True)
    args.snapshot.write_bytes(content)
    if output := os.environ.get("GITHUB_OUTPUT"):
        with Path(output).open("a") as file:
            file.write(f"spec_updated={str(updated).lower()}\n")
    print(f"Specification {'updated' if updated else 'unchanged'}: {digest}")


if __name__ == "__main__":
    main()
