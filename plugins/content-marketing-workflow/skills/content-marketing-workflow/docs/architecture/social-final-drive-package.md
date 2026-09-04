# Social final Google Drive package contract

Date: 2026-09-02
Status: current architecture contract

## Purpose

When Google Drive is used as the durable workspace for a social post's visual assets, the validated post text must also be preserved in Google Drive alongside the final visual.

This rule makes the private `final/` folder a complete human-usable delivery package for manual publication.

## Mandatory invariant

For every social post that uses Google Drive for proposals/final media:

```text
human approves final post text
AND
human selects/approves one visual
-> normalize/verify selected visual
-> store visual in the post's private final/ folder
-> create/update one native Google Doc containing ONLY the exact validated publishable post text
-> store that Google Doc in the SAME final/ folder
-> verify both objects are recoverable
-> persist their stable Drive identities in GitHub
```

A post is not fully finalized for scheduling readiness until both the final visual and the final Google Doc exist and are verified when this Drive-backed rule applies.

## Required Drive layout

```text
<drive-root>/<site-domain>/social/<post_id>-<descriptive-slug>/
├── proposals/
│   └── ... review rounds ...
└── final/
    ├── <post_id>-<descriptive-slug>.<png|jpg>
    └── <post_id> - <human-readable-title>   # native Google Doc
```

Both objects remain private.

## Google Doc content: publishable text only

The Google Doc body must contain **only the exact final publishable post copy**, preserving intended paragraph breaks.

Forbidden inside the Google Doc body:

- post ID;
- post title or concept label unless that title is itself literally part of the publishable post text;
- headings such as `Texte final validé`;
- workflow state or validation notes;
- selected visual label;
- source article URL;
- target platforms;
- validation date;
- ALT text;
- production metadata;
- any other non-publishable information.

The goal is operational: the user must be able to open the Google Doc, select all, copy, and paste directly into Facebook/LinkedIn without deleting anything first.

The Drive filename/title may remain descriptive for retrieval. The restriction applies to the **document body**.

Do not silently alter the validated publishable copy while creating/updating the Google Doc.

## Idempotency and revisions

- create one canonical Google Doc per final post package;
- persist its Drive `document_id`/URL in GitHub;
- on resume, reuse/update that exact canonical document instead of creating duplicates;
- if the user explicitly reopens and changes an approved post before publication, update the canonical Google Doc only after the revised text is approved again;
- superseded historical text may remain in GitHub history, but the canonical `final/` Google Doc body must contain only the currently approved publishable post text.

## Durable GitHub record

When applicable, persist at least:

```yaml
final_post_document:
  provider: google_drive
  document_id: <native Google Doc file id>
  title: <Drive title>
  folder_id: <same final folder that contains the visual>
  body_policy: publishable_text_only
  status: verified_final
```

GitHub remains the workflow/state authority; the Google Doc is the copy/paste-ready human-readable final post stored with the media package.

## Completion and blocking behavior

For a Drive-backed social post:

```text
visual verified_final
!=
complete final Drive package
```

Completion requires:

```text
visual verified_final
AND
final text approved
AND
final Google Doc stored in same final/ folder
AND
Google Doc body equals the exact approved publishable post text and contains no non-publishable metadata
AND
Google Doc identity persisted/re-read
```

If Google Doc creation, placement, or exact-text verification fails, report the post as finalization-incomplete rather than silently proceeding to scheduling readiness.

## Relationship to other contracts

Read together with:

- `docs/architecture/google-drive-workspace.md`
- `docs/architecture/social-workflow.md`
- `docs/architecture/social-execution-checklist.md`
- `docs/architecture/social-post-review-loop.md`
- `docs/architecture/capabilities/social-create-post.md`
- `docs/architecture/capabilities/social-create-visual.md`

This contract does not change scheduling or publication authorization gates.
