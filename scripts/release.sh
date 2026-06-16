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

if [[ -t 1 ]]; then
  BOLD=$'\033[1m'
  GREEN=$'\033[0;32m'
  RED=$'\033[0;31m'
  CYAN=$'\033[0;36m'
  NC=$'\033[0m'
else
  BOLD="" GREEN="" RED="" CYAN="" NC=""
fi

STEP=0
TOTAL_STEPS=7

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
  2. Auto-update CHANGELOG.md if ## [X.Y.Z] is missing (from git commits since last tag)
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
  - Clean git working tree (CHANGELOG.md may be auto-edited)
  - make, Python 3.11+, gh CLI (gh auth login)
  - PyPI trusted publishing (see docs/PUBLISHING.md)
EOF
}

log() { printf '  %s→%s %s\n' "$CYAN" "$NC" "$*"; }
ok() { printf '  %s✓%s %s\n' "$GREEN" "$NC" "$*"; }
fail() { printf '  %s✗%s %s\n' "$RED" "$NC" "$*" >&2; }
die() { fail "$*"; exit 1; }

step() {
  STEP=$((STEP + 1))
  printf '\n%s[%s/%s] %s%s\n' "$BOLD" "$STEP" "$TOTAL_STEPS" "$1" "$NC"
}

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

detect_python() {
  if [[ -n "${PYTHON:-}" ]]; then
    printf '%s' "$PYTHON"
    return
  fi
  local candidate
  for candidate in python3.13 python3.12 python3.11; do
    if command -v "$candidate" >/dev/null 2>&1 \
      && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null; then
      printf '%s' "$candidate"
      return
    fi
  done
  die "Python 3.11+ not found — install python3.11 or set PYTHON=python3.11"
}

ensure_dev_env() {
  PYTHON="$(detect_python)"
  export PYTHON
  log "using ${PYTHON} ($(${PYTHON} --version))"
  if [[ ! -x "$ROOT/.venv/bin/ruff" ]]; then
    log "dev tools missing — running make sync"
    run make -C "$ROOT" -s sync PYTHON="$PYTHON"
  fi
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

changelog_section_heading() {
  case "${1:-patch}" in
    patch) printf 'Fixed' ;;
    minor) printf 'Added' ;;
    major) printf 'Changed' ;;
    *) printf 'Changed' ;;
  esac
}

latest_release_tag() {
  git -C "$ROOT" describe --tags --match 'v*' --abbrev=0 2>/dev/null || true
}

collect_commit_bullets() {
  local range tag
  tag="$(latest_release_tag)"
  if [[ -n "$tag" ]]; then
    range="${tag}..HEAD"
  else
    range="HEAD"
  fi

  local count=0
  while IFS= read -r subject; do
    [[ -z "$subject" ]] && continue
    [[ "$subject" =~ ^Release\ v ]] && continue
    [[ "$subject" =~ ^Merge\  ]] && continue
    printf -- '- %s\n' "$subject"
    count=$((count + 1))
    [[ "$count" -ge 25 ]] && break
  done < <(git -C "$ROOT" log "$range" --pretty=format:'%s' --no-merges 2>/dev/null; echo)

  if [[ "$count" -eq 0 ]]; then
    printf -- '- Release %s\n' "$VERSION"
  fi
}

ensure_changelog_link() {
  local ver=$1
  local link="[${ver}]: https://github.com/openjkai/secscan_mcp/releases/tag/v${ver}"
  grep -qF "$link" "$CHANGELOG" && return
  printf '\n%s\n' "$link" >>"$CHANGELOG"
}

