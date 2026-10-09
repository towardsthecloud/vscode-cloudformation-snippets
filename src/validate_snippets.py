"""Validate expanded artifacts against the independently supplied AWS specification."""

import json
import re

import yaml


def expand_defaults(body):
    text = "\n".join(body)
    text = re.sub(r"\$\{\d+\|([^}]+)\|\}", lambda match: match[1].split(",")[0], text)
    return re.sub(
        r"\$\{\d+(?::((?:\\.|[^\\}])*))?\}",
        lambda match: re.sub(r"\\([\\}$])", r"\1", match[1] or ""),
        text,
    )


def check_value(value, info, owner, spec):
    primitive = info.get("PrimitiveType")
    if primitive:
        if primitive in {"Integer", "Long", "Double"}:
            valid = type(value) in {int, float}
        elif primitive == "Boolean":
            valid = isinstance(value, bool)
        elif primitive in {"String", "Timestamp"}:
            valid = isinstance(value, str)
        else:
            valid = primitive == "Json"
        if not valid:
            raise ValueError(f"Expected {primitive}, received {value!r}")
        return
    kind = info["Type"]
    if kind in {"List", "Map"}:
        if not isinstance(value, list if kind == "List" else dict):
            raise ValueError(f"Expected {kind}")
        item = (
            {"PrimitiveType": info["PrimitiveItemType"]}
            if "PrimitiveItemType" in info
            else {"Type": info["ItemType"]}
        )
        for child in value if kind == "List" else value.values():
            check_value(child, item, owner, spec)
        return
    if not isinstance(value, dict):
        raise TypeError(f"Expected an object for {kind}")
    # Empty editable objects terminate recursive or size-limited expansion.
    if not value:
        return
    name = kind if "::" in kind or kind == "Tag" else f"{owner}.{kind}"
    expected = spec["PropertyTypes"][name].get("Properties", {})
    if set(value) != set(expected):
        raise ValueError(f"Incomplete properties for {name}")
    for key, child in value.items():
        check_value(child, expected[key], owner, spec)


def validate_artifacts(spec, artifacts):
    expected = spec["ResourceTypes"]
    for output_format in ["json", "yaml"]:
        snippets = artifacts[f"{output_format}-cfn-resource-types.json"]
        if set(snippets) != set(expected):
            raise ValueError(f"Incomplete {output_format} resource coverage")
        for name, snippet in snippets.items():
            if not snippet["body"] or len(snippet["body"]) > 400:
                raise ValueError(f"Invalid snippet size: {name}")
            text = expand_defaults(snippet["body"])
            inserted = (
                json.loads("{" + text + "}")
                if output_format == "json"
                else yaml.safe_load(text)
            )
            resource = inserted["LogicalID"]
            if resource["Type"] != name or set(resource["Properties"]) != set(
                expected[name].get("Properties", {})
            ):
                raise ValueError(f"Incorrect resource properties: {name}")
            for key, value in resource["Properties"].items():
                try:
                    check_value(value, expected[name]["Properties"][key], name, spec)
                except (KeyError, TypeError, ValueError) as error:
                    raise ValueError(
                        f"{output_format} {name}.{key}: {error}"
                    ) from error
    documentation = artifacts["raw-cfn-resources-output.json"]
    if set(documentation["Resources"]) != set(expected) or set(
        documentation["PropertyTypes"]
    ) != set(spec["PropertyTypes"]):
        raise ValueError("Incomplete documentation coverage")
    for section, source in [
        ("Resources", expected),
        ("PropertyTypes", spec["PropertyTypes"]),
    ]:
        for name, data in source.items():
            actual = documentation[section][name]
            if section == "Resources" and actual["Docs"] != data[
                "Documentation"
            ].replace("http://", "https://"):
                raise ValueError(f"Incorrect resource documentation: {name}")
            if set(actual["Properties"]) != set(data.get("Properties", {})):
                raise ValueError(f"Incomplete property documentation: {name}")
            for key, info in data.get("Properties", {}).items():
                if actual["Properties"][key]["Docs"] != info["Documentation"].replace(
                    "http://", "https://"
                ):
                    raise ValueError(f"Incorrect property documentation: {name}.{key}")
