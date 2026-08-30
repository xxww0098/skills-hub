---
name: npmjs-cli
description: >
  Publish, version, deprecate, unpublish, tag, and control access on the npm
  registry. Use when the user mentions npm publish, npm version, deprecate,
  unpublish, dist-tag, OTP/2FA publish, scoped package --access public,
  npm whoami, maintainers, or a broken npm release. Run this before any
  registry write.
---

# npmjs-cli

Registry writes. Confirm auth and the target registry before publishing.

```bash
npm --version
npm whoami                              # else: npm login
npm config get registry                 # public: https://registry.npmjs.org/
# wrong registry (cnpm / private):  npm publish --registry https://registry.npmjs.org
```

Ask the user for the OTP when 2FA is on. Do not hang on an interactive prompt
you cannot complete.

## Publish (or bump + publish)

Preflight — most failures are here:

```bash
PKGNAME=$(node -p "require('./package.json').name")
PKGVER=$(node -p "require('./package.json').version")
npm view "${PKGNAME}@${PKGVER}" version 2>/dev/null \
  && echo "ERROR: ${PKGVER} already on npm — bump first" \
  || echo "OK: version is available"
npm publish --dry-run                   # files + size
```

Bump only if `package.json` is still the already-published version:

```bash
npm version patch                       # 1.0.0 → 1.0.1
npm version minor                       # → 1.1.0
npm version major                       # → 2.0.0
npm version 1.2.4                       # explicit
# dirty tree:  npm version patch --no-git-tag-version
```

Build if the package ships compiled output and `prepublishOnly` does not.

```bash
npm publish                             # unscoped
npm publish --access public             # first publish of @scope/pkg
npm publish --otp=<CODE>                # 2FA
```

Then `npm view "${PKGNAME}@${PKGVER}" version` and `git push --follow-tags`
if `npm version` created a tag.

`package.json` must use pure semver (`1.2.3`, never `v1.2.3`). Prefer `files`
over `.npmignore`. First scoped publish without `--access public` is a 403.

## Publish failed

```
ENEEDAUTH            → npm login or NPM_TOKEN
E403 verify email    → confirm npm email
E403 requires OTP    → --otp=<CODE>
E403 scoped first    → --access public
E403 name taken      → npm view <name>, rename
EPUBLISHCONFLICT     → npm version patch && npm publish
E400 invalid version → strip the leading v
E402 payment         → paid private plan, or --access public
ETARGET / network    → --registry https://registry.npmjs.org
prepublishOnly fail  → fix build/test, retry
```

## Broken release

Versions are immutable. You cannot overwrite `1.2.3`.

Prefer deprecate + new patch (always allowed):

```bash
npm deprecate <pkg>@<bad> "Broken, use <new>"
npm version patch && npm publish
```

`npm unpublish <pkg>@<ver>` only within 72 hours and only if nothing depends
on it. After 72h, or with dependents: deprecate. Entire package:
`npm unpublish <pkg> --force` (rare, destructive).

Clear a deprecation with `npm deprecate <pkg>@<ver> ""`.

## Beta / dist-tags

```bash
npm version prerelease --preid=beta     # 1.0.0 → 1.0.1-beta.0
npm publish --tag beta                  # do not overwrite latest
# install: npm install <pkg>@beta
npm dist-tag add <pkg>@<ver> latest     # promote
npm dist-tag ls <pkg>
```

## Access, inspect, CI

```bash
npm access set status=public <package>
npm owner ls <package>
npm owner add <user> <package>
npm view <pkg> versions --json
npm pack                                # local tarball
```

CI: `export NPM_TOKEN=...` and
`//registry.npmjs.org/:_authToken=${NPM_TOKEN}` in `.npmrc`.
Scoped GitHub Packages: `npm config set @org:registry https://npm.pkg.github.com`.
