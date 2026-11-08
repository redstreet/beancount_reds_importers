# Releases

Pip is the primary distribution channel. Stable versions use immutable numeric tags
such as `1.0.0`. Beancount v3 releases start at 1.0.0; the historical 0.10.0 release
remains available for Beancount v2. Debian packaging is maintained downstream, using
the tagged source distribution and its included tests.

## Everyday workflow

1. Push your own Conventional Commits to `main`, or review and merge contributors'
   PRs. Direct pushes stay supported; no permanent `dev` branch is needed.
2. CI runs lint, formatting, offline tests across Python 3.11–3.15 on Linux, and
   clean-install tests for both distribution formats. Fix a failed direct push with
   another commit. Review passing checks before merging a PR.
3. After successful push CI on current `main`, Release Please opens or updates one
   release PR with the proposed version and changelog. Its workflow also updates
   `uv.lock`, then the PR receives normal CI. Superseded CI runs are ignored.
4. When ready to ship, inspect the release PR, add migration notes where needed,
   and merge it after its checks pass. This is the release decision; it is never
   automatically merged.
5. Release Please creates the tag and published GitHub release. Publishing rechecks
   the exact tagged commit, including its membership in `main` and package version.
   Only after all checks succeed are the tested artifacts attached to the release
   and uploaded to PyPI. A failed publication leaves the GitHub release visible;
   check the publishing workflow before announcing availability on PyPI.

`pyproject.toml` contains the authoritative package version. Development starts at
`1.0.0.dev0`; the automation's bootstrap commit has a `Release-As: 1.0.0` footer,
so the first release PR proposes `1.0.0`. That commit falls outside the changelog
range after 1.0.0 is released, and Conventional Commits determine subsequent versions.
No manual version or changelog editing is needed for normal releases. Preserve the
bootstrap footer if squashing these setup commits into a single commit.

The release workflow builds once with locked build tools and a commit-derived timestamp,
tests the artifacts, and passes those same files to the publishing job. Only that final
job has PyPI publishing permissions. CI never generates new expected test outputs.

## One-time account setup

Repository files alone cannot create the GitHub App or establish trust in the PyPI
owner's account. Complete these steps before enabling the release bot:

1. Create a GitHub App and install it on this repository only. Give it repository
   **Contents**, **Pull requests**, and **Issues** read/write permissions (Issues
   is used for release labels). Store its private key as the Actions secret
   `RELEASE_APP_PRIVATE_KEY`. Keep its App ID for the final step below.
   The [token action](https://github.com/actions/create-github-app-token) creates
   a short-lived installation token; the ordinary `GITHUB_TOKEN` would suppress
   CI events for bot-created PRs and releases.
2. Create the GitHub Actions environment **pypi**. Required environment reviewers
   are unnecessary for this process: merging the release PR is the approval.
   If restricting deployment branches/tags, allow `main` for manual retries and
   stable release tags for release events.
3. In the existing PyPI project's publishing settings, add a
   [trusted publisher](https://docs.pypi.org/trusted-publishers/adding-a-publisher/)
   for owner `redstreet`, repository `beancount_reds_importers`, workflow
   `pythonpublish.yml`, environment `pypi`. No PyPI API token is needed.
4. After pushing these changes, manually run **Publish Python package** on `main`
   with the tag empty and **publish unchecked**. All validation/build/test jobs
   must succeed and the publishing job must be skipped. Inspect the resulting
   `distributions` artifact. Also confirm ordinary `Python package` CI is green.
5. Set the repository Actions variable **RELEASE_APP_ID** to the App ID. This enables
   the bot; before it is set, the Release PR job is intentionally skipped. Run
   **Release PR** manually or push another change to start the first release PR.
6. Confirm that the bot's PR gets CI checks after its lockfile update. Merge it only
   when ready to publish 1.0.0. After a successful trusted publication, remove the
   old `PYPI_PASSWORD` secret if nothing else uses it.

Keep direct pushes available. Do not enable a blanket "Require a pull request"
rule unless you also deliberately configure a maintainer bypass. Without a ruleset,
GitHub does not technically block merging failed PRs: the maintainer checks the
statuses before merging. Publication independently enforces passing CI.

## Dry runs and recovery

**Publish Python package** has two manual inputs: an optional existing stable `tag`
and a `publish` checkbox that defaults to false. An empty tag tests current `main`;
it can never publish. Supplying a tag tests that exact release. Checking `publish`
requires a matching stable package version and a published stable GitHub release.
Drafts, prereleases, mismatched tags, and commits outside `main` cannot publish.

After an infrastructure failure, rerun the failed workflow or dispatch it with the
same tag and `publish` checked. Publication is serialized. Existing GitHub assets
and any files already on PyPI must have identical SHA256 hashes; otherwise the retry
fails. The release assets include `SHA256SUMS`. No artifact is silently replaced.

If code or metadata needs correction, make a new commit and a new release. Never
move a published tag, delete files to force a retry, or reuse a published version.
GitHub and PyPI are separate services, so a failure can leave one updated before
the other; inspect both before announcing the release.
