# Content Marketing Workflow

**Content Marketing Workflow** is the canonical source repository for the Codex/OpenAI plugin `content-marketing-workflow`.

Current version: `0.1.0`

The repository follows the Codex repo/team marketplace layout:

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

## Install from the Git marketplace

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

Refresh the configured Git marketplace:

```bash
codex plugin marketplace upgrade content-marketing-workflow
```

Then reinstall/refresh the plugin from the same marketplace when required by the active Codex version:

```bash
codex plugin add content-marketing-workflow@content-marketing-workflow
```

## Canonical source

Corrections, evolutions, release preparation and versioning of the generic plugin are performed in this repository.

Real integration environments and user/project state are deliberately separate from the generic product source and are never sources for a future generic release.

## Repository versus release package

The marketplace manifest is repository-level installation metadata. The installable plugin source lives under `plugins/content-marketing-workflow/`.

`tools/build-release.py` creates the clean standalone release ZIP from the plugin source directory plus the release-level README/VERSION files and generates `SOURCE.json` with the exact canonical commit SHA used for that build.

Repository-only files such as the marketplace manifest, tests, CI, migration notes and development instructions are not copied into the standalone plugin ZIP.

## Versioning

The plugin follows Semantic Versioning. `VERSION` and `plugins/content-marketing-workflow/.codex-plugin/plugin.json` must contain the same version. Release notes are maintained in `CHANGELOG.md`.

`SEO Workflow Bridge` is bundled as a WordPress companion resource and keeps its own independent versioning.

## Safety boundary

Generic source and release artifacts must not contain user/project content, integration identities/configuration, live provider IDs, exact publication authorizations, credentials or user media. Runtime values belong to the active user's durable project state or external credential owner.
