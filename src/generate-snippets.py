"""Generate and validate all artifacts from one immutable specification snapshot."""

import argparse
from pathlib import Path

from cfn_generator import build_documentation, build_snippets
from cfn_spec import load_spec, write_json
from validate_snippets import validate_artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output", default=Path("snippets"), type=Path)
    args = parser.parse_args()
    spec = load_spec(args.spec)
    artifacts = {
        f"{format_name}-cfn-resource-types.json": build_snippets(spec, format_name)
        for format_name in ["json", "yaml"]
    }
    artifacts["raw-cfn-resources-output.json"] = build_documentation(spec)
    validate_artifacts(spec, artifacts)
    for name, artifact in artifacts.items():
        write_json(args.output / name, artifact)
    print(
        f"Generated and validated {len(spec['ResourceTypes'])} resources in JSON, YAML and documentation"
    )


if __name__ == "__main__":
    main()
