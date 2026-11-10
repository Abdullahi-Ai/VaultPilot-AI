# VaultPilot AI — Final Round 2 GitHub Publication Execution Checklist (Hardened)

**Target Repository:** `git@github.com:Abdullahi-Ai/VaultPilot-AI.git`  
**Target Branch:** `main`  
**Current Local Baseline Commit:** `7f12ef8`  
**Execution Mode:** Human-Operator Review & Manual Execution Only  
**Safety Mandate:** Zero force-push, zero `git add .`, zero `git add dist/`, zero modification of existing databases or source documents, and explicit verification of Skill ZIP digests and remote cleanliness before pushing.

---

## 1. Tested Bash Path Security Scanner

### Path Security Function Specification
Rather than relying on brittle, complex regex strings or escaped wildcards in single-line shell commands, we use a modular, fully tested Bash path checking function (`is_sensitive_path`) with native `case` pattern matching.

It validates paths against five strict categories:
1. Real `.env` variants (`.env`, `.env.local`, `.env.production`, etc.) while explicitly allowing `.env.example`.
2. Database files and SQLite sidecars via clean, unescaped `case` globs:
   - Primary databases: `*.db`, `*.sqlite`, `*.sqlite3`
   - Write-Ahead Logs: `*.db-wal`, `*.sqlite-wal`, `*.sqlite3-wal`
   - Shared-Memory files: `*.db-shm`, `*.sqlite-shm`, `*.sqlite3-shm`
3. Cryptographic private keys and certificates (`*.pem`, `*.key`, `*.p12`, `*.pfx`).
4. Dependency caches and package trees at root or any depth (`node_modules/`, `__pycache__/`).
5. Generated frontend production build directories (`frontend/dist/`).

```bash
is_sensitive_path() {
    local path="$1"

    # Allow explicit safe exceptions first
    if [[ "$path" == ".env.example" || "$path" == */.env.example ]]; then
        return 1
    fi

    local base="${path##*/}"

    # 1. Environment files (.env, .env.local, .env.production, etc.)
    if [[ "$base" == ".env" || "$base" == .env.* ]]; then
        return 0
    fi

    # 2. Database files and SQLite WAL/SHM sidecars
    case "$base" in
        *.db|*.sqlite|*.sqlite3|\
        *.db-wal|*.db-shm|\
        *.sqlite-wal|*.sqlite-shm|\
        *.sqlite3-wal|*.sqlite3-shm)
            return 0
            ;;
    esac

    # 3. Certificates, keys, and credentials
    case "$base" in
        *.pem|*.key|*.p12|*.pfx)
            return 0
            ;;
    esac

    # 4. node_modules or __pycache__ at root or any depth
    if [[ "$path" == "node_modules"* || "$path" == *"node_modules/"* || "$path" == "__pycache__"* || "$path" == *"__pycache__/"* ]]; then
        return 0
    fi

    # 5. frontend/dist/ at root or nested
    if [[ "$path" == "frontend/dist/"* || "$path" == *"frontend/dist/"* ]]; then
        return 0
    fi

    return 1
}

# Stream scanner: Reads lines from STDIN; prints violations to STDERR; exits 1 if violation found
check_path_stream() {
    local has_violation=0
    while IFS= read -r file_path || [[ -n "$file_path" ]]; do
        [[ -z "$file_path" ]] && continue
        if is_sensitive_path "$file_path"; then
            echo "[SENSITIVE BLOCKED] $file_path" >&2
            has_violation=1
        fi
    done
    return "$has_violation"
}
```

### Actual Test Results (Directly Executed in Bash)
The test suite was executed in Bash with `set -euo pipefail`. All 29 test cases (safe, sensitive, nested, and all 9 SQLite sidecar variations) were directly executed and verified:

