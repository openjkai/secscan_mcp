# Publishing to PyPI

This guide is for maintainers releasing **secscan-mcp** to [PyPI](https://pypi.org/project/secscan-mcp/).

## One-time PyPI setup

1. Create a PyPI account and register the project name `secscan-mcp` (first release creates it).
2. On [pypi.org](https://pypi.org) → **Your projects** → **Publishing** → **Add a new pending publisher** (trusted publishing):
   - **PyPI Project Name:** `secscan-mcp`
   - **Owner:** `openjkai`
   - **Repository name:** `secscan_mcp`
   - **Workflow name:** `release.yml`
   - **Environment name:** `pypi`
3. In GitHub → **Settings** → **Environments** → create environment **`pypi`** (no secrets required for trusted publishing).

Trusted publishing uses OIDC — no long-lived `PYPI_API_TOKEN` in GitHub secrets.

## Release checklist

1. Update version in `src/secscan_mcp/__init__.py` (single source of truth via hatch).
2. Add a section to [CHANGELOG.md](../CHANGELOG.md).
3. Run locally:

   ```bash
   make check
   make build
   ```

4. Commit, push, and create a **GitHub Release** with tag `vX.Y.Z` (e.g. `v0.1.0`).
5. The [release workflow](../.github/workflows/release.yml) builds and publishes to PyPI automatically.

## Local build (verify before release)

```bash
make build
# Inspect dist/
unzip -l dist/secscan_mcp-*.whl | grep rules
```

The wheel must include `secscan_mcp/rules/custom_secrets.yaml`.

## Manual publish (fallback)

If trusted publishing is not configured:

```bash
pip install build twine
make build
twine upload dist/*
```

Use an API token from PyPI account settings as `TWINE_PASSWORD` (username `__token__`).

## After publish

Users can install with:

```bash
pip install secscan-mcp
uvx secscan-mcp   # no prior install; requires uv
```

Update README badges if desired:

```markdown
[![PyPI](https://img.shields.io/pypi/v/secscan-mcp)](https://pypi.org/project/secscan-mcp/)
```
