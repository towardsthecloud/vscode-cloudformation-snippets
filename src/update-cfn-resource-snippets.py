#!/usr/bin/env python3
"""Generate resource snippets from a local or downloaded AWS specification."""

import argparse
from pathlib import Path

from cfn_generator import build_snippets
from cfn_spec import load_spec, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", dest="local_path")
    parser.add_argument("--format", choices=["json", "yaml"], default="yaml")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or (
        Path(".vscode-test") / f"{args.format}-cfn-resource-types-test-output.json"
        if args.local_path
        else Path("snippets") / f"{args.format}-cfn-resource-types.json"
    )
    snippets = build_snippets(load_spec(args.local_path), args.format)
    write_json(output, snippets)
    print(f"Generated {len(snippets)} {args.format} snippets: {output}")


if __name__ == "__main__":
    main()
