# Content Marketing Workflow

<p align="center">
  <img src="assets/repository-icon.png" alt="Content Marketing Workflow icon" width="180">
</p>

**Content Marketing Workflow** is the canonical source repository for the reusable Content Marketing Workflow Skill and its optional Codex plugin distribution.

Current version: `0.3.0`

## Distribution model

The workflow has one canonical Skill source and two supported distributions:

```text
content-marketing-workflow/
├── skills/content-marketing-workflow/       # canonical Skill source
├── plugins/content-marketing-workflow/      # Codex plugin distribution
├── tools/
├── tests/
└── .agents/plugins/marketplace.json
```

The Skill is the canonical reasoning/workflow boundary. The Codex plugin is a packaging/distribution envelope and must not develop a separate behavior model.

## Runtime prerequisites and compatibility

`/start` performs prerequisite discovery immediately and reports:

```text
READY
DEGRADED
BLOCKED
```

Central authority:

```text
skills/content-marketing-workflow/docs/architecture/runtime-compatibility-matrix.md
```

Current product rules:

- **GitHub repository access is mandatory.** Without a usable repository CMW is `BLOCKED`; conversation memory is not a substitute.
- **Online cloud-media storage is required for the complete media workflow.** Google Drive and Dropbox are implemented providers in 0.3.0; exactly one is active per project, with Google Drive recommended/default when both are operational.
- GitHub, WordPress and local filesystem are not automatic media-storage fallbacks.
- New users do not need to pre-install Google Drive or Dropbox before `/start`; when runtime plugin discovery is available CMW discovers eligibility/installability/connection state and guides setup.
- When the runtime cannot generate/edit images but cloud storage is available, CMW produces a complete external-generation prompt and resumes after the user returns/uploads the image.
- Without required verified final media, CMW does not degrade to image-less WordPress publication or text-only social publication.
- Current LinkedIn/Facebook automated publication depends on a verified WordPress-hosted SEO Workflow Bridge runtime.
- GitHub Actions is required for current unattended scheduled publication.
- Telegram remains optional and never changes publication truth.

The 0.3.0 release adds Dropbox as a first-class `cloud_media_storage` adapter while preserving provider-neutral media identity, publication gates and runtime-degradation behavior.

## Direct installation in ChatGPT

Tagged releases publish:

```text
content-marketing-workflow-<version>.skill
content-marketing-workflow-skill-<version>.zip
```

Upload the complete `.skill` artifact (preferred) or Skill ZIP, start a new chat and invoke `/start`.

Installing CMW does not itself grant GitHub, WordPress, cloud-storage or social-provider access. Onboarding detects/configures available dependencies. See `docs/chatgpt-direct-skill.md`.

## ChatGPT conversational execution

When required connected tools are available, CMW can run directly in ChatGPT without forcing Codex. Typical usage includes onboarding, repository/project inspection, article/social creation, visual creation/manual handoff, WordPress/social preparation/publication through explicit gates, and status/help projection.

The Skill must never claim an external write succeeded when the active runtime lacks the required tool/connection.

## Codex plugin distribution

Add marketplace:

```bash
codex plugin marketplace add <owner>/content-marketing-workflow --ref main
```

Install:

```bash
codex plugin add content-marketing-workflow@content-marketing-workflow
```

For local development:

```bash
codex plugin marketplace add .
codex plugin add content-marketing-workflow@content-marketing-workflow
```

## Canonical Skill and plugin mirror

Edit canonical Skill under:

```text
skills/content-marketing-workflow/
```

Synchronize mirror with:

```bash
python3 tools/sync-skill-mirror.py
```

CI compares the trees byte-for-byte.

## Build artifacts

Direct Skill:

```bash
python3 tools/build-skill.py
```

Codex plugin ZIP:

```bash
python3 tools/build-release.py --source-sha "$(git rev-parse HEAD)"
```

## Versioning

These values must stay synchronized:

```text
VERSION
skills/content-marketing-workflow/VERSION
plugins/content-marketing-workflow/skills/content-marketing-workflow/VERSION
plugins/content-marketing-workflow/.codex-plugin/plugin.json
```

Release notes are maintained in `CHANGELOG.md`. Tagged release automation publishes direct Skill artifacts and Codex plugin ZIP with SHA-256 checksums.

`SEO Workflow Bridge` keeps independent versioning.

## Safety boundary

Generic source/release artifacts must not contain user/project content, integration identities/configuration, live provider IDs, exact publication authorizations, credentials or user media. Runtime values belong to active durable project state or the external credential owner.
