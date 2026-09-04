# Skill package boundary

Date: 2026-09-04
Status: normative architecture contract

## Purpose

The canonical repository contains the generic Content Marketing Workflow product source. The primary skill payload is rooted at:

```text
skills/content-marketing-workflow/
```

The relative allowlist is:

```text
skills/content-marketing-workflow/docs/architecture/skill-package-manifest.json
```

User/project runtime state, live pilot evidence and credentials must remain outside this canonical repository and outside every release artifact.

## Primary invariant

```text
generic product source + explicit release allowlist
!=
user/project runtime state or pilot environment
```

The release contains models, schemas, generic capability behavior, reusable runtime code and the WordPress companion source.

## Generic package content

Eligible categories include:

- capability contracts;
- user-profile and command schemas;
- generic help/onboarding using placeholders/profile lookups;
- generic orchestration/scheduler scripts;
- generic GitHub workflow templates/runtime workflows;
- SEO Workflow Bridge source;
- provider-independent architecture contracts;
- provider-specific generic procedures that contain no concrete user identity;
- the generic user-provided-image policy contract;
- the structured visual preference enums/inheritance model;
- the generic `visual-source-resolve` capability and deterministic visual-policy resolver;
- generic source-provenance/fidelity/treatment field definitions.

The generic package may know *how* to resolve and process user media. It must not ship the user's actual media, concrete visual preferences or content-specific source provenance.

## User/project data excluded from package

At minimum:

```text
user-data/**
strategy/**
articles/**
social/**
assets/**
work-context/**
prompts/work-items/**
docs/architecture/checkpoints/**
wordpress/config/**
wordpress/articles/**
wordpress/presentation/profiles/**
wordpress/prepare/manifests/**
wordpress/publish/candidates/**
```

These paths are runtime/project authorities and must not exist as concrete user data in the canonical generic repository or release package.

User/project-owned visual data also remains outside the generic package even when it is provider-backed rather than stored under a repository path. This includes:

```text
visual_preferences values chosen by the user
article/social/content-local visual overrides
source-user originals
chat-upload originals copied into durable provider storage
source provider folder/file IDs and direct links
source original filenames and source hashes tied to one user's assets
source roles/fidelity/treatment choices for a concrete content item
free-text ai_treatment_directive values
content-specific source provenance and final-media evidence
```

The package ships schemas/contracts for these fields, not the concrete values.

## User-provided media boundary

Normative generic behavior is defined by:

```text
docs/architecture/user-provided-images.md
docs/architecture/capabilities/visual-source-resolve.md
docs/architecture/capabilities/asset-ingest.md
scripts/visual-policy-resolve.py
```

Boundary rules:

- original user media is runtime/project data and is never embedded in the installable skill;
- Drive `source-user/` folders remain private project workspaces, not package resources;
- exact chat-upload bytes may be copied into the configured durable provider workspace when required, but never into the generic package merely because the skill ingested them;
- source provenance persisted with one article/post remains user/project state;
- generic role/fidelity/treatment enum definitions belong in the package;
- no user-specific treatment directive becomes a default constant in generic code;
- no pilot photo, product, portrait, filename, Drive ID or source hash may be used as a packaged example fixture unless replaced by synthetic/generic test data.

## Historical documentation

Pilot checkpoints, dated UI observations, live-validation evidence and conversation handoffs are valuable development history. They are user/project evidence rather than product payload and remain excluded unless deliberately rewritten into a generic contract.

A generic contract may cite a lesson learned from pilot work, but must express that lesson with placeholders/profile lookups rather than shipping the pilot identity/evidence.

## User-profile rule

The generic skill knows:

```text
docs/architecture/schemas/user-profile.schema.json
```

It does not ship:

```text
user-data/profile.json
```

On a real installation, onboarding creates/populates a user-owned profile instance. Future capability runs read those values rather than hard-coding them.

`visual_preferences` is therefore a schema-owned generic data shape whose concrete project/article/social values are runtime user data.

## Credential boundary

Neither side contains raw reusable provider credentials in Git:

```text
skill package -> no raw credentials
user/project Git data -> no raw credentials
external credential owner -> raw credential when required
```

The profile may contain safe lifecycle metadata such as credential type, secret owner, expiry/data-access-expiry timestamps and last observed validity.

## Runtime genericity

Packaged executable code must not contain pilot-specific constants such as:

- user name/slug;
- domain/site URL;
- repository owner/name/IDs;
- WordPress connection IDs;
- social member/Page IDs/URNs;
- social application/configuration IDs;
- Drive folder IDs;
- source-user folder IDs/links;
- user source filenames, source asset IDs or source hashes;
- concrete user visual preferences or treatment directives;
- exact pilot credential-expiry timestamps.

Runtime code obtains concrete values from the active profile, content-local state, exact source provenance, exact authorization record or connection profile as appropriate.

## CI guard

`tests/test_repository.py` in the canonical repository validates the release boundary, including:

1. all manifest entries exist;
2. excluded user/project roots are not accidentally included;
3. generic packaged text does not contain known pilot identity markers;
4. generic LinkedIn scheduler code no longer hard-codes a pilot connection ID;
5. repository-only development files are excluded from the release;
6. known pilot identity/configuration markers are rejected from generic payload files.

User-image-specific acceptance is additionally guarded by:

```text
tests/test_user_provided_images_contract.py
tests/test_skill_package_preproductization.py
```

Those checks ensure the generic user-image authorities are packaged while concrete user media/preferences/provenance remain runtime/project data.

This guard is intentionally conservative. If a new user-specific datum is discovered in generic package material, move it to user/project data or replace it with a schema/profile lookup rather than weakening the guard without architectural justification.

## Machine-maintained user profile state

The daily social connection health workflow is a deliberately narrow exception to normal PR-based project mutations. It may directly update `user-data/profile.json` on the default branch only for deterministic, non-secret operational health metadata produced from a read-only provider probe.

Allowed machine-maintained fields include:

```text
credential.last_observed_valid
credential.last_observed_at
credential.token_expires_at when learned from the credential owner
health.status
health.checked_at
health.credential_live_valid
health.expiry_basis
health.effective_expiry_at
health.days_until_expiry
health.scheduled_after_expiry
health.next_action
health.bridge_probe
```

It must not directly change:

- business/editorial strategy;
- visual_preferences or content-local visual overrides;
- source roles/fidelity/treatment directives;
- publishing-time preferences;
- standing publication-consent policy;
- remote account identity;
- content/post text or visuals;
- exact publication authorizations;
- raw credentials.

The workflow must use a normal non-force push and fail on conflicting repository changes rather than overwriting them.

## Completion criterion

The skill/user-data separation is considered enforced only when canonical repository CI and release-build validation pass on the change branch and on `main` after merge.

Any package-relevant change requires a new canonical `main` SHA for the next build. Release artifacts must record that exact source SHA in generated `SOURCE.json`.

## References

- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/persistence-contract.md`
- `docs/architecture/user-provided-images.md`
- `docs/architecture/schemas/user-profile.schema.json`
- `docs/architecture/capabilities/start.md`
- `docs/architecture/capabilities/visual-source-resolve.md`
- `docs/architecture/capabilities/asset-ingest.md`
- `docs/architecture/capabilities/social-connection-health.md`
