---
name: npmjs-cli
description: Manage npm registry operations including publishing packages, versioning, deprecating, unpublishing, and access control. Use whenever the user needs to publish to npm, manage package versions, add/remove maintainers, deprecate old versions, or handle npm authentication. Essential for any npm registry workflow including package releases, beta tags, scoped packages, and team collaboration.
---

# npmjs-cli

A skill for managing npm registry operations and package lifecycle.

## Prerequisites

```bash
npm --version       # npm CLI installed
npm whoami          # logged in (if not: npm login)
npm config get registry   # should be https://registry.npmjs.org/ for public packages
```

If the registry is wrong (e.g., pointing to a company registry or cnpm mirror):
```bash
# Publish to the official registry regardless of local config
npm publish --registry https://registry.npmjs.org
```

## Workflow 1: Publish a Package

**ALWAYS run the pre-flight checks before publishing.** Most failures are preventable.

### Step 1 — Pre-flight

```bash
# Auth & registry
npm whoami                           # must succeed
npm config get registry              # verify target registry

# Version conflict check
PKGNAME=$(node -p "require('./package.json').name")
PKGVER=$(node -p "require('./package.json').version")
npm view "${PKGNAME}@${PKGVER}" version 2>/dev/null && echo "ERROR: ${PKGVER} already exists on npm" || echo "OK: version is available"

# Contents check
npm publish --dry-run                # review files + total size
```

### Step 2 — Publish

```bash
# Unscoped package (most common)
npm publish

# Scoped package (@org/pkg) — FIRST TIME requires --access public
npm publish --access public

# If 2FA/OTP is enabled on the account (very common):
# npm will prompt interactively, OR pass it explicitly:
npm publish --otp=<CODE>

# Scoped + OTP combo
npm publish --access public --otp=<CODE>
```

### Step 3 — Verify

```bash
npm view "${PKGNAME}@${PKGVER}" version   # should print the version you just published
```

### Publish Failed? Diagnose

```
npm publish failed
├── ENEEDAUTH → npm login (or set NPM_TOKEN for CI)
├── E403 Forbidden
│   ├── "you must verify your email" → check npm email
│   ├── "requires OTP" → re-run with --otp=<CODE>
│   ├── scoped package first time → add --access public
│   └── name taken → npm view <desired-name> to confirm, then rename
├── EPUBLISHCONFLICT (version exists)
│   ├── npm version patch → npm publish
│   └── OR set an explicit version: npm version 1.2.4 --no-git-tag-version
├── E400 "Invalid version"
│   └── version must be pure semver: 1.2.3 (not v1.2.3)
├── E402 "Payment Required"
│   └── private scoped packages need a paid npm plan, or use --access public
├── ETARGET / network error
│   └── check npm config get registry, try --registry https://registry.npmjs.org
└── "prepublishOnly" script failed
    └── fix the build/test error first, then retry npm publish
```

## Workflow 2: Unpublish / Remove a Version

### Eligibility

- **Within 72 hours** of publishing: `npm unpublish` is allowed
- **After 72 hours**: unpublish is blocked — use deprecation instead
- Package must have **no dependents** (no other public packages depend on it)

### Execute

```bash
# Remove a specific version
npm unpublish <package>@<version>

# If prompted for OTP:
npm unpublish <package>@<version> --otp=<CODE>

# Remove the ENTIRE package (all versions) — destructive, rarely needed
npm unpublish <package> --force
```

### Unpublish Failed? Alternatives

```
npm unpublish failed
├── "cannot unpublish" (>72h) → deprecate instead:
│   npm deprecate <pkg>@<ver> "Broken, use <new-ver>"
├── "has dependents" → you cannot unpublish while others depend on it
│   └── deprecate instead, or contact npm support
├── E403 → check auth: npm whoami, and OTP: --otp=<CODE>
└── E404 → package or version does not exist (already removed?)
    └── npm view <pkg> versions   # confirm what's published
```

