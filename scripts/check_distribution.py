"""Validate and install both release artifacts without importing the checkout.

Usage: python scripts/check_distribution.py dist
Requires uv on PATH. Temporary environments resolve runtime dependencies as pip users do.
"""

import email
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path


def check_distribution(dist):
    root = Path(__file__).resolve().parents[1]
    expected = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    wheels = list(dist.glob("*.whl"))
    sources = list(dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sources) != 1:
        raise ValueError("Expected exactly one wheel and one source distribution")
    with zipfile.ZipFile(wheels[0]) as archive:
        metadata_file = next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))
        metadata = email.message_from_bytes(archive.read(metadata_file))
        assert metadata["Version"] == expected
        assert metadata["Name"].replace("-", "_") == "beancount_reds_importers"
        assert "beancount_reds_importers/util/template.cfg" in archive.namelist()
        assert any("LICENSE" in n for n in archive.namelist())
        assert not any("/tests/" in n for n in archive.namelist())
    with tarfile.open(sources[0]) as archive:
        names = archive.getnames()
        prefix = names[0].split("/")[0] + "/"
        for required in (
            "pyproject.toml",
            "README.md",
            "LICENSE",
            "conftest.py",
            "uv.lock",
            "tests/test_readers.py",
            "tests/distribution/smoke.py",
        ):
            assert prefix + required in names, f"Missing from source distribution: {required}"
        assert any(n.endswith(".qfx.extract") for n in names)
        assert any(n.endswith(".pdf") for n in names)
        metadata = email.message_from_bytes(archive.extractfile(prefix + "PKG-INFO").read())
        assert metadata["Version"] == expected

    env = dict(os.environ, PYTHONNOUSERSITE="1")
    env.pop("PYTHONPATH", None)
    for artifact in (wheels[0], sources[0]):
        with tempfile.TemporaryDirectory(prefix="reds-package-") as directory:
            work = Path(directory)
            venv = work / "venv"
            subprocess.run(
                ["uv", "venv", "--python", sys.executable, str(venv)], check=True, env=env
            )
            python = venv / "bin/python"
            subprocess.run(
                ["uv", "pip", "install", "--python", str(python), str(artifact.resolve())],
                check=True,
                cwd=work,
                env=env,
            )
            subprocess.run(["uv", "pip", "check", "--python", str(python)], check=True, env=env)
            for file in (root / "tests/distribution").glob("*.py"):
                shutil.copy(file, work)
            subprocess.run([str(python), "smoke.py", expected], check=True, cwd=work, env=env)


if __name__ == "__main__":
    check_distribution(Path(sys.argv[1] if len(sys.argv) > 1 else "dist"))
