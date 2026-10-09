"""Generate typed snippet trees, then render JSON and YAML from the same values."""

import json
from dataclasses import dataclass

MAX_DEPTH = 10
MAX_LINES = 400


@dataclass(frozen=True)
class Placeholder:
    text: str
    quoted: bool = False


class ResourceParser:
    def __init__(self, spec, resource, max_depth):
        self.spec = spec
        self.resource = resource
        self.max_depth = max_depth
        self.counter = 1

    def placeholder(self, default, quoted=False):
        self.counter += 1
        escaped = default.replace("}", "\\}")
        return Placeholder(f"${{{self.counter}:{escaped}}}", quoted)

    def value(self, info, depth=0, ancestors=()):
        primitive = info.get("PrimitiveType")
        if primitive:
            if primitive in {"Integer", "Long", "Double"}:
                return self.placeholder("0")
            if primitive == "Boolean":
                self.counter += 1
                return Placeholder(f"${{{self.counter}|false,true|}}")
            if primitive == "Json":
                return self.placeholder("{}")
            if primitive in {"String", "Timestamp"}:
                return self.placeholder(primitive, quoted=True)
            raise ValueError(f"Unsupported primitive type: {primitive}")
        kind = info.get("Type")
        if kind in {"List", "Map"}:
            item = (
                {"PrimitiveType": info["PrimitiveItemType"]}
                if "PrimitiveItemType" in info
                else {"Type": info["ItemType"]}
            )
            if kind == "List":
                return [self.value(item, depth, ancestors)]
            key = self.placeholder("Key", quoted=True).text
            return {key: self.value(item, depth, ancestors)}
        name = kind if kind and "::" in kind else f"{self.resource}.{kind}"
        if name in ancestors or depth >= self.max_depth:
            return self.placeholder("{}")
        properties = self.spec["PropertyTypes"].get(name)
        if properties is None and kind == "Tag":
            properties = self.spec["PropertyTypes"].get("Tag")
        if properties is None:
            raise ValueError(f"Unknown property type: {name}")
        return {
            key: self.value(value, depth + 1, (*ancestors, name))
            for key, value in sorted(properties.get("Properties", {}).items())
        }


def scalar(value):
    if isinstance(value, Placeholder):
        return json.dumps(value.text) if value.quoted else value.text
    return json.dumps(value)


def render_json(value, indent=0):
    if isinstance(value, dict) and value:
        entries = [
            " " * (indent + 2) + json.dumps(key) + ": " + render_json(item, indent + 2)
            for key, item in value.items()
        ]
        return "{\n" + ",\n".join(entries) + "\n" + " " * indent + "}"
    if isinstance(value, list) and value:
        return (
            "[\n"
            + ",\n".join(
                " " * (indent + 2) + render_json(item, indent + 2) for item in value
            )
            + "\n"
            + " " * indent
            + "]"
        )
    return scalar(value)


def render_yaml(value, indent=0):
    lines = []
    entries = (
        value.items() if isinstance(value, dict) else [(None, item) for item in value]
    )
    for key, item in entries:
        prefix = " " * indent + (f"{key}:" if key is not None else "-")
        if isinstance(item, (dict, list)) and item:
            lines.append(prefix)
            lines.extend(render_yaml(item, indent + 2))
        else:
            lines.append(prefix + " " + scalar(item))
    return lines


def build_snippets(spec, output_format):
    output = {}
    for name, resource in sorted(spec["ResourceTypes"].items()):
        for max_depth in range(MAX_DEPTH, -1, -1):
            parser = ResourceParser(spec, name, max_depth)
            tree = {
                "${1:LogicalID}": {
                    "Type": name,
                    "Properties": {
                        key: parser.value(info)
                        for key, info in sorted(resource.get("Properties", {}).items())
                    },
                }
            }
            if output_format == "json":
                # A resource snippet is a member of the enclosing Resources object.
                body = [line[2:] for line in render_json(tree).splitlines()[1:-1]]
            else:
                body = render_yaml(tree)
                required = {
                    key
                    for key, info in resource.get("Properties", {}).items()
                    if info.get("Required")
                }
                body = [
                    line + " # Required"
                    if line.startswith("    ")
                    and not line.startswith("     ")
                    and line.strip().split(":", 1)[0] in required
                    else line
                    for line in body
                ]
            if len(body) <= MAX_LINES:
                break
        else:
            raise ValueError(f"{name} cannot fit within {MAX_LINES} lines")
        description = [resource["Documentation"].replace("http://", "https://")]
        if resource.get("Attributes"):
            description.append(
                "Attributes:\n"
                + "\n".join(f"  {key}" for key in sorted(resource["Attributes"]))
            )
        output[name] = {
            "body": body,
            "description": description,
            "prefix": name.removeprefix("AWS::").replace("::", "-").lower(),
            "scope": output_format,
        }
    return output


def build_documentation(spec):
    def properties(owner, values):
        output = {}
        for key, info in values.items():
            entry = {"Docs": info["Documentation"].replace("http://", "https://")}
            if info.get("Type") in {"List", "Map"}:
                entry["Container"] = info["Type"]
            kind = info.get("ItemType", info.get("Type"))
            if kind and kind not in {"List", "Map"}:
                entry["Type"] = (
                    kind if "::" in kind or kind == "Tag" else f"{owner}.{kind}"
                )
            output[key] = entry
        return output

    resources = {
        name: {
            "Docs": data["Documentation"].replace("http://", "https://"),
            "Properties": properties(name, data.get("Properties", {})),
        }
        for name, data in spec["ResourceTypes"].items()
    }
    nested = {
        name: {
            "Properties": properties(name.split(".", 1)[0], data.get("Properties", {}))
        }
        for name, data in spec["PropertyTypes"].items()
    }
    return {"Resources": resources, "PropertyTypes": nested}