### Deprecation (the safe alternative)

Deprecated versions **still installable** but show a warning. This is almost always preferred over unpublishing.

```bash
# Deprecate one version
npm deprecate <package>@<version> "Reason: use X.Y.Z instead"

# Deprecate the entire package
npm deprecate <package> "This package is no longer maintained"

# Un-deprecate (clear the message)
npm deprecate <package>@<version> ""
```

## Workflow 3: Update Version + Publish

For your own package — code is updated, ready to upload a new version.

### Step 1 — Pre-flight

```bash
# Auth & registry
npm whoami                                # must succeed
npm config get registry                   # verify target registry

# Check current local version
PKGNAME=$(node -p "require('./package.json').name")
PKGVER=$(node -p "require('./package.json').version")
echo "Publishing: ${PKGNAME}@${PKGVER}"

# Check this version doesn't already exist on npm
npm view "${PKGNAME}@${PKGVER}" version 2>/dev/null \
  && echo "ERROR: ${PKGVER} already on npm — bump version first" \
  || echo "OK: version is available"

# Review what will be uploaded
npm publish --dry-run
```

### Step 2 — Bump version (if not already done)

If `package.json` version is already updated, **skip this step**.

```bash
# Choose one:
npm version patch                         # 1.0.0 → 1.0.1 (bug fix)
npm version minor                         # 1.0.0 → 1.1.0 (new feature)
npm version major                         # 1.0.0 → 2.0.0 (breaking change)

# If git working tree is dirty and npm version refuses:
npm version patch --no-git-tag-version    # only bump package.json, skip git commit/tag
```

### Step 3 — Build (if applicable)

```bash
# If the project has a build step (TypeScript, bundler, etc.)
npm run build
```

Skip if the package publishes source directly or `prepublishOnly` handles the build.

### Step 4 — Publish

```bash
# Standard publish
npm publish

# Scoped package (@org/pkg) — first time MUST include --access public
npm publish --access public

# If account has 2FA enabled (most accounts do):
npm publish --otp=<CODE>
# The agent should ask the user for the OTP code before running this command.
# Example: "Your npm account requires 2FA. Please provide your OTP code."
```

### Step 5 — Verify + Git push

```bash
# Confirm it's live
npm view "${PKGNAME}@${PKGVER}" version

# Push version commit and tag to git (if npm version created them)
git push --follow-tags
```

### Publish Failed? Diagnose

```
npm publish failed
├── ENEEDAUTH → npm login (or set NPM_TOKEN for CI)
├── E403 Forbidden
│   ├── "you must verify your email" → check npm email inbox
│   ├── "requires OTP" → re-run with --otp=<CODE> (ask user for code)
│   ├── scoped package first time → add --access public
│   └── name taken → npm view <name> to confirm, pick a different name
├── EPUBLISHCONFLICT (version already exists)
│   └── bump version: npm version patch → npm publish
├── E400 "Invalid version"
│   └── version must be pure semver: 1.2.3 (not v1.2.3)
├── E402 "Payment Required"
│   └── private scoped packages need a paid npm plan, or use --access public
├── ETARGET / network error
│   └── check: npm config get registry, try --registry https://registry.npmjs.org
└── "prepublishOnly" script failed
    └── fix the build/test error first, then retry npm publish
```

## Workflow 4: Beta / Prerelease

```bash
# 1. Bump to prerelease
npm version prerelease --preid=beta   # 1.0.0 → 1.0.1-beta.0
# (subsequent runs: 1.0.1-beta.0 → 1.0.1-beta.1 → ...)

# 2. Publish with beta tag (IMPORTANT: --tag prevents overwriting "latest")
npm publish --tag beta

# 3. Users install via:
#    npm install <pkg>@beta

# 4. When ready to promote beta to stable:
npm dist-tag add <package>@<beta-version> latest
```

## Workflow 5: Fix a Broken Release

