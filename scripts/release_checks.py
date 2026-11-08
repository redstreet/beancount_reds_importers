"""Fail closed before testing/publishing an existing stable release tag."""

import os
import re
import subprocess
import tomllib
from pathlib import Path


def validate_version(tag, version, publish):
    if publish and not tag:
        raise ValueError("Publishing requires an existing stable release tag")
    if tag and not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", tag):
        raise ValueError("Use a stable numeric tag such as 1.0.0")
    if tag and tag != version:
        raise ValueError(f"Tag {tag} does not match package version {version}")


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def validate_checkout(tag):
    sha = git("rev-parse", "HEAD")
    if tag and git("rev-parse", f"refs/tags/{tag}^{{commit}}") != sha:
        raise ValueError("The checkout must be the exact tagged commit")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", sha, "refs/remotes/origin/main"], check=True
    )
    return sha


def main():
    tag = os.environ.get("RELEASE_TAG", "")
    publish = os.environ.get("PUBLISH", "false").lower() == "true"
    version = tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"]
    validate_version(tag, version, publish)
    sha = validate_checkout(tag)
    outputs = {"sha": sha, "tag": tag, "version": version, "publish": str(publish).lower()}
    print(f"Validated {'publication' if publish else 'dry run'}: {version} at {sha}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            for key, value in outputs.items():
                output.write(f"{key}={value}\n")


if __name__ == "__main__":
    main()
