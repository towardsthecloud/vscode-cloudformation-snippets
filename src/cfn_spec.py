"""Read one specification snapshot and write complete artifacts atomically."""

import gzip
import json
import os
import tempfile
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SPEC_URL = "https://d1uauaxba7bl26.cloudfront.net/latest/gzip/CloudFormationResourceSpecification.json"


def download_spec():
    with requests.Session() as session:
        session.mount(
            "https://",
            HTTPAdapter(
                max_retries=Retry(
                    total=3,
                    backoff_factor=1,
                    status_forcelist=[429, 500, 502, 503, 504],
                )
            ),
        )
        response = session.get(SPEC_URL, timeout=(10, 60))
        response.raise_for_status()
        validate_spec(response.json())
        return response.content


def validate_spec(spec):
    if not isinstance(spec.get("ResourceTypes"), dict) or not spec["ResourceTypes"]:
        raise ValueError("The specification must contain resource types")
    if not isinstance(spec.get("PropertyTypes"), dict):
        raise TypeError("The specification must contain property types")


def load_spec(local_path=None):
    content = Path(local_path).read_bytes() if local_path else download_spec()
    if local_path and str(local_path).endswith(".gz"):
        content = gzip.decompress(content)
    spec = json.loads(content)
    validate_spec(spec)
    return spec


def write_json(destination, value):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", dir=destination.parent, delete=False, encoding="utf-8"
    ) as file:
        temporary = Path(file.name)
        try:
            json.dump(value, file, sort_keys=True, indent=2)
            file.write("\n")
            file.close()
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