```bash
# Option A: Deprecate + publish fix (preferred, always works)
npm deprecate <pkg>@<bad-ver> "Broken build, use <new-ver>"
npm version patch
npm publish

# Option B: Unpublish + re-publish (only within 72 hours)
npm unpublish <pkg>@<bad-ver>
npm version patch
npm publish

# Option C: Overwrite same version (NOT possible on npm — versions are immutable)
# You MUST bump the version. There is no way around this.
```

## Reference

### Version Management

| Command | Effect | Use case |
|---------|--------|----------|
| `npm version patch` | 1.0.0 → 1.0.1 | Bug fixes |
| `npm version minor` | 1.0.0 → 1.1.0 | New features (backward-compatible) |
| `npm version major` | 1.0.0 → 2.0.0 | Breaking changes |
| `npm version prerelease --preid=beta` | 1.0.0 → 1.0.1-beta.0 | Pre-release |
| `npm version 2.3.4` | → 2.3.4 | Set explicit version |

```bash
# View published versions
npm view <pkg> versions --json
npm view <pkg>@latest version
npm view <pkg>@beta version

# View dist-tags
npm dist-tag ls <pkg>

# Manage tags
npm dist-tag add <pkg>@<ver> <tag>
npm dist-tag rm <pkg> <tag>
```

### Access Control

```bash
# Scoped package visibility
npm access set status=public <package>
npm access set status=private <package>

# Owners
npm owner ls <package>
npm owner add <username> <package>
npm owner rm <username> <package>
```

### Package Inspection

```bash
npm view <pkg>                     # all metadata
npm view <pkg> versions --json     # all published versions
npm view <pkg> dist.tarball        # download URL
npm pack                           # create local .tgz for inspection
npm publish --dry-run              # preview what would be published
```

### Authentication for CI/CD

```bash
# Set token (CI environments)
npm config set //registry.npmjs.org/:_authToken=${NPM_TOKEN}

# Or via environment variable (preferred for CI)
export NPM_TOKEN=<your-token>
# Then in .npmrc: //registry.npmjs.org/:_authToken=${NPM_TOKEN}
```

### Registry Configuration

```bash
npm config get registry                # check current
npm config set registry https://registry.npmjs.org   # reset to default

# Scoped registry (e.g., GitHub Packages)
npm config set @myorg:registry https://npm.pkg.github.com

# One-off publish to specific registry
npm publish --registry https://registry.npmjs.org
```

### package.json Essentials

Before publishing, ensure these fields are set:

```json
{
  "name": "@scope/pkg-name",
  "version": "1.0.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "files": ["dist"],
  "scripts": {
    "build": "tsc",
    "prepublishOnly": "npm run build && npm test"
  },
  "license": "MIT"
}
```

**Critical:**
- `name` — unique on npm; use `@scope/` prefix if needed
- `version` — must be semver (`1.2.3`, never `v1.2.3`)
- `files` — whitelist what gets published (safer than `.npmignore`)
- `prepublishOnly` — runs automatically before `npm publish`

### Quick Reference

| Task | Command |
|------|---------|
| Publish | `npm publish` |
| Publish scoped (first time) | `npm publish --access public` |
| Publish with OTP | `npm publish --otp=123456` |
| Version bump | `npm version [patch\|minor\|major]` |
| Deprecate | `npm deprecate pkg@ver "reason"` |
| Un-deprecate | `npm deprecate pkg@ver ""` |
| Unpublish version | `npm unpublish pkg@ver` |
| Unpublish all | `npm unpublish pkg --force` |
| Add dist-tag | `npm dist-tag add pkg@ver tag` |
| Remove dist-tag | `npm dist-tag rm pkg tag` |
| Dry run | `npm publish --dry-run` |
| View info | `npm view pkg` |
| List versions | `npm view pkg versions --json` |
| Check auth | `npm whoami` |
| Check registry | `npm config get registry` |
