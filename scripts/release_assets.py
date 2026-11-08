"""Preserve immutable release assets and verify safe publication retries.

Only invoked after CI succeeds. All network activity lives in main() so digest
and release identity checks can be exercised without credentials or publishing.
"""

import hashlib
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

from release_checks import validate_version


def digest(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def check_pypi_files(files, existing):
    hashes = {file.name: digest(file) for file in files}
    for artifact in existing:
        name = artifact["filename"]
        if name not in hashes or hashes[name] != artifact["digests"]["sha256"]:
            raise ValueError(f"PyPI already has a different artifact: {name}; use a new version")


def check_release(release, tag):
    if release["tag_name"] != tag or release["draft"] or release["prerelease"]:
        raise ValueError("Publishing requires a published stable GitHub release")


def gh(*args):
    return subprocess.check_output(["gh", *args], text=True)


def main():
    tag = os.environ["RELEASE_TAG"]
    version = os.environ["RELEASE_VERSION"]
    validate_version(tag, version, True)
    files = sorted(Path("dist").iterdir())
    if (
        len(files) != 2
        or not any(f.name.endswith(".whl") for f in files)
        or not any(f.name.endswith(".tar.gz") for f in files)
    ):
        raise ValueError("Expected exactly the tested wheel and source distribution")

    url = f"https://pypi.org/pypi/beancount-reds-importers/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            existing = json.load(response)["urls"]
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        existing = []
    check_pypi_files(files, existing)

    repository = os.environ["GITHUB_REPOSITORY"]
    release = json.loads(gh("api", f"repos/{repository}/releases/tags/{tag}"))
    check_release(release, tag)
    checksums = Path("SHA256SUMS")
    checksums.write_text("".join(f"{digest(file)}  {file.name}\n" for file in files))
    assets = {asset["name"] for asset in release["assets"]}
    for file in [*files, checksums]:
        if file.name in assets:
            with tempfile.TemporaryDirectory() as directory:
                gh(
                    "release",
                    "download",
                    tag,
                    "--repo",
                    repository,
                    "--pattern",
                    file.name,
                    "--dir",
                    directory,
                )
                if digest(Path(directory) / file.name) != digest(file):
                    raise ValueError(
                        f"GitHub release already has a different artifact: {file.name}"
                    )
        else:
            gh("release", "upload", tag, str(file), "--repo", repository)
    print("Release assets preserved; any existing PyPI files have identical hashes.")


if __name__ == "__main__":
    main()
