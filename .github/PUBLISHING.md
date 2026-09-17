# Publishing to PyPI

The `publish.yml` workflow runs when a GitHub Release is published. Pushing a tag
alone does not trigger it. Tags must have the form `v0.0.6`. The package version
is derived automatically from Git tags using Hatchling and hatch-vcs;
`pyproject.toml` declares `dynamic = ["version"]`. Tests and the build must pass
before publishing, and both distribution versions are checked against the tag.

## One-time setup

1. In the GitHub repository settings, create an environment named `pypi`.
2. In the PyPI project's **Publishing** settings, add a GitHub Trusted Publisher:

   | Field | Value |
   | --- | --- |
   | Owner | `pydna-group` |
   | Repository | `pydna-interactive-utils` |
   | Workflow filename | `publish.yml` |
   | Environment | `pypi` |

   These values follow the current Git remote. If the repository is renamed,
   update the PyPI configuration accordingly.


## Publish a version

1. Commit the changes you want to release and push the commit to GitHub.
2. Create and publish a GitHub Release with a new tag, such as `v0.0.6`,
   targeting that commit. No `uv version` command or manual version edit is needed.

The workflow tests the release, builds a wheel and source distribution with uv,
then publishes both to PyPI using a separate job with OIDC permissions.
Both workflows fetch Git history and tags so version detection works. Builds
between tags or with uncommitted changes receive a development version. The
generated `src/pydna_utils/_version.py` supplies the runtime `__version__` and
is not committed; `uv sync` or `uv build` generates it.
PyPI does not allow replacing previously uploaded distribution files; use a new
version for a subsequent release.

See the [uv Trusted Publishing guide](https://docs.astral.sh/uv/guides/integration/github/#publishing-to-pypi).
