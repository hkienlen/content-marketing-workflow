# Content Marketing Workflow

<p align="center">
  <img src="assets/repository-icon.png" alt="Content Marketing Workflow icon" width="180">
</p>

**Content Marketing Workflow** is the canonical source repository for the reusable Content Marketing Workflow Skill and its optional Codex plugin distribution.

Current version: `0.1.2`

## Distribution model

The workflow now has one canonical Skill source and two supported distributions:

```text
content-marketing-workflow/
├── skills/
│   └── content-marketing-workflow/          # canonical Skill source
│       ├── SKILL.md
│       ├── VERSION
│       └── supporting resources
├── plugins/
│   └── content-marketing-workflow/          # Codex plugin distribution
│       ├── .codex-plugin/plugin.json
│       ├── assets/
│       └── skills/
│           └── content-marketing-workflow/  # byte-for-byte mirror of canonical Skill
├── tools/
│   ├── build-skill.py
│   ├── build-release.py
│   └── sync-skill-mirror.py
├── tests/
└── .agents/plugins/marketplace.json
```

The **Skill is the canonical reasoning/workflow boundary**. The Codex plugin is an optional packaging/distribution envelope and must not develop a separate behavior model.

SEO, article, visual, WordPress, social, scheduling, publication, verification and notification behaviors remain internal capabilities of this single Skill.

## Direct installation in ChatGPT

For users who can upload Skills in ChatGPT, this is the preferred ChatGPT distribution.

Tagged releases publish:

```text
content-marketing-workflow-<version>.skill
content-marketing-workflow-skill-<version>.zip
```

Both files contain the complete canonical Skill folder with `SKILL.md` and its supporting resources.

In ChatGPT, use the Skills interface (`Create` → `Upload from your computer`) and upload the `.skill` artifact, or the Skill ZIP when appropriate. Uploading only `SKILL.md` is possible in interfaces that support it, but the complete package is recommended because this workflow relies on supporting contracts and scripts.

After installation, start a new chat and invoke the Skill or use:

```text
/start
```

The Skill can then initialize or resume project onboarding. Installing a Skill does **not** itself grant GitHub, WordPress, cloud-storage or social-provider access; external operations use only the tools/connections actually available in the active ChatGPT conversation.

See `docs/chatgpt-direct-skill.md` for the direct-install and update guide.

## ChatGPT conversational execution

The workflow is intentionally usable directly in ChatGPT when the required connected tools are available. Repository work does not automatically require Codex.

Typical direct-ChatGPT usage includes:

- `/start` onboarding and durable project configuration;
- inspection of an existing/new project repository when GitHub tools are connected;
- selective migration of articles, social posts and related assets from an older project repository;
- article planning, drafting, review and update;
- social-series planning, post creation and review;
- WordPress/social preparation and publication only through their explicit authorization gates.

The Skill must not claim an external write succeeded when the active conversation does not expose the required connection/tool.

## Codex plugin distribution

The Codex plugin remains available for users who want marketplace installation or Codex repository execution.

Add the repository as a Codex marketplace:

```bash
codex plugin marketplace add <owner>/content-marketing-workflow --ref main
```

Install the plugin:

```bash
codex plugin add content-marketing-workflow@content-marketing-workflow
```

Verify discovery:

```bash
codex plugin marketplace list
codex plugin list --marketplace content-marketing-workflow
```

For local development:

```bash
codex plugin marketplace add .
codex plugin add content-marketing-workflow@content-marketing-workflow
```

The CI smoke test validates this Codex installation path independently from direct Skill packaging.

## Canonical Skill and plugin mirror

Edit the canonical Skill under:

```text
skills/content-marketing-workflow/
```

Then synchronize the Codex plugin mirror with:

```bash
python3 tools/sync-skill-mirror.py
```

CI compares the two trees byte-for-byte and fails if they diverge.

This prevents ChatGPT and Codex behavior from becoming separate implementations.

## Build artifacts

Build the direct ChatGPT Skill artifacts:

```bash
python3 tools/build-skill.py
```

Build the standalone Codex plugin ZIP:

```bash
python3 tools/build-release.py --source-sha "$(git rev-parse HEAD)"
```

The two builders coexist in `build/`; neither builder deletes the other's artifacts.

## Branding

The canonical repository artwork is stored in `assets/repository-icon.png`.

The Codex plugin uses:

- `plugins/content-marketing-workflow/assets/icon.png` for compact plugin/composer views;
- `plugins/content-marketing-workflow/assets/logo.png` for larger plugin presentation surfaces.

The plugin manifest references those assets through `interface.composerIcon` and `interface.logo`. The human-readable developer name is `Hervé Kienlen`.

## Versioning

The project follows Semantic Versioning. These values must stay synchronized:

```text
VERSION
skills/content-marketing-workflow/VERSION
plugins/content-marketing-workflow/skills/content-marketing-workflow/VERSION
plugins/content-marketing-workflow/.codex-plugin/plugin.json
```

Release notes are maintained in `CHANGELOG.md`.

Tagged release automation publishes both the direct Skill artifacts and the Codex plugin ZIP with SHA-256 checksum files.

`SEO Workflow Bridge` is bundled as a WordPress companion resource and keeps its own independent versioning.

## Safety boundary

Generic source and release artifacts must not contain user/project content, integration identities/configuration, live provider IDs, exact publication authorizations, credentials or user media. Runtime values belong to the active user's durable project state or external credential owner.

A project repository is separate from this generic product repository. `/start` may initialize project-specific state in the project repository, but it must never copy generic product source, release tooling or credentials into that project merely because they are available.