update_changelog() {
  if changelog_has_version "$VERSION"; then
    log "CHANGELOG already has ## [${VERSION}]"
    return
  fi

  local date heading body_file tmp
  date="$(date +%Y-%m-%d)"
  heading="$(changelog_section_heading "${BUMP_KIND:-patch}")"
  body_file="$(mktemp)"
  tmp="$(mktemp)"
  collect_commit_bullets >"$body_file"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "would add CHANGELOG section ## [${VERSION}] - ${date}"
    log "release notes preview:"
    sed 's/^/    /' "$body_file"
    rm -f "$body_file" "$tmp"
    return
  fi

  awk -v ver="$VERSION" -v date="$date" -v heading="$heading" -v body_file="$body_file" '
    BEGIN {
      while ((getline line < body_file) > 0) {
        if (line != "") body = body line "\n"
      }
      close(body_file)
      block = "## [" ver "] - " date "\n\n### " heading "\n\n" body "\n"
      inserted = 0
    }
    /^## \[/ && !inserted {
      print block
      inserted = 1
    }
    { print }
    END {
      if (!inserted) print block
    }
  ' "$CHANGELOG" >"$tmp"
  mv "$tmp" "$CHANGELOG"
  ensure_changelog_link "$VERSION"
  rm -f "$body_file"
  ok "CHANGELOG updated for ${VERSION}"
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
    if [[ "$DRY_RUN" -eq 1 ]]; then
      log "CHANGELOG ## [${VERSION}] will be added in step 1"
    else
      die "CHANGELOG.md missing ## [$VERSION] — run update_changelog first"
    fi
  fi

  local cur
  cur="$(current_version)"
  if [[ "$cur" == "$VERSION" ]]; then
    log "version already $VERSION in $VERSION_FILE (will re-release if tag absent)"
  fi

  if [[ "$DRY_RUN" -eq 0 ]]; then
    local dirty
    dirty="$(git -C "$ROOT" status --porcelain)"
    if [[ -n "$dirty" ]]; then
      local allowed=1
      while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        local file=${line:3}
        if [[ "$file" != "CHANGELOG.md" && "$file" != "src/secscan_mcp/__init__.py" ]]; then
          allowed=0
          break
        fi
      done <<<"$dirty"
      [[ "$allowed" -eq 1 ]] || die "working tree not clean — commit or stash changes first"
    fi
  fi

  if git -C "$ROOT" rev-parse "v${VERSION}" >/dev/null 2>&1; then
    die "tag v${VERSION} already exists"
  fi
}

bump_version_file() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    return
  fi
  sed -i "s/^__version__ = .*/__version__ = \"${VERSION}\"/" "$VERSION_FILE"
}

git_release() {
  local tag="v${VERSION}"
  local branch
  branch="$(git -C "$ROOT" rev-parse --abbrev-ref HEAD)"

  run git -C "$ROOT" add "$VERSION_FILE"
  if [[ -n "$(git -C "$ROOT" status --porcelain CHANGELOG.md 2>/dev/null)" ]]; then
    run git -C "$ROOT" add "$CHANGELOG"
  fi

  if [[ -n "$(git -C "$ROOT" status --porcelain)" ]]; then
    log "commit release changes ..."
    run git -C "$ROOT" commit -m "Release ${tag}"
    ok "committed"
  else
    ok "version ${VERSION} already committed — skipping commit"
  fi

  log "create tag ${tag} ..."
  run git -C "$ROOT" tag -a "$tag" -m "Release ${tag}"
  ok "tagged ${tag}"

  if ! confirm "Push ${branch} and ${tag} to origin?"; then
    die "aborted before push — tag ${tag} exists locally only"
  fi

  log "git push origin ${branch} ${tag} ..."
  run git -C "$ROOT" push origin "$branch" "$tag"
  ok "pushed to origin"
}

github_release() {
  local tag="v${VERSION}"
  local notes_file
  notes_file="$(mktemp)"
  extract_release_notes "$VERSION" >"$notes_file"

  if [[ ! -s "$notes_file" && "$DRY_RUN" -eq 1 ]]; then
    collect_commit_bullets >"$notes_file"
  fi

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

  printf '\n%ssecscan-mcp release%s\n' "$BOLD" "$NC"

  step "Resolve version & changelog"
  update_changelog

  step "Preflight checks"
  preflight
  ok "git, gh, and tag checks passed"

  log "target v${VERSION} (current $(current_version))"

  if ! confirm "Proceed with release v${VERSION}?"; then
    die "release cancelled"
  fi

  step "Set version"
  bump_version_file
  ok "version → ${VERSION}"

  step "Prepare dev environment"
  ensure_dev_env
  ok "using ${PYTHON}"

  step "Quality checks & build"
  log "make check ..."
  if ! run make -C "$ROOT" -s check PYTHON="$PYTHON"; then
    die "make check failed — fix errors above, then retry"
  fi
  ok "lint, typecheck, and tests passed"
  log "make build ..."
  if ! run make -C "$ROOT" -s build PYTHON="$PYTHON"; then
    die "make build failed — fix errors above, then retry"
  fi
  ok "package built (dist/)"

  step "Git tag & push"
  git_release

  step "GitHub Release (triggers PyPI)"
  github_release

  printf '\n%s✓ Release v%s complete%s\n' "$GREEN" "$VERSION" "$NC"
  log "track PyPI: gh run list --workflow=release.yml"
}

main "$@"
