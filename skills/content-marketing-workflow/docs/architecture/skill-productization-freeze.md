# Productization and release freeze

Date: 2026-09-04
Status: normative release contract

## Historical provenance boundary

The initial 0.1.0 productization predates this canonical repository. Detailed migration provenance is retained only in repository-only migration/history files and is intentionally excluded from the installable plugin payload.

Installable releases must expose only their canonical repository identity and exact canonical source SHA through `SOURCE.json`.

## Canonical release sequence

```text
canonical repository main
-> dedicated change branch
-> update code/contracts/docs/tests/version as required
-> green canonical CI
-> merge
-> green CI on resulting main SHA
-> build clean ZIP from that exact SHA
-> generated SOURCE.json records that canonical SHA
-> publish/version artifact
```

## Freeze invariants

- future generic releases are sourced only from this canonical repository;
- user/project state and pilot evidence remain outside the canonical repository;
- historical pilot repository identity/provenance remains outside the installable payload;
- raw credentials remain in external credential owners;
- one plugin contains one primary skill with multiple internal capabilities;
- release assembly follows the root `plugin-package-manifest.json`;
- the primary-skill payload remains governed by `docs/architecture/skill-package-manifest.json`;
- a released artifact is immutable; a later correction requires a new Semantic Version and a new canonical source SHA.

## Acceptance

A release freeze is accepted only when:

1. branch/PR CI is green;
2. the change is merged;
3. CI on the resulting `main` SHA is green;
4. `tools/build-release.py` builds successfully from that exact SHA;
5. the ZIP passes integrity and repository-boundary tests;
6. generated `SOURCE.json.source_commit_sha` equals the exact canonical `main` SHA.