| Test Input Path | Expected Category | Test Execution Status | Actual Stream Output | Stream Exit Status |
| :--- | :---: | :---: | :---: | :---: |
| `.env.example` | **SAFE** | **VERIFIED** | Allowed (Silent) | Clean stream: `0` |
| `README.md` | **SAFE** | **VERIFIED** | Allowed (Silent) | Clean stream: `0` |
| `backend/requirements.txt` | **SAFE** | **VERIFIED** | Allowed (Silent) | Clean stream: `0` |
| `.env` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] .env` | Violation: `1` |
| `.env.local` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] .env.local` | Violation: `1` |
| `backend/.env.production` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] backend/.env.production` | Violation: `1` |
| `backend/vaultpilot.db` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] backend/vaultpilot.db` | Violation: `1` |
| `backend/vaultpilot.db-wal`| **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] backend/vaultpilot.db-wal` | Violation: `1` |
| `backend/vaultpilot.db-shm`| **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] backend/vaultpilot.db-shm` | Violation: `1` |
| `backend/vaultpilot.sqlite` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] backend/vaultpilot.sqlite` | Violation: `1` |
| `backend/vaultpilot.sqlite-wal` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] backend/vaultpilot.sqlite-wal` | Violation: `1` |
| `backend/vaultpilot.sqlite-shm` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] backend/vaultpilot.sqlite-shm` | Violation: `1` |
| `backend/vaultpilot.sqlite3` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] backend/vaultpilot.sqlite3` | Violation: `1` |
| `backend/vaultpilot.sqlite3-wal` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] backend/vaultpilot.sqlite3-wal` | Violation: `1` |
| `backend/vaultpilot.sqlite3-shm` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] backend/vaultpilot.sqlite3-shm` | Violation: `1` |
| `frontend/dist/assets/index.js`| **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] frontend/dist/assets/index.js` | Violation: `1` |
| `__pycache__/module.pyc` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] __pycache__/module.pyc` | Violation: `1` |
| `backend/__pycache__/module.pyc`| **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] backend/__pycache__/module.pyc`| Violation: `1` |
| `node_modules/package/file.js` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] node_modules/package/file.js` | Violation: `1` |
| `frontend/node_modules/package/file.js`| **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] frontend/node_modules/package/file.js` | Violation: `1` |
| `server.pem` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] server.pem` | Violation: `1` |
| `private.key` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] private.key` | Violation: `1` |
| `database.db` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] database.db` | Violation: `1` |
| `database.sqlite` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] database.sqlite` | Violation: `1` |
| `database.sqlite3` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] database.sqlite3` | Violation: `1` |
| `database.sqlite-wal` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] database.sqlite-wal` | Violation: `1` |
| `database.sqlite-shm` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] database.sqlite-shm` | Violation: `1` |
| `nested/path/database.sqlite3-wal` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] nested/path/database.sqlite3-wal` | Violation: `1` |
| `nested/path/database.sqlite3-shm` | **FLAG** | **VERIFIED** | `[SENSITIVE BLOCKED] nested/path/database.sqlite3-shm` | Violation: `1` |

### How to Scan Proposed Publication Lists Before Staging
To audit a candidate file list before running `git add`:

```bash
cat << 'EOF' | check_path_stream
.env.example
docker-compose.nas.yml
backend/requirements.txt
backend/app/main.py
frontend/package.json
dist/vaultpilot-skill.zip
dist/vaultpilot-skill-round2-candidate.zip
EOF
# Returns exit code 0 if all paths are safe.
```

To audit files currently staged in Git:
```bash
git diff --cached --name-only | check_path_stream
```

---

## 2. Secret Scanning Availability & Local Procedures

### Scanner Availability Audit
A system-level check was performed:
- `gitleaks`: **NOT INSTALLED**
- `detect-secrets`: **NOT INSTALLED**
- `trufflehog`: **NOT INSTALLED**
- Local Docker daemon: Docker binary `29.1.3` installed, but user lacks permission on `/var/run/docker.sock` in this sandbox.

> [!WARNING]
> Simple keyword search (`git diff -S`) does **NOT** prove the absence of secrets. High-entropy API tokens, HMAC secret overrides, and private certificates can easily evade simple keyword matches. Never upload repository files to external web scanners.

### Pinned Local Secret-Scanning Procedures for the Operator

#### Procedure 1: Native Gitleaks Binary with Official SHA-256 Checksum Verification
On a local workstation with internet access, download the official pinned release binary, verify its SHA-256 digest against the official release manifest, and execute:

```bash
# 1. Define pinned release & official SHA-256 digest
GITLEAKS_VER="8.18.4"
EXPECTED_GITLEAKS_SHA="ba6dbb656933921c775ee5a2d1c13a91046e7952e9d919f9bac4cec61d628e7d"
TAR_PATH="/tmp/gitleaks_${GITLEAKS_VER}_linux_x64.tar.gz"

