# Repository Agent Instructions

## Authority

This repository is the **canonical source of the generic Content Marketing Workflow plugin**.

All generic product corrections, evolutions, packaging changes and versioning must be developed here. Do not use the former pilot repository `hkienlen/herve-kienlen-seo` as a source of generic plugin code. That repository may still be used for real integration validation and user/project state, but product changes discovered there must be ported back here through a normal branch/PR before release.

## Product architecture

- plugin name: `content-marketing-workflow`;
- display name: `Content Marketing Workflow`;
- one primary skill: `skills/content-marketing-workflow`;
- internal capability names are not separate installable skills;
- `SEO Workflow Bridge` is a bundled WordPress companion and retains independent versioning.

## Development workflow

1. Branch from current `main`.
2. Make the smallest coherent product change.
3. Update contracts/docs/tests when behavior changes.
4. Keep `VERSION` and `.codex-plugin/plugin.json` synchronized.
5. Run `python3 tests/test_repository.py`.
6. Run `python3 tools/build-release.py --source-sha <40-hex-sha>` when validating packaging.
7. Open a PR, require green CI, then merge.
8. Build releases from an exact merged `main` SHA only.

Routine GitHub mechanics are implementation plumbing; business/content publication gates defined by the skill remain authoritative.

## Generic-data boundary

Never commit or package:

- user/project strategy, articles, posts or live workflow state;
- site/account/provider IDs tied to one user;
- credentials, tokens, secrets or private keys;
- user media or source-user assets;
- exact publication authorizations or live publication evidence;
- pilot-specific profile names, hostnames, URLs or configuration as generic defaults.

Publisher/developer metadata in `.codex-plugin/plugin.json` is legitimate product metadata and is not user runtime data.

## Release/versioning

Use Semantic Versioning.

- patch: backwards-compatible bug fixes or contract corrections;
- minor: backwards-compatible new capabilities/features;
- major: breaking behavior/schema/package changes.

Update `CHANGELOG.md` for every released version. Do not edit a released artifact in place; create a new version from a new canonical SHA.
