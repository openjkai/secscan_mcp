#!/usr/bin/env bash
# Release secscan-mcp: bump version, verify, tag, push, create GitHub Release (→ PyPI).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="$ROOT/src/secscan_mcp/__init__.py"
CHANGELOG="$ROOT/CHANGELOG.md"

DRY_RUN=0
ASSUME_YES=0
VERSION=""
BUMP_KIND=""

usage() {
  cat <<'EOF'
Usage: scripts/release.sh [options] VERSION | BUMP

Create a semver release and publish to PyPI via GitHub Actions.

  VERSION   Explicit version: 0.1.1 or v0.1.1
  BUMP      Auto next version from current __version__:
              patch   0.1.0 → 0.1.1  (bug fixes)
              minor   0.1.0 → 0.2.0  (new features)
              major   0.1.0 → 1.0.0  (breaking changes)

Options:
  --dry-run    Print steps without changing anything
  --yes, -y    Skip confirmation prompts
  -h, --help   Show this help

What it does:
  1. Resolve target version (explicit or patch/minor/major bump)
  2. Verify CHANGELOG.md has a section for that version
  3. Bump __version__ in src/secscan_mcp/__init__.py
  4. Run make check && make build
  5. Commit, tag vX.Y.Z, push to origin
  6. Create GitHub Release (triggers PyPI publish workflow)

Examples:
  ./scripts/release.sh patch
  ./scripts/release.sh minor
  ./scripts/release.sh major
  ./scripts/release.sh --dry-run patch
  ./scripts/release.sh 0.1.1
  make release BUMP=patch
  make release-patch

Prerequisites:
  - CHANGELOG.md section ## [X.Y.Z] for the target version
  - Clean git working tree
  - make, Python 3.11+, gh CLI (gh auth login)
  - PyPI trusted publishing (see docs/PUBLISHING.md)
EOF
}

log() { printf '→ %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] %s\n' "$*"
  else
    "$@"
  fi
}

confirm() {
  if [[ "$ASSUME_YES" -eq 1 || "$DRY_RUN" -eq 1 ]]; then
    return 0
  fi
  local prompt=$1
  read -r -p "$prompt [y/N] " reply
  [[ "$reply" =~ ^[Yy]$ ]]
}

normalize_version() {
  local raw=$1
  raw="${raw#v}"
  [[ "$raw" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "invalid semver: $1 (expected X.Y.Z)"
  printf '%s' "$raw"
}

current_version() {
  grep -E '^__version__ = ' "$VERSION_FILE" | sed -E 's/^__version__ = ["'\'']([^"'\'']+)["'\'']/\1/'
}

next_version() {
  local cur bump major minor patch
  cur="$(normalize_version "$1")"
  bump="$2"
  IFS=. read -r major minor patch <<<"$cur"
  case "$bump" in
    patch) patch=$((patch + 1)) ;;
    minor)
      minor=$((minor + 1))
      patch=0
      ;;
    major)
      major=$((major + 1))
      minor=0
      patch=0
      ;;
    *) die "unknown bump kind: $bump (use patch, minor, or major)" ;;
  esac
  printf '%s.%s.%s' "$major" "$minor" "$patch"
}

resolve_bump_kind() {
  local raw="${1,,}" # lowercase
  case "$raw" in
    patch | minor | major) printf '%s' "$raw" ;;
    *) return 1 ;;
  esac
}

changelog_has_version() {
  local ver=$1
  grep -qE "^## \\[${ver}\\]" "$CHANGELOG"
}