# 2. Download pinned archive
curl -sSL -o "$TAR_PATH" "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VER}/gitleaks_${GITLEAKS_VER}_linux_x64.tar.gz"

# 3. Verify cryptographic checksum before extracting or executing
ACTUAL_GITLEAKS_SHA=$(sha256sum "$TAR_PATH" | awk '{print $1}')
if [ "$ACTUAL_GITLEAKS_SHA" != "$EXPECTED_GITLEAKS_SHA" ]; then
    echo "CRITICAL SECURITY ERROR: Gitleaks binary checksum mismatch!"
    echo "Expected: $EXPECTED_GITLEAKS_SHA"
    echo "Actual:   $ACTUAL_GITLEAKS_SHA"
    rm -f "$TAR_PATH"
    exit 1
fi
echo "Gitleaks binary checksum verified: $EXPECTED_GITLEAKS_SHA"

# 4. Extract and run scan against staged changes with secret values redacted
tar -xzf "$TAR_PATH" -C /tmp/ gitleaks
/tmp/gitleaks detect --source=. --staged --redact --verbose

# 5. Clean up binary
rm -f /tmp/gitleaks "$TAR_PATH"
```

*Note: If checksum verification cannot be completed (e.g. no internet access), Gitleaks scanning remains explicitly **UNVERIFIED**.*

#### Procedure 2: Containerized Gitleaks (Pinned v8.18.4)
If running on a host with operational Docker permissions:
```bash
docker run --rm -v "$(pwd):/path" zricethezav/gitleaks:v8.18.4 detect --source="/path" --staged --redact --verbose
```

#### Procedure 3: Offline Staged Diff Regex Pattern Scan (Local Fallback)
```bash
# 1. Scan for private key headers
git diff --cached -S"BEGIN PRIVATE KEY" --quiet && \
git diff --cached -S"BEGIN RSA PRIVATE KEY" --quiet && \
git diff --cached -S"BEGIN OPENSSH PRIVATE KEY" --quiet && \
git diff --cached -S"BEGIN EC PRIVATE KEY" --quiet || { echo "CRITICAL: Private key header detected in staged diff!"; exit 1; }

