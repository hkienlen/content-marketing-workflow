# Content Marketing Workflow

**Content Marketing Workflow** is the canonical source repository for the OpenAI plugin `content-marketing-workflow`.

Current version: `0.1.0`

```text
content-marketing-workflow
├── .codex-plugin/plugin.json
└── skills/content-marketing-workflow/SKILL.md
```

The plugin contains one primary skill. SEO, article, visual, WordPress, social, scheduling, publication, verification and notification behaviors remain internal capabilities of that single skill.

## Canonical source

Corrections, evolutions, release preparation and versioning of the generic plugin are performed in this repository.

Real pilot/integration environments and user/project state are deliberately separate from the generic product source and are never sources for a future generic release.

## Repository versus release package

The repository contains development/release tooling in addition to the installable plugin payload. `tools/build-release.py` creates the clean release ZIP from an explicit allowlist and generates `SOURCE.json` with the exact canonical commit SHA used for that build.

The installable payload contains:

- `.codex-plugin/plugin.json`;
- `skills/content-marketing-workflow/**`;
- `README.md`;
- `VERSION`;
- generated `SOURCE.json`.

Repository-only files such as tests, CI, migration notes and development instructions are not copied into the installable ZIP.

## Versioning

The plugin follows Semantic Versioning. `VERSION` and `.codex-plugin/plugin.json` must contain the same version. Release notes are maintained in `CHANGELOG.md`.

`SEO Workflow Bridge` is bundled as a WordPress companion resource and keeps its own independent versioning.

## Safety boundary

Generic source and release artifacts must not contain user/project content, pilot identities/configuration, live provider IDs, exact publication authorizations, credentials or user media. Runtime values belong to the active user's durable project state or external credential owner.
