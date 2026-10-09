"""Check the installable artifact rather than its source manifest."""

import json
import sys
import zipfile
from pathlib import Path

with zipfile.ZipFile(sys.argv[1]) as package:
    names = set(package.namelist())
    manifest = json.loads(package.read("extension/package.json"))
    required = {
        "extension/" + manifest["main"].removeprefix("./"),
        "extension/" + manifest["icon"],
        "extension/snippets/raw-cfn-resources-output.json",
    }
    required.update(
        "extension/" + snippet["path"].removeprefix("./")
        for snippet in manifest["contributes"]["snippets"]
    )
    required.update(
        f"extension/node_modules/{dependency}/package.json"
        for dependency in manifest.get("dependencies", {})
    )
    if missing := required - names:
        raise ValueError(f"Missing runtime files: {sorted(missing)}")
    if extras := [
        name
        for name in names
        if name.endswith(".gif")
        or name.startswith(("extension/tests/", "extension/specification/"))
    ]:
        raise ValueError(f"Non-runtime files in package: {extras}")
    report = {
        "files": len(names),
        "compressed_bytes": Path(sys.argv[1]).stat().st_size,
        "uncompressed_bytes": sum(info.file_size for info in package.infolist()),
        "runtime_complete": True,
    }
    Path(".vscode-test/package-report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report))
