# Runtime capability handoff completion - 0.2.1

Date: 2026-09-05
Status: implementation completion record

Source decision handoff:

```text
docs/runtime-capability-handoff-2026-09-05.md
```

## Why 0.2.1 exists

Version 0.2.0 introduced the central runtime compatibility model but was tagged before every downstream capability contract from the approved handoff had been aligned.

Version 0.2.1 is the completion patch. It does not change the approved product decisions; it finishes their propagation through the repository.

## Completion checklist

1. **Central runtime/integration compatibility contract** - complete (`runtime-compatibility-matrix.md`).
2. **`start` onboarding + direct ChatGPT runtime** - complete from 0.2.0 and retained.
3. **Provider-neutral cloud-media wording** - complete in media delivery/capability contracts; Google Drive remains sole implemented adapter, Dropbox future-only.
4. **Google Drive discovery/installability/connection expectations** - complete in start/runtime compatibility/Google Drive/direct-install contracts.
5. **Image-generation runtime detection + manual handoff** - complete in central runtime, article creation and social visual contracts.
6. **Media/article/WordPress/social contract alignment** - complete in 0.2.1.
7. **WordPress/SEO Workflow Bridge dependency for current automated social publication** - complete in central matrix plus social schedule/publish contracts.
8. **`/status` and `/help` compatibility projection** - complete from 0.2.0 and regression-covered.
9. **User-profile persistence model** - complete in 0.2.1 with optional non-secret `runtime_compatibility`; image-generation availability intentionally remains runtime-ephemeral/re-detected.
10. **Regression tests for fatal/degraded/optional behavior** - complete and expanded in 0.2.1 across downstream contracts.
11. **README/direct-install/changelog/versioning** - complete in 0.2.1.
12. **Canonical Skill / Codex plugin mirror synchronization + CI** - required before merge; PR must not merge unless repository CI passes.

## Preserved decisions

### Hard block

```text
no usable GitHub repository
=> BLOCKED
=> CMW does not continue as conversation-only workflow
```

### Cloud media

```text
Google Drive = implemented provider
Dropbox = future adapter
GitHub/WordPress/local filesystem = not media-storage fallbacks
```

### Missing media

```text
no required verified_final media
=> no WordPress preparation-for-publication/publication
=> no social publication
```

No image-less WordPress fallback and no text-only social fallback were introduced.

### WordPress dependency

Current automated LinkedIn/Facebook publication requires a verified WordPress-hosted SEO Workflow Bridge runtime.

### Image generation unavailable

When cloud media works but the current surface cannot generate/edit images:

```text
exact brief/policy
-> complete external-generation prompt
-> user generates externally
-> user returns/uploads result
-> CMW inspects/persists/reviews/finalizes
```

The prompt alone never represents a completed visual.

## 0.2.1 authoritative changes

Canonical Skill files aligned in this patch include:

```text
docs/architecture/google-drive-workspace.md
docs/architecture/media-delivery-architecture.md
docs/architecture/user-profile-data-contract.md
docs/architecture/schemas/user-profile.schema.json
docs/architecture/capabilities/README.md
docs/architecture/capabilities/seo-create-article.md
docs/architecture/capabilities/social-create-visual.md
docs/architecture/capabilities/social-schedule.md
docs/architecture/capabilities/social-publish.md
docs/architecture/capabilities/wordpress-prepare-article.md
docs/architecture/capabilities/wordpress-publish-article.md
```

Repository-level documentation/testing/version files include:

```text
docs/chatgpt-direct-skill.md
tests/test_runtime_compatibility.py
README.md
CHANGELOG.md
VERSION
```

The corresponding canonical Skill files must be byte-for-byte mirrored under:

```text
plugins/content-marketing-workflow/skills/content-marketing-workflow/
```

## Release condition

`v0.2.1` must be tagged only after:

- the completion PR is merged to `main`;
- CI passes, including canonical/mirror equality and runtime compatibility tests;
- all four version identities report `0.2.1`.
