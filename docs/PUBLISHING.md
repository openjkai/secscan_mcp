# Publishing to PyPI

This guide is for maintainers releasing **secscan-mcp** to [PyPI](https://pypi.org/project/secscan-mcp/).

## Just registered on PyPI? Do this next

Your GitHub Action failed with `invalid-publisher` because PyPI did not have a **trusted publisher** yet. Fix it in this order:

### Step 1 — Add trusted publisher on PyPI

1. Log in at [pypi.org](https://pypi.org)
2. Click your avatar → **Account settings**
3. Left sidebar → **Publishing** (under “Security”)
4. **Add a new pending publisher**
5. Enter **exactly** (must match GitHub or publish will fail):

| Field | Value |
|-------|--------|
| **PyPI Project Name** | `secscan-mcp` |
| **Owner** | `openjkai` |
| **Repository name** | `secscan_mcp` |
| **Workflow name** | `release.yml` |
| **Environment name** | `pypi` |

6. Save. You do **not** need to create the project manually first — the first successful upload creates it.

### Step 2 — Create GitHub environment

1. Open https://github.com/openjkai/secscan_mcp/settings/environments
2. **New environment** → name it **`pypi`** (lowercase, exact)
3. Save (no secrets required for trusted publishing)

### Step 3 — Publish

**Option A — Re-run the failed release** (if `v0.1.1` already exists):

1. https://github.com/openjkai/secscan_mcp/actions/workflows/release.yml
2. Open the failed run for `v0.1.1`
3. **Re-run all jobs**

**Option B — Manual workflow** (after pushing latest `release.yml`):

1. Actions → **Release** → **Run workflow** → Run

**Option C — New patch release:**

```bash
make release-patch PYTHON=python3.11   # CHANGELOG auto-updated from git log
```

### Step 4 — Verify

```bash
pip install secscan-mcp
secscan-mcp --help 2>/dev/null || which secscan-mcp
```

Or check https://pypi.org/project/secscan-mcp/

---

## One-time PyPI setup (reference)

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

1. Ensure PyPI trusted publisher + GitHub `pypi` environment are configured ([below](#just-registered-on-pypi-do-this-next)).
2. Run the release script — **CHANGELOG is updated automatically** from commits since the last tag:

   ```bash
   make release-patch          # 0.1.1 → 0.1.2
   make release-minor
   make release-major

   # Preview without writing:
   make release-patch DRY_RUN=1
   ```

   Optional: edit `CHANGELOG.md` after the script adds `## [X.Y.Z]` and before you confirm the push, if you want custom release notes.

   The script will:
   - Insert `## [X.Y.Z]` into CHANGELOG (from `git log` since last tag)
   - Bump `src/secscan_mcp/__init__.py`
   - Run `make check` and `make build`
   - Commit, tag `vX.Y.Z`, push to origin
   - Create a GitHub Release (notes from CHANGELOG → triggers PyPI publish)

### Manual checklist (if not using the script)

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