# 2. Scan for generic credential assignments without printing secrets
git diff --cached | grep -E '^\+[^+]' | grep -i -E '(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|private[_-]?key)[[:space:]]*[:=][[:space:]]*["'\''][A-Za-z0-9/\+=_\.\-]{16,}["'\'']' > /dev/null && \
  { echo "CRITICAL: Potential high-entropy secret assignment detected in staged diff!"; exit 1; } || \
  echo "Staged diff regex scan: CLEAN"
```

---

## 3. Verified Selective Staging Review

A full inspection of the repository structure confirms all components required for a complete, reproducible clone:

- **Root & Orchestration:** `.env.example`, `docker-compose.nas.yml`, `README.md`.
- **Backend Core:** `backend/requirements.txt`, `backend/alembic.ini`, `backend/pytest.ini`, `backend/Dockerfile`, `backend/alembic/`, `backend/app/`, `backend/tests/`.
- **Frontend Core:** `frontend/package.json`, `frontend/package-lock.json`, `frontend/index.html`, `frontend/tsconfig.json`, `frontend/tsconfig.node.json`, `frontend/vite.config.ts`, `frontend/postcss.config.js`, `frontend/tailwind.config.js`, `frontend/Dockerfile`, `frontend/nginx.conf`, `frontend/src/`.
- **UGREEN Skill:** `vaultpilot/SKILL.md`, `vaultpilot/references/`, and tracked deletion of `vaultpilot/README.md`.
- **Skill Archives:** `dist/vaultpilot-skill.zip` and `dist/vaultpilot-skill-round2-candidate.zip` (both preserving hash `4b002849...`).
- **Docs & Scripts:** `docs/` (dossiers, reports, runbooks), `scripts/` (reproducibility and testing tools).

### Exact Staging Commands
```bash
# 1. Deployment configurations & repository root
git add .env.example
git add docker-compose.nas.yml
git add README.md

# 2. Backend dependency manifests, configs, migrations & source
git add backend/requirements.txt
git add backend/alembic.ini
git add backend/pytest.ini
git add backend/Dockerfile
git add backend/alembic/versions/
git add backend/app/
git add backend/tests/

# 3. Frontend manifests, configs, source & web assets
git add frontend/package.json
git add frontend/package-lock.json
git add frontend/index.html
git add frontend/tsconfig.json
git add frontend/tsconfig.node.json
git add frontend/vite.config.ts
git add frontend/postcss.config.js
git add frontend/tailwind.config.js
git add frontend/Dockerfile
git add frontend/nginx.conf
git add frontend/src/

# 4. UGREEN Skill Package (Specific Archives ONLY - Never dist/)
git add dist/vaultpilot-skill.zip
git add dist/vaultpilot-skill-round2-candidate.zip

# 5. UGREEN Skill Source & Tracked Deletion
git add vaultpilot/SKILL.md
git add vaultpilot/references/
git add -u -- vaultpilot/README.md

# 6. Operational Scripts & Competition Documentation
git add scripts/
git add docs/
```

*Note: `HACKATHON_COMPETITIVENESS_AUDIT.md` remains untracked (`??`).*

---

## 4. Pre-Commit Verification Sequence

Execute this verification script. It asserts all pre-conditions before allowing a commit:

```bash
set -euo pipefail

echo "=== CHECK 1: VERIFYING SKILL ARCHIVE INTEGRITY ==="
EXPECTED_SHA="4b002849af79eb3c5d5cb0aa77c9f083480b57250465747a19c4dc997f1dd01f"
SKILL_SHA=$(sha256sum dist/vaultpilot-skill.zip | awk '{print $1}')
CAND_SHA=$(sha256sum dist/vaultpilot-skill-round2-candidate.zip | awk '{print $1}')

if [ "$SKILL_SHA" != "$EXPECTED_SHA" ]; then
    echo "CRITICAL FAILURE: dist/vaultpilot-skill.zip hash is $SKILL_SHA (expected $EXPECTED_SHA)"
    exit 1
fi
if [ "$CAND_SHA" != "$EXPECTED_SHA" ]; then
    echo "CRITICAL FAILURE: dist/vaultpilot-skill-round2-candidate.zip hash is $CAND_SHA (expected $EXPECTED_SHA)"
    exit 1
fi
echo "Skill ZIP hashes verified: $EXPECTED_SHA"

echo "=== CHECK 2: CHECKING FOR WHITESPACE AND SYNTAX ERRORS ==="
git diff --cached --check || { echo "WARNING: Whitespace check flagged issues."; }

echo "=== CHECK 3: RUNNING STAGED PATH SECURITY SCANNER ==="
git diff --cached --name-only | check_path_stream || {
    echo "CRITICAL FAILURE: Sensitive files detected in Git staging index!"
    exit 1
}
echo "Staged paths verified: 0 sensitive files staged."

echo "=== CHECK 4: VERIFYING DELETION OF VAULTPILOT/README.MD ==="
README_STATUS=$(git status --short -- vaultpilot/README.md | awk '{print $1}')
if [ "$README_STATUS" != "D" ]; then
    echo "CRITICAL FAILURE: vaultpilot/README.md is not staged for deletion (status: $README_STATUS)!"
    exit 1
fi
echo "vaultpilot/README.md deletion verified."

echo "=== CHECK 5: VERIFYING NO OTHER UNEXPECTED DELETIONS ==="
UNEXPECTED_DELETIONS=$(git diff --cached --name-only --diff-filter=D | grep -v 'vaultpilot/README.md' || true)
if [ -n "$UNEXPECTED_DELETIONS" ]; then
    echo "CRITICAL FAILURE: Unexpected files were deleted in staging:"
    echo "$UNEXPECTED_DELETIONS"
    exit 1
fi
echo "Deletions verified: Only vaultpilot/README.md is staged as deleted."

echo "=== CHECK 6: RUNNING STAGED DIFF SECRET SCAN ==="
git diff --cached -S"BEGIN PRIVATE KEY" --quiet && \
git diff --cached -S"BEGIN RSA PRIVATE KEY" --quiet && \
git diff --cached -S"BEGIN OPENSSH PRIVATE KEY" --quiet || { echo "CRITICAL: Private key header detected!"; exit 1; }
echo "Staged diff secret scan: CLEAN"

echo "=== ALL PRE-COMMIT VERIFICATIONS PASSED ==="
```

---

## 5. Commit and Publication Push Instructions

Execute only after all pre-commit verifications pass:

```bash
# 1. Verify remote is still empty before committing
REMOTE_HEADS=$(git ls-remote --heads origin)
if [ -n "$REMOTE_HEADS" ]; then
    echo "CRITICAL: Remote origin is NOT empty! Aborting commit."
    exit 1
fi

# 2. Commit the Round 2 implementation
git commit -m "feat(round2): complete UGREEN NAS integration, security hardening, and evidence review workflow

- Implement Tri-Mode storage isolation (Emulated, UGOS Read-Only Mount, Bridge Daemon)
- Add human-in-the-loop evidence review workflow with HMAC-SHA256 audit signing
- Add Uliya agent bridge with deterministic 5-stage delegation state machine
- Provide hardened Docker Compose configuration for UGOS Container Station
- Expand backend automated test suite to 183 tests across all modules
- Include comprehensive Round 2 competition dossiers, verification reports, and video scripts"

# 3. Publish to GitHub establishing upstream tracking
git push -u origin main
```

---

## 6. Post-Push Assertions & Clean-Clone Procedure

Execute this script after pushing. It uses strict Bash error handling (`set -euo pipefail`), halts on any discrepancy, and retains the clone directory for operator inspection:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== POST-PUSH ASSERTION 1: VERIFYING REMOTE HEAD ALIGNMENT ==="
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git ls-remote --heads origin main | awk '{print $1}')

if [ -z "$REMOTE_COMMIT" ]; then
    echo "CRITICAL ASSERTION FAILED: Remote branch 'main' does not exist on origin!"
    exit 1
fi

if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
    echo "CRITICAL ASSERTION FAILED: Local HEAD ($LOCAL_COMMIT) does not match remote main ($REMOTE_COMMIT)!"
    exit 1
fi
echo "SUCCESS: Remote origin/main matches local HEAD ($LOCAL_COMMIT)"

echo "=== POST-PUSH ASSERTION 2: PERFORMING CLEAN CLONE ==="
CLONE_DIR=$(mktemp -d /tmp/vaultpilot-audit-XXXXXX)
echo "Cloning into temporary directory: $CLONE_DIR"
git clone git@github.com:Abdullahi-Ai/VaultPilot-AI.git "$CLONE_DIR"

CLONE_COMMIT=$(git -C "$CLONE_DIR" rev-parse HEAD)
if [ "$CLONE_COMMIT" != "$REMOTE_COMMIT" ]; then
    echo "CRITICAL ASSERTION FAILED: Cloned HEAD ($CLONE_COMMIT) does not match remote commit ($REMOTE_COMMIT)!"
    exit 1
fi
echo "SUCCESS: Cloned commit matches remote commit ($CLONE_COMMIT)"

echo "=== POST-PUSH ASSERTION 3: VERIFYING REQUIRED FILES IN CLEAN CLONE ==="
REQUIRED_FILES=(
    "README.md"
    ".env.example"
    "docker-compose.nas.yml"
    "backend/Dockerfile"
    "backend/requirements.txt"
    "backend/alembic.ini"
    "backend/pytest.ini"
    "backend/app/main.py"
    "frontend/Dockerfile"
    "frontend/nginx.conf"
    "frontend/package.json"
    "frontend/package-lock.json"
    "frontend/index.html"
    "frontend/tsconfig.json"
    "frontend/tsconfig.node.json"
    "frontend/vite.config.ts"
    "frontend/postcss.config.js"
    "frontend/tailwind.config.js"
    "vaultpilot/SKILL.md"
    "vaultpilot/references/finding-classification.md"
    "vaultpilot/references/investigation-methodology.md"
    "vaultpilot/references/submission-disclosures.md"
    "vaultpilot/references/testing-guide.md"
    "dist/vaultpilot-skill.zip"
    "dist/vaultpilot-skill-round2-candidate.zip"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$CLONE_DIR/$file" ]; then
        echo "CRITICAL ASSERTION FAILED: Required file missing in clean clone: $file"
        exit 1
    else
        echo "  [FOUND] $file"
    fi
done

# Assert that vaultpilot/README.md was correctly excluded
if [ -f "$CLONE_DIR/vaultpilot/README.md" ]; then
    echo "CRITICAL ASSERTION FAILED: vaultpilot/README.md is present in the clean clone (violates Uliya specification)!"
    exit 1
fi
echo "  [EXCLUDED] vaultpilot/README.md (clean Uliya root confirmed)"

echo "=== POST-PUSH ASSERTION 4: VERIFYING SKILL ZIP HASHES IN CLONE ==="
EXPECTED_SHA="4b002849af79eb3c5d5cb0aa77c9f083480b57250465747a19c4dc997f1dd01f"
CLONE_SKILL_SHA=$(sha256sum "$CLONE_DIR/dist/vaultpilot-skill.zip" | awk '{print $1}')
CLONE_CAND_SHA=$(sha256sum "$CLONE_DIR/dist/vaultpilot-skill-round2-candidate.zip" | awk '{print $1}')

if [ "$CLONE_SKILL_SHA" != "$EXPECTED_SHA" ]; then
    echo "CRITICAL ASSERTION FAILED: Cloned dist/vaultpilot-skill.zip hash is $CLONE_SKILL_SHA (expected $EXPECTED_SHA)!"
    exit 1
fi
if [ "$CLONE_CAND_SHA" != "$EXPECTED_SHA" ]; then
    echo "CRITICAL ASSERTION FAILED: Cloned dist/vaultpilot-skill-round2-candidate.zip hash is $CLONE_CAND_SHA (expected $EXPECTED_SHA)!"
    exit 1
fi
echo "SUCCESS: Both cloned Skill ZIP archives match expected SHA-256 ($EXPECTED_SHA)"

echo "=== POST-PUSH STEP 5: CLEAN CLONE EXECUTION TESTING ==="
echo "Note: The following execution checks run inside the temporary clone without modifying the working directory."

# Backend dependency and test execution
echo "Executing clean-clone backend tests..."
python3 -m venv "$CLONE_DIR/clone_venv"
"$CLONE_DIR/clone_venv/bin/pip" install --quiet -r "$CLONE_DIR/backend/requirements.txt" pytest httpx
"$CLONE_DIR/clone_venv/bin/pytest" -q "$CLONE_DIR/backend/tests"

# Frontend dependency and production build execution
echo "Executing clean-clone frontend production build..."
(cd "$CLONE_DIR/frontend" && npm ci --quiet && npm run build)

echo "============================================================"
echo "CLEAN CLONE AUDIT COMPLETE: ALL ASSERTIONS AND TESTS PASSED"
echo "Temporary clone directory retained for review at: $CLONE_DIR"
echo "Operator may inspect or remove manually: rm -rf $CLONE_DIR"
echo "============================================================"
```

---

## 7. Status of Verification Checks

### Directly Executed & Verified in Local Repository
1. **Filename Path Scanner:** Tested and verified against all 29 safe, sensitive, nested, and SQLite sidecar variations.
2. **Backend Automated Tests:** 183 / 183 tests pass (`backend/venv/bin/pytest -q backend/tests`).
3. **Frontend Production Build:** Verified (`npm run build` succeeds cleanly).
4. **Skill Compliance:** Passes official static check (`scripts/package_skill.py --verify-only`).
5. **Skill ZIP Digest:** Verified both archives match `4b002849...`.
6. **Remote Repository Status:** Verified empty (`git ls-remote --heads origin` exited 0 with 0 refs).
7. **Database Isolation:** Verified untracked and untouched (SHA-256: `daad640a...`).

### Explicitly UNVERIFIED Checks (Pending Future Execution)
1. **[UNVERIFIED] Dedicated Gitleaks Secret Scan:** Unverified because Gitleaks is not installed locally and checksum-verified binary installation has not yet been executed by the operator.
2. **[UNVERIFIED] GitHub Push & Remote Commit Comparison:** Unverified until the operator executes `git push -u origin main`.
3. **[UNVERIFIED] Fresh GitHub Clone:** Unverified until post-push clone execution.
4. **[UNVERIFIED] Backend Tests Inside Fresh Clone:** Unverified until executed inside the post-push clone directory.
5. **[UNVERIFIED] Frontend Build Inside Fresh Clone:** Unverified until executed inside the post-push clone directory.
6. **[UNVERIFIED] Physical UGREEN NAS & Live Uliya Daemon Execution:** Unverified until physical hardware testing window (22–28 November 2026).
