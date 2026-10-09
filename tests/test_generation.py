import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def expand_defaults(body):
    text = "\n".join(body)
    text = re.sub(r"\$\{\d+\|([^}]+)\|\}", lambda m: m[1].split(",")[0], text)
    return re.sub(
        r"\$\{\d+(?::((?:\\.|[^\\}])*))?\}",
        lambda m: re.sub(r"\\([\\}$])", r"\1", m[1] or ""),
        text,
    )


class GeneratorTests(unittest.TestCase):
    def test_snapshot_check_reports_changes_without_advancing_released_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "spec.json"
            content = json.dumps(
                {"ResourceTypes": {"AWS::Example::Resource": {}}, "PropertyTypes": {}}
            ).encode()
            fixture.write_bytes(content)
            digest = hashlib.sha256(content).hexdigest()
            released = Path(directory) / "released-hash"
            output = Path(directory) / "github-output"
            snapshot = Path(directory) / "snapshot.json"
            for previous, expected in [("previous", "true"), (digest, "false")]:
                with self.subTest(changed=expected):
                    released.write_text(previous)
                    output.write_text("")
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(REPO / "src/check-cfn-resource-spec-hash.py"),
                            "--local",
                            str(fixture),
                            "--snapshot",
                            str(snapshot),
                            "--hash-file",
                            str(released),
                        ],
                        env={**os.environ, "GITHUB_OUTPUT": str(output)},
                        cwd=directory,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(output.read_text(), f"spec_updated={expected}\n")
                    self.assertEqual(snapshot.read_bytes(), content)
                    self.assertEqual(released.read_text(), previous)
            fixture.write_text('{"ResourceTypes": {}, "PropertyTypes": {}}')
            output.write_text("")
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO / "src/check-cfn-resource-spec-hash.py"),
                    "--local",
                    str(fixture),
                    "--snapshot",
                    str(snapshot),
                    "--hash-file",
                    str(released),
                ],
                env={**os.environ, "GITHUB_OUTPUT": str(output)},
                cwd=directory,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_text(), "")
            self.assertEqual(snapshot.read_bytes(), content)
            self.assertEqual(released.read_text(), digest)

    def test_full_snapshot_pipeline_rejects_incomplete_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot = REPO / "specification/resource-specification.json.gz"
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO / "src/generate-snippets.py"),
                    "--spec",
                    str(snapshot),
                    "--output",
                    directory,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            command = [
                sys.executable,
                str(REPO / "src/validate-snippets.py"),
                "--spec",
                str(snapshot),
                "--directory",
                directory,
            ]
            result = subprocess.run(
                command, capture_output=True, text=True, check=False
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            artifact = Path(directory) / "json-cfn-resource-types.json"
            snippets = json.loads(artifact.read_text())
            del snippets["AWS::Lambda::Function"]
            artifact.write_text(json.dumps(snippets))
            result = subprocess.run(
                command, capture_output=True, text=True, check=False
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Incomplete json resource coverage", result.stderr)

    def test_required_numbers_maps_and_recursive_objects_have_valid_defaults(self):
        spec = {
            "ResourceTypes": {
                "AWS::Example::Resource": {
                    "Documentation": "https://docs.aws.amazon.com/example-resource.html",
                    "Properties": {
                        "Count": {"PrimitiveType": "Integer", "Required": True},
                        "Settings": {"Type": "Map", "PrimitiveItemType": "Boolean"},
                        "Node": {"Type": "Node"},
                    },
                },
            },
            "PropertyTypes": {
                "AWS::Example::Resource.Node": {
                    "Properties": {
                        "Child": {"Type": "Node"},
                        "Name": {"PrimitiveType": "String"},
                    },
                },
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "spec.json"
            fixture.write_text(json.dumps(spec))
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO / "src/update-cfn-resource-snippets.py"),
                    "--local",
                    str(fixture),
                    "--format",
                    "json",
                ],
                cwd=directory,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            snippets = json.loads(
                (
                    Path(directory)
                    / ".vscode-test/json-cfn-resource-types-test-output.json"
                ).read_text()
            )
            inserted = json.loads(
                "{" + expand_defaults(snippets["AWS::Example::Resource"]["body"]) + "}"
            )
            self.assertEqual(
                inserted["LogicalID"]["Properties"],
                {
                    "Count": 0,
                    "Node": {"Child": {}, "Name": "String"},
                    "Settings": {"Key": False},
                },
            )

    def test_bad_resource_does_not_replace_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "spec.json"
            fixture.write_text(
                json.dumps(
                    {"ResourceTypes": {"AWS::Example::Broken": {}}, "PropertyTypes": {}}
                )
            )
            output = (
                Path(directory)
                / ".vscode-test/json-cfn-resource-types-test-output.json"
            )
            output.parent.mkdir()
            output.write_text('{"existing": true}')
            for script, arguments, output_name in [
                ("update-cfn-resource-snippets.py", ["--format", "json"], output.name),
                (
                    "create-raw-cfn-resources-output.py",
                    [],
                    "raw-cfn-resources-test-output.json",
                ),
            ]:
                with self.subTest(script=script):
                    destination = output.parent / output_name
                    destination.write_text('{"existing": true}')
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(REPO / "src" / script),
                            "--local",
                            str(fixture),
                            *arguments,
                        ],
                        cwd=directory,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(
                        json.loads(destination.read_text()), {"existing": True}
                    )

    def test_json_primitive_lists_insert_as_arrays_of_scalars(self):
        spec = {
            "PropertyTypes": {},
            "ResourceTypes": {
                "AWS::Lambda::Function": {
                    "Documentation": "https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-lambda-function.html",
                    "Properties": {
                        "Architectures": {
                            "Type": "List",
                            "PrimitiveItemType": "String",
                        },
                    },
                },
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "spec.json"
            fixture.write_text(json.dumps(spec))
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO / "src/update-cfn-resource-snippets.py"),
                    "--local",
                    str(fixture),
                    "--format",
                    "json",
                ],
                cwd=directory,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            snippets = json.loads(
                (
                    Path(directory)
                    / ".vscode-test/json-cfn-resource-types-test-output.json"
                ).read_text()
            )
            inserted = json.loads(
                "{" + expand_defaults(snippets["AWS::Lambda::Function"]["body"]) + "}"
            )
            self.assertEqual(
                inserted["LogicalID"]["Properties"], {"Architectures": ["String"]}
            )


if __name__ == "__main__":
    unittest.main()
