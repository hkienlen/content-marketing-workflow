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

Providers implemented since 0.3.0:

```text
Google Drive (`google_drive`): supported, recommended/default
Dropbox (`dropbox`): supported alternative
```

Exactly one provider is active per project. When both are operational, `/start` presents both choices and defaults to Google Drive unless the user selects Dropbox.

When plugin discovery is available, `/start` should discover both implemented providers even when they are not installed, distinguish eligibility/installability/installation/connection state, propose installation when eligible, then guide connection/workspace verification for the selected provider.

If neither Google Drive nor Dropbox is usable, CMW enters `DEGRADED` mode. GitHub, WordPress and local filesystem are not media-storage fallbacks.

Switching an existing project from one provider to the other is explicit migration work: provider-backed asset references are not interchangeable and exact hashes/provenance must be preserved.

### Visual identity, logo and permanent visual guidelines

Version 0.4.0 adds guided durable visual identity configuration.

When visuals are in scope, `/start` or `/visual configure` can ask for:

1. visual source/fidelity/treatment preferences;
2. an official logo, accepting one logo and preferably light/dark variants when available;
3. logo use for article images;
4. logo use for social-post images;
5. permanent global/article/social visual directives.

Article and social logo behavior are separate user preferences and must never be inferred from each other. For example, this is a valid permanent configuration:

```yaml
visual_identity:
  logo_policy:
    article: never
    social: always
```

Supported logo application values are:

```text
always
case by case (`auto`)
never
```

The user can inspect or change durable visual configuration with:

```text
/visual status
/visual configure
/visual logo
/visual guidelines
/logo
```

`/logo` is an alias for `/visual logo`.

Official logo files are retained privately in the selected cloud-media provider's brand workspace. CMW should use the exact verified official logo bytes during final composition; it must not ask an image generator to redraw or approximate a missing official logo merely to complete a visual.

Permanent natural-language visual directives may be stored in the user's project authority referenced by the profile, normally `strategy/visual-guidelines.md`. User creative directives override conflicting generic CMW creative defaults. A request explicitly limited to one article/post/image remains content-local and does not silently change the permanent project preference.

### Image generation/editing

CMW detects whether the active ChatGPT/Codex surface can generate/edit images.

If image generation is unavailable but cloud storage works, CMW uses a manual handoff:

1. generates a complete ready-to-use image prompt;
2. user runs it in an image-capable ChatGPT conversation or compatible image AI;
3. user returns/uploads the result;
4. CMW inspects and persists it to the selected cloud provider;
5. normal review/finalization resumes.

When logo application is required or allowed, the generation brief may reserve suitable brand space, but the official logo itself is composed afterward from the verified brand asset rather than recreated by the generator.

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

A required logo is part of final-media correctness: `logo_application=always` cannot become `verified_final` without an exact verified official logo asset.

## First project onboarding

The Skill contains no project-specific site names, repositories, identities, credentials, logos, visual directives or publication authorizations.

On first use `/start`:

1. verifies GitHub first;
2. discovers Google Drive and Dropbox;
3. selects and verifies exactly one cloud-media provider;
4. detects image-generation/editing capability;
5. progressively resolves visual preferences and visual identity when visuals are in scope;
6. verifies WordPress/Bridge if WordPress or social publication is enabled;
7. verifies GitHub Actions/scheduler for unattended scheduling;
8. verifies enabled social adapters independently;
9. treats Telegram as optional notification capability;
10. reports exact feature availability/degradations.

When an older project repository is a migration source, migration is selective. Generic Skill source, product tests, release machinery, credentials and unrelated historical implementation material stay out of the project repository.

Older profiles without `visual_identity` remain compatible. CMW reports visual identity as not yet explicitly configured rather than silently introducing a logo policy.

## ChatGPT versus Codex

Installing the Skill in ChatGPT does not force execution in Codex. If the active ChatGPT conversation exposes required connected tools, the workflow can execute there.

When a Codex surface lacks image generation but the user can generate images in a ChatGPT conversation, use the manual handoff above instead of pretending Codex generated the image.

The Codex plugin remains available for repository-heavy execution. Both distributions embed the same canonical Skill content and CI prevents drift.

## Updating

For a new release, install the new `.skill` artifact through the same Skills interface. Version identity is carried by packaged `VERSION` and synchronized with repository release/Codex plugin manifest.