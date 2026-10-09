"""Validate checked-in or staged snippets against their AWS specification snapshot."""

import argparse
import json
from pathlib import Path

from cfn_spec import load_spec
from validate_snippets import validate_artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--directory", default=Path("snippets"), type=Path)
    args = parser.parse_args()
    names = [
        "json-cfn-resource-types.json",
        "yaml-cfn-resource-types.json",
        "raw-cfn-resources-output.json",
    ]
    artifacts = {
        name: json.loads((args.directory / name).read_text()) for name in names
    }
    spec = load_spec(args.spec)
    validate_artifacts(spec, artifacts)
    print(
        f"Validated {len(spec['ResourceTypes'])} resources in JSON, YAML and documentation"
    )


if __name__ == "__main__":
    main()
