# Content Marketing Workflow

**Content Marketing Workflow** is the canonical source repository for the ChatGPT/Codex plugin `content-marketing-workflow`.

Current version: `0.1.0`

The repository follows the supported repo/team marketplace layout:

```text
content-marketing-workflow/
├── .agents/
│   └── plugins/
│       └── marketplace.json
├── plugins/
│   └── content-marketing-workflow/
│       ├── .codex-plugin/
│       │   └── plugin.json
│       └── skills/
│           └── content-marketing-workflow/
│               └── SKILL.md
├── tests/
└── tools/
```

The plugin contains one primary skill. SEO, article, visual, WordPress, social, scheduling, publication, verification and notification behaviors remain internal capabilities of that single skill.

## ChatGPT Web workspace import

The same repository marketplace can be imported directly by eligible ChatGPT workspace administrators. No separate Web plugin package, Apps SDK wrapper or MCP server is required merely to distribute this skill-only plugin.

In ChatGPT Web:

1. Open `Workspace settings`.
2. Open `Plugins`.
3. Select `Add`, then `Import marketplace`.
4. In `Source`, enter the repository URL for this repository. Use the repository URL only, not a branch or folder URL.
5. Leave `Path` empty because `.agents/plugins/marketplace.json` is at repository root.
6. Set `Branch, tag, or commit` to `main` for ongoing synchronization, or pin a tag/commit for an immutable import.
7. Select `Import marketplace` and authorize GitHub access when prompted.
8. Review the import result and open `Content Marketing Workflow`.
9. Set the workspace installation policy to `Available` or `Installed` as appropriate for eligible users/roles.

GitHub marketplace import is a workspace-admin capability. Repository policy values do not override ChatGPT workspace policies; installation/authentication are controlled by the workspace after import.

The base plugin is skill-only and does not require an app connection merely to install. Optional runtime integrations such as GitHub, Google Drive, WordPress or social publication remain subject to the actual connected tools, permissions and provider authorization available in the active ChatGPT workspace.

See `docs/chatgpt-web-marketplace.md` for the repository-maintainer guide.

## Install from the Git marketplace with Codex CLI

Add the repository as a Codex marketplace:

```bash
codex plugin marketplace add <owner>/content-marketing-workflow --ref main
```

Then install the plugin exposed by that marketplace:

```bash
codex plugin add content-marketing-workflow@content-marketing-workflow
```

Verify discovery and installation:

```bash
codex plugin marketplace list
codex plugin list --marketplace content-marketing-workflow
```

Start a new Codex thread after installation so newly installed skills and plugin surfaces are loaded cleanly.

## Local development install

From a checkout of this repository:

```bash
codex plugin marketplace add .
codex plugin add content-marketing-workflow@content-marketing-workflow
```

The CI smoke test performs this local marketplace installation with a pinned Codex CLI version in addition to repository/package validation.

## Upgrade

For Codex CLI, refresh the configured Git marketplace:

```bash
codex plugin marketplace upgrade content-marketing-workflow
```

Then reinstall/refresh the plugin from the same marketplace when required by the active Codex version:

```bash
codex plugin add content-marketing-workflow@content-marketing-workflow
```

For a ChatGPT Web workspace marketplace, GitHub synchronization is managed from the marketplace entry in `Workspace settings > Plugins`; automatic sync may be enabled and an administrator can request `Sync now` when needed.

## Canonical source

Corrections, evolutions, release preparation and versioning of the generic plugin are performed in this repository.

Real integration environments and user/project state are deliberately separate from the generic product source and are never sources for a future generic release.

## Repository versus release package

The marketplace manifest is repository-level installation metadata for both Codex marketplace discovery and eligible ChatGPT workspace import. The installable plugin source lives under `plugins/content-marketing-workflow/`.

`tools/build-release.py` creates the clean standalone release ZIP from the plugin source directory plus the release-level README/VERSION files and generates `SOURCE.json` with the exact canonical commit SHA used for that build.

Repository-only files such as the marketplace manifest, tests, CI, migration notes and development instructions are not copied into the standalone plugin ZIP.

## Versioning

The plugin follows Semantic Versioning. `VERSION` and `plugins/content-marketing-workflow/.codex-plugin/plugin.json` must contain the same version. Release notes are maintained in `CHANGELOG.md`.

`SEO Workflow Bridge` is bundled as a WordPress companion resource and keeps its own independent versioning.

## Safety boundary

Generic source and release artifacts must not contain user/project content, integration identities/configuration, live provider IDs, exact publication authorizations, credentials or user media. Runtime values belong to the active user's durable project state or external credential owner.
