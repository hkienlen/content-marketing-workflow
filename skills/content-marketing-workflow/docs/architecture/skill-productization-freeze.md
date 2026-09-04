# Productization and release freeze

Date: 2026-09-04
Status: normative release contract

## Initial provenance

Content Marketing Workflow 0.1.0 was first generated and validated from the historical pilot/development source commit:

```text
hkienlen/herve-kienlen-seo@d89d1de1c2cbb47b68a75d3923003624e027cfc5
```

That SHA is historical provenance for 0.1.0 only. It is **not** the source for future generic releases.

## Canonical release sequence

```text
hkienlen/content-marketing-workflow main
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

- future generic releases are sourced only from `hkienlen/content-marketing-workflow`;
- user/project state and pilot evidence remain outside the canonical repository;
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
