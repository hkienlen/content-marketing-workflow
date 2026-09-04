# WordPress review gate

Date: 2026-09-04
Status: authoritative architecture contract

## Purpose

This contract defines the generic human validation gate for a prepared WordPress draft in the single installable Content / Marketing skill.

The generic gate is:

```text
WordPress OK
```

It intentionally does not name a page builder.

Legacy integration records may retain adapter-specific wording. Such wording is external project history only. Current workflow contracts and user-facing prompts must use `WordPress OK`.

## Meaning

`WordPress OK` means the user has reviewed the prepared WordPress draft in the presentation/editor environment relevant to that site and accepts its rendered/persisted presentation state.

Depending on the configured WordPress adapter/profile, that review may involve:

- Divi;
- Gutenberg/block editor;
- Elementor;
- Bricks;
- another supported presentation layer;
- a future adapter-specific editor/preview mechanism.

The generic capability must never hardcode one of those implementations into the name of the human gate.

## Separation from adapter-specific checks

Adapter-specific verification may still legitimately mention its technology.

Examples:

```text
Divi profile verified
Gutenberg blocks valid
Elementor presentation profile verified
```

Those are technical/profile checks.

The human workflow gate remains:

```text
WordPress OK
```

## Gate semantics

These states remain distinct:

```text
article editorial validation
!= final visual selection
!= GitHub integration
!= WordPress draft prepared/read back
!= WordPress OK
!= publication intent
!= publish_now
```

`WordPress OK` validates the prepared WordPress representation only.

It does not:

- request publication;
- create publication authorization;
- activate `wordpress.publish_enabled`;
- activate the Bridge `Article publication` permission;
- imply `publish_now`.

If publication is not in the requested workflow scope, the procedure may end successfully after `WordPress OK` with the article remaining a validated draft.

## Publication boundary

Only when publication is explicitly requested may the workflow proceed after `WordPress OK` to publication-specific capture/candidate/preflight and the independent exact `publish_now` gate.

## Compatibility and precedence

Historical execution evidence may retain the literal adapter-specific gate wording that was actually used at the time.

For current/future contracts, checklists, templates and user-facing prompts, `WordPress OK` is the generic gate name.
