# Repository Agent Instructions

## Authority

This repository is the **canonical source of the generic Content Marketing Workflow plugin** for ChatGPT and Codex.

All generic product corrections, evolutions, packaging changes and versioning must be developed here. Separate integration environments may validate real user/project state, but product changes discovered there must be ported back here through a normal branch/PR before release.

## Product architecture

- marketplace manifest: `.agents/plugins/marketplace.json`;
- marketplace name: `content-marketing-workflow`;
- plugin source root: `plugins/content-marketing-workflow`;
- plugin manifest: `plugins/content-marketing-workflow/.codex-plugin/plugin.json`;
- display name: `Content Marketing Workflow`;
- one primary skill: `plugins/content-marketing-workflow/skills/content-marketing-workflow`;
- internal capability names are not separate installable skills;
- `SEO Workflow Bridge` is a bundled WordPress companion and retains independent versioning.

The repository must follow the supported repo/team marketplace convention: marketplace metadata stays at repository root, while installable plugin source stays under `plugins/<plugin-name>/`. Do not move the plugin manifest back to repository root and do not duplicate the plugin source in two locations.

The same marketplace manifest is the source for Codex marketplace discovery and eligible ChatGPT Web workspace GitHub import. Do not create a second Web-specific copy of the plugin. Do not add an Apps SDK wrapper or MCP server solely for Web distribution; introduce app/MCP architecture only when a genuine connected-tool/data/action requirement exists.

## Development workflow

1. Branch from current `main`.
2. Make the smallest coherent product change.
3. Update contracts/docs/tests when behavior changes.
4. Keep `VERSION` and `plugins/content-marketing-workflow/.codex-plugin/plugin.json` synchronized.
5. Run `python3 tests/test_repository.py`.
6. Run `python3 tools/build-release.py --source-sha <40-hex-sha>` when validating packaging.
7. Validate marketplace discovery/install through the CI Codex smoke test when installation metadata or plugin layout changes.
8. When distribution behavior changes, keep `README.md` and `docs/chatgpt-web-marketplace.md` aligned with the supported ChatGPT/Codex surfaces.
9. Open a PR, require green CI, then merge.
10. Build releases from an exact merged `main` SHA only.

Routine GitHub mechanics are implementation plumbing; business/content publication gates defined by the skill remain authoritative.

## Generic-data boundary

Never commit or package:

- user/project strategy, articles, posts or live workflow state;
- site/account/provider IDs tied to one user;
- credentials, tokens, secrets or private keys;
- user media or source-user assets;
- exact publication authorizations or live publication evidence;
- integration-specific profile names, hostnames, URLs or configuration as generic defaults.

Publisher/developer metadata in the plugin manifest is legitimate product metadata and is not user runtime data.

## Marketplace boundary

`.agents/plugins/marketplace.json` is repository-level discovery/import metadata and must:

- expose exactly the canonical plugin name;
- use a local source path under `./plugins/`;
- point at the same plugin source validated by packaging tests;
- include Codex installation/authentication policy and category where supported;
- remain outside the standalone plugin release ZIP.

For ChatGPT Web workspace import, workspace settings are authoritative for installation/authentication policy. Repository policy values must never be treated as a way to override workspace controls.

## Release/versioning

Use Semantic Versioning.

- patch: backwards-compatible bug fixes or contract corrections;
- minor: backwards-compatible new capabilities/features;
- major: breaking behavior/schema/package changes.

Update `CHANGELOG.md` for every released version. Do not edit a released artifact in place; create a new version from a new canonical SHA.
