"""Release identity and retry checks must fail before any upload occurs."""

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest


def load_script(name):
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


release_checks = load_script("release_checks")
release_assets = load_script("release_assets")


@pytest.mark.parametrize(
    "tag,version,publish",
    [
        ("1.0.0", "1.0.0", True),
        ("1.2.3", "1.2.3", False),
        ("", "1.0.0.dev0", False),
    ],
)
def test_allowed_release_identities(tag, version, publish):
    release_checks.validate_version(tag, version, publish)


@pytest.mark.parametrize(
    "tag,version,publish",
    [
        ("", "1.0.0", True),
        ("1.0.0", "1.0.1", True),
        ("1.0.0rc1", "1.0.0rc1", True),
        ("v1.0.0", "1.0.0", True),
        ("01.0.0", "01.0.0", True),
        ("main", "1.0.0", True),
        ("1.0.0\nsha=bad", "1.0.0", True),
    ],
)
def test_invalid_release_identities(tag, version, publish):
    with pytest.raises(ValueError):
        release_checks.validate_version(tag, version, publish)


def test_tag_must_match_checkout_and_belong_to_main(monkeypatch):
    monkeypatch.setattr(
        release_checks, "git", lambda *args: "head" if args[-1] == "HEAD" else "tag"
    )
    with pytest.raises(ValueError, match="exact tagged commit"):
        release_checks.validate_checkout("1.0.0")
    monkeypatch.setattr(release_checks, "git", lambda *args: "same-sha")

    def reject_ancestor(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0])

    monkeypatch.setattr(release_checks.subprocess, "run", reject_ancestor)
    with pytest.raises(subprocess.CalledProcessError):
        release_checks.validate_checkout("1.0.0")


def test_publication_retry_accepts_only_identical_files(tmp_path):
    file = tmp_path / "package.whl"
    file.write_bytes(b"tested artifact")
    record = {"filename": file.name, "digests": {"sha256": release_assets.digest(file)}}
    release_assets.check_pypi_files([file], [])
    release_assets.check_pypi_files([file], [record])
    file.write_bytes(b"different artifact")
    with pytest.raises(ValueError, match="different artifact"):
        release_assets.check_pypi_files([file], [record])
    with pytest.raises(ValueError):
        release_assets.check_pypi_files([], [record])


@pytest.mark.parametrize("draft,prerelease", [(True, False), (False, True)])
def test_draft_and_prerelease_cannot_publish(draft, prerelease):
    with pytest.raises(ValueError):
        release_assets.check_release(
            {"tag_name": "1.0.0", "draft": draft, "prerelease": prerelease}, "1.0.0"
        )


def test_release_ancestry_with_real_git_repository(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def git(*args):
        return subprocess.check_output(["git", *args], text=True).strip()

    git("init", "--initial-branch=main")
    git(
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.org",
        "commit",
        "--allow-empty",
        "-m",
        "test: initial fixture",
    )
    sha = git("rev-parse", "HEAD")
    git("tag", "1.0.0")
    git("update-ref", "refs/remotes/origin/main", sha)
    assert release_checks.validate_checkout("1.0.0") == sha
    git(
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.org",
        "commit",
        "--allow-empty",
        "-m",
        "test: unmerged fixture",
    )
    git("tag", "1.1.0")
    with pytest.raises(subprocess.CalledProcessError):
        release_checks.validate_checkout("1.1.0")


@pytest.mark.parametrize("retry", [False, True])
def test_preserve_release_assets_without_publishing(tmp_path, monkeypatch, retry):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("RELEASE_TAG", "1.0.0")
    monkeypatch.setenv("RELEASE_VERSION", "1.0.0")
    monkeypatch.setenv("GITHUB_REPOSITORY", "example/repo")
    dist = tmp_path / "dist"
    dist.mkdir()
    wheel = dist / "package-1.0.0-py3-none-any.whl"
    source = dist / "package-1.0.0.tar.gz"
    wheel.write_bytes(b"wheel")
    source.write_bytes(b"source")
    files = sorted([wheel, source])
    existing = (
        [{"filename": f.name, "digests": {"sha256": release_assets.digest(f)}} for f in files]
        if retry
        else []
    )
    monkeypatch.setattr(
        release_assets.urllib.request,
        "urlopen",
        lambda *a, **kw: io.BytesIO(json.dumps({"urls": existing}).encode()),
    )
    release = {
        "tag_name": "1.0.0",
        "draft": False,
        "prerelease": False,
        "assets": [{"name": f.name} for f in files] if retry else [],
    }
    calls = []

    def gh(*args):
        calls.append(args)
        if args[0] == "api":
            return json.dumps(release)
        if args[1] == "download":
            name = args[args.index("--pattern") + 1]
            directory = Path(args[args.index("--dir") + 1])
            (directory / name).write_bytes((dist / name).read_bytes())
        return ""

    monkeypatch.setattr(release_assets, "gh", gh)
    release_assets.main()
    assert (tmp_path / "SHA256SUMS").read_text() == "".join(
        f"{release_assets.digest(f)}  {f.name}\n" for f in files
    )
    uploads = [c for c in calls if c[:2] == ("release", "upload")]
    assert len(uploads) == (1 if retry else 3)
