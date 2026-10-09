"""Preserve AWS resource and nested property documentation links."""

import argparse
from pathlib import Path

from cfn_generator import build_documentation
from cfn_spec import load_spec, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", dest="local_path")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or (
        Path(".vscode-test/raw-cfn-resources-test-output.json")
        if args.local_path
        else Path("snippets/raw-cfn-resources-output.json")
    )
    documentation = build_documentation(load_spec(args.local_path))
    write_json(output, documentation)
    print(
        f"Generated documentation for {len(documentation['Resources'])} resources: {output}"
    )


if __name__ == "__main__":
    main()
