# Installing Content Marketing Workflow directly as a ChatGPT Skill

Content Marketing Workflow ships a direct-install Skill bundle in addition to the Codex plugin package.

## Which artifact to use

For ChatGPT, prefer:

```text
content-marketing-workflow-<version>.skill
```

A ZIP variant is also produced:

```text
content-marketing-workflow-skill-<version>.zip
```

Both contain the complete canonical Skill folder. Use the complete package because CMW depends on supporting contracts/scripts/resources.

## ChatGPT installation

In ChatGPT:

1. Open **Skills**.
2. Select **Create**.
3. Select **Upload from your computer**.
4. Upload the `.skill` artifact (preferred) or Skill ZIP.
5. Review the scan result and install/enable the Skill.
6. Start a new chat and invoke the Skill or `/start`.

## Important: dependency installation is part of onboarding

A new user is **not expected to know or pre-install CMW integration plugins before installing CMW**.

`/start` performs prerequisite discovery immediately and reports:

```text
READY
DEGRADED
BLOCKED
```

CMW must determine availability from the actual runtime/plugin state, not by guessing from a ChatGPT plan label such as Free or Plus.

### GitHub

GitHub repository access is a hard prerequisite.

```text
no usable GitHub repository access
=> BLOCKED
=> CMW does not continue in conversation-only mode
```

If GitHub integration exists but is not connected/configured, onboarding guides that first.

### Cloud media storage

Online cloud media storage is required for the complete media workflow.

Providers implemented by the current version must be listed during onboarding. In 0.2.x:

```text
Google Drive: supported/current
Dropbox: future adapter, not selectable yet
```

When plugin discovery is available, `/start` should find Google Drive even when it is not installed, distinguish eligibility/installability/installation/connection state, propose installation when eligible, then guide connection/workspace verification.

If Google Drive is unavailable/ineligible and no other implemented provider exists, CMW enters `DEGRADED` mode. GitHub, WordPress and local filesystem are not media-storage fallbacks.

### Image generation/editing

CMW detects whether the active ChatGPT/Codex surface can generate/edit images.

If image generation is unavailable but cloud storage works, CMW uses a manual handoff:

1. generates a complete ready-to-use image prompt;
2. user runs it in an image-capable ChatGPT conversation or compatible image AI;
3. user returns/uploads the result;
4. CMW inspects and persists it to the configured cloud provider;
5. normal review/finalization resumes.

If cloud storage is unavailable, generated/returned images cannot become durable `verified_final` media and cannot unlock publication.

### WordPress and social publication

WordPress itself is optional for authoring. However the current automated publication architecture uses SEO Workflow Bridge hosted in WordPress.

Therefore without a verified WordPress + compatible Bridge runtime:

- no WordPress article preparation/publication;
- no current automated LinkedIn publication;
- no current automated Facebook Page publication.

Article/social authoring and GitHub persistence may continue when their own prerequisites are satisfied.

### No-image behavior

CMW deliberately does not degrade publication to text-only/image-less modes:

```text
required verified final media missing
=> no WordPress preparation-for-publication / publication
=> no social publication
```

## First project onboarding

The Skill contains no project-specific site names, repositories, identities, credentials or publication authorizations.

On first use `/start`:

1. verifies GitHub first;
2. discovers/configures implemented cloud-media provider(s);
3. detects image-generation/editing capability;
4. verifies WordPress/Bridge if WordPress or social publication is enabled;
5. verifies GitHub Actions/scheduler for unattended scheduling;
6. verifies enabled social adapters independently;
7. treats Telegram as optional notification capability;
8. reports exact feature availability/degradations.

When an older project repository is a migration source, migration is selective. Generic Skill source, product tests, release machinery, credentials and unrelated historical implementation material stay out of the project repository.

## ChatGPT versus Codex

Installing the Skill in ChatGPT does not force execution in Codex. If the active ChatGPT conversation exposes required connected tools, the workflow can execute there.

When a Codex surface lacks image generation but the user can generate images in a ChatGPT conversation, use the manual handoff above instead of pretending Codex generated the image.

The Codex plugin remains available for repository-heavy execution. Both distributions embed the same canonical Skill content and CI prevents drift.

## Updating

For a new release, install the new `.skill` artifact through the same Skills interface. Version identity is carried by packaged `VERSION` and synchronized with repository release/Codex plugin manifest.
