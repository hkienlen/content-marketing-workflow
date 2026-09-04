# Repository Agent Instructions

## Authority

This repository is the **canonical source of the generic Content Marketing Workflow Skill and its optional Codex plugin distribution**.

All generic product corrections, evolutions, packaging changes and versioning must be developed here. Separate integration environments may validate real user/project state, but product changes discovered there must be ported back here through a normal branch/PR before release.

## Product architecture

- canonical Skill source: `skills/content-marketing-workflow`;
- direct ChatGPT Skill package manifest: `skill-package-manifest.json`;
- Codex marketplace manifest: `.agents/plugins/marketplace.json`;
- marketplace name: `content-marketing-workflow`;
- Codex plugin source root: `plugins/content-marketing-workflow`;
- plugin manifest: `plugins/content-marketing-workflow/.codex-plugin/plugin.json`;
- plugin Skill mirror: `plugins/content-marketing-workflow/skills/content-marketing-workflow`;
- display name: `Content Marketing Workflow`;
- internal capability names are not separate installable skills;
- `SEO Workflow Bridge` is a bundled WordPress companion and retains independent versioning.

The canonical Skill source is authoritative for workflow behavior. The plugin Skill mirror must remain byte-for-byte identical and exists only because the Codex plugin layout needs the Skill under the plugin source directory. Use `python3 tools/sync-skill-mirror.py` after editing the canonical Skill. CI must fail on drift.

The Codex plugin continues to follow the supported repo/team marketplace convention: marketplace metadata stays at repository root, while installable plugin source stays under `plugins/<plugin-name>/`. Do not move the plugin manifest back to repository root.

Direct ChatGPT distribution is built from the canonical `skills/content-marketing-workflow/` folder and does not depend on workspace plugin-marketplace administration. The Skill itself never grants external tool access; runtime capabilities depend on the tools/connections available in the active conversation.

## Development workflow

1. Branch from current `main`.
2. Make the smallest coherent product change.
3. Edit workflow behavior only in `skills/content-marketing-workflow/`.
4. Run `python3 tools/sync-skill-mirror.py` whenever canonical Skill files change.
5. Update contracts/docs/tests when behavior changes.
6. Keep `VERSION`, canonical Skill `VERSION`, plugin Skill mirror `VERSION` and `plugins/content-marketing-workflow/.codex-plugin/plugin.json` synchronized.
7. Run `python3 tests/test_repository.py`.
8. Run `python3 tools/build-skill.py` to validate direct ChatGPT Skill packaging.
9. Run `python3 tools/build-release.py --source-sha <40-hex-sha>` to validate Codex plugin packaging.
10. Validate marketplace discovery/install through the CI Codex smoke test when installation metadata or plugin layout changes.
11. When distribution behavior changes, keep `README.md`, `docs/chatgpt-direct-skill.md` and Codex marketplace documentation aligned with the supported surfaces.
12. Open a PR, require green CI, then merge.
13. Build releases from an exact merged `main` SHA only.

Routine GitHub mechanics are implementation plumbing; business/content publication gates defined by the Skill remain authoritative.

## Generic-data boundary

Never commit or package:

- user/project strategy, articles, posts or live workflow state;
- site/account/provider IDs tied to one user;
- credentials, tokens, secrets or private keys;
- user media or source-user assets;
- exact publication authorizations or live publication evidence;
- integration-specific profile names, hostnames, URLs or configuration as generic defaults.

Publisher/developer metadata in the plugin manifest is legitimate product metadata and is not user runtime data.

## Direct Skill boundary

The direct Skill package must:

- contain the canonical `SKILL.md` and all supporting resources needed by the workflow;
- carry a Skill `VERSION` synchronized with repository `VERSION`;
- preserve normal readable file permissions in packaged ZIP metadata;
- not contain repository-only CI, release or product-development files outside the Skill folder;
- not imply that installing the Skill grants GitHub, WordPress, storage or social-provider permissions.

## Marketplace boundary

`.agents/plugins/marketplace.json` is Codex repository-level discovery/import metadata and must:

- expose exactly the canonical plugin name;
- use a local source path under `./plugins/`;
- point at the same plugin source validated by packaging tests;
- include Codex installation/authentication policy and category where supported;
- remain outside the standalone plugin release ZIP.

## Release/versioning

Use Semantic Versioning.

- patch: backwards-compatible bug fixes, packaging fixes or contract corrections;
- minor: backwards-compatible new capabilities/features;
- major: breaking behavior/schema/package changes.

Update `CHANGELOG.md` for every released version. Do not edit a released artifact in place; create a new version from a new canonical SHA.

Tagged releases publish both direct ChatGPT Skill artifacts and the Codex plugin ZIP, each with a SHA-256 checksum.