extract_release_notes() {
  local ver=$1
  awk -v ver="$ver" '
    $0 ~ "^## \\[" ver "\\]" { found=1; next }
    found && /^## \[/ { exit }
    found { print }
  ' "$CHANGELOG" | sed '/^$/d'
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run) DRY_RUN=1; shift ;;
      --yes | -y) ASSUME_YES=1; shift ;;
      -h | --help) usage; exit 0 ;;
      -*) die "unknown option: $1" ;;
      *)
        [[ -z "$VERSION" ]] || die "unexpected argument: $1"
        VERSION="$1"
        shift
        ;;
    esac
  done
  [[ -n "$VERSION" ]] || { usage; exit 1; }

  if BUMP_KIND="$(resolve_bump_kind "$VERSION")"; then
    local cur next
    cur="$(current_version)"
    next="$(next_version "$cur" "$BUMP_KIND")"
    log "bump ${BUMP_KIND}: ${cur} → ${next}"
    VERSION="$next"
  else
    VERSION="$(normalize_version "$VERSION")"
  fi
}

preflight() {
  command -v git >/dev/null || die "git not found"
  command -v make >/dev/null || die "make not found"
  [[ -f "$VERSION_FILE" ]] || die "missing $VERSION_FILE"
  [[ -f "$CHANGELOG" ]] || die "missing $CHANGELOG"

  if [[ "$DRY_RUN" -eq 0 ]]; then
    command -v gh >/dev/null || die "gh CLI not found — install from https://cli.github.com"
    gh auth status >/dev/null 2>&1 || die "gh not authenticated — run: gh auth login"
  fi

  if ! changelog_has_version "$VERSION"; then
    die "CHANGELOG.md has no section '## [$VERSION]' — add release notes first"
  fi

  local cur
  cur="$(current_version)"
  if [[ "$cur" == "$VERSION" ]]; then
    log "version already $VERSION in $VERSION_FILE (will re-release if tag absent)"
  fi

  if [[ "$DRY_RUN" -eq 0 ]] && [[ -n "$(git -C "$ROOT" status --porcelain)" ]]; then
    die "working tree not clean — commit or stash changes first"
  fi

  if git -C "$ROOT" rev-parse "v${VERSION}" >/dev/null 2>&1; then
    die "tag v${VERSION} already exists"
  fi
}

bump_version_file() {
  log "set version → $VERSION"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    return
  fi
  sed -i "s/^__version__ = .*/__version__ = \"${VERSION}\"/" "$VERSION_FILE"
}

quality_gate() {
  log "make check"
  run make -C "$ROOT" check
  log "make build"
  run make -C "$ROOT" build
}

git_release() {
  local tag="v${VERSION}"
  local branch
  branch="$(git -C "$ROOT" rev-parse --abbrev-ref HEAD)"

  log "commit version bump"
  run git -C "$ROOT" add "$VERSION_FILE"
  run git -C "$ROOT" commit -m "Release ${tag}"

  log "create tag ${tag}"
  run git -C "$ROOT" tag -a "$tag" -m "Release ${tag}"

  if ! confirm "Push ${branch} and ${tag} to origin?"; then
    die "aborted before push — local commit and tag were created"
  fi

  log "git push origin ${branch} ${tag}"
  run git -C "$ROOT" push origin "$branch" "$tag"
}

github_release() {
  local tag="v${VERSION}"
  local notes_file
  notes_file="$(mktemp)"
  extract_release_notes "$VERSION" >"$notes_file"

  if [[ ! -s "$notes_file" ]]; then
    rm -f "$notes_file"
    die "no release notes found under ## [$VERSION] in CHANGELOG.md"
  fi

  log "create GitHub Release ${tag}"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "release notes:"
    cat "$notes_file"
    rm -f "$notes_file"
    return
  fi

  gh release create "$tag" \
    --title "secscan-mcp ${tag}" \
    --notes-file "$notes_file"
  rm -f "$notes_file"

  log "done — PyPI publish workflow will run automatically"
  log "track: gh run list --workflow=release.yml"
}

main() {
  parse_args "$@"
  cd "$ROOT"
  preflight

  log "release secscan-mcp v${VERSION} (current: $(current_version))"

  if ! confirm "Proceed with release v${VERSION}?"; then
    die "aborted"
  fi

  bump_version_file
  quality_gate
  git_release
  github_release
}

main "$@"
