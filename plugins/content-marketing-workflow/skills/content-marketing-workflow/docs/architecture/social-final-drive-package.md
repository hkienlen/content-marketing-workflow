# Social final cloud package contract

Date: 2026-09-05
Status: current architecture contract

## Purpose

When a supported cloud-media provider is used as the durable workspace for a social post's visual assets, the validated post text must also be preserved alongside the final visual in the same private `final/` package.

The historical filename of this contract is retained for compatibility, but the contract is provider-neutral from CMW 0.3.0 onward.

## Mandatory invariant

For every social post using the selected cloud-media provider for proposals/final media:

```text
human approves final post text
AND
human selects/approves one visual
-> normalize/verify selected visual
-> store visual in the post's private final/ folder
-> create/update one provider-appropriate copy/paste-ready text artifact in the SAME final/ folder
-> verify both objects are recoverable
-> persist their stable provider identities/references in GitHub
```

A post is not fully finalized for scheduling readiness until both the final visual and the provider-appropriate final text artifact exist and are verified.

## Provider-specific final text artifact

### Google Drive

Create/update one native Google Doc containing only the exact validated publishable post text.

### Dropbox

Create/update one UTF-8 plain-text file:

```text
<post_id>-<descriptive-slug>.txt
```

The file body contains only the exact validated publishable post text, preserving intended paragraph breaks. UTF-8 without workflow metadata is required so the user can open/select all/copy/paste directly.

Do not silently convert the Dropbox text artifact into Markdown with headings/front matter or any other wrapper that changes the copy/paste-ready body.

## Canonical provider-neutral layout

```text
<provider-root>/<site-domain>/social/<post_id>-<descriptive-slug>/
├── proposals/
│   └── ... review rounds ...
└── final/
    ├── <post_id>-<descriptive-slug>.<png|jpg>
    └── <provider-appropriate final text artifact>
```

Both objects remain private.

## Final text content: publishable text only

The final text artifact body must contain **only the exact final publishable post copy**, preserving intended paragraph breaks.

Forbidden inside the body:

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

The provider object/file name may remain descriptive for retrieval. The restriction applies to the body.

Do not silently alter the validated publishable copy while creating/updating the final text artifact.

## Idempotency and revisions

- create one canonical final text artifact per final post package;
- persist its provider + stable provider identity/reference in GitHub;
- on resume, reuse/update that exact canonical artifact instead of creating duplicates;
- if the user explicitly reopens and changes an approved post before publication, update the canonical artifact only after the revised text is approved again;
- superseded historical text may remain in GitHub history, but the canonical `final/` artifact body must contain only the currently approved publishable post text;
- a provider change requires explicit migration/recreation and verification rather than reinterpreting the previous provider identity.

## Durable GitHub record

Provider-neutral conceptual record:

```yaml
final_post_document:
  provider: google_drive|dropbox
  document_id: <native Google Doc id or Dropbox file identity/reference>
  title: <provider object/file title>
  folder_id: <same final folder identity/reference that contains the visual>
  body_policy: publishable_text_only
  format: google_doc|text_plain_utf8
  status: verified_final
```

GitHub remains the workflow/state authority; the cloud artifact is the copy/paste-ready human-readable final post stored with the media package.

## Completion and blocking behavior

```text
visual verified_final
!=
complete final cloud package
```

Completion requires:

```text
visual verified_final
AND
final text approved
AND
provider-appropriate final text artifact stored in same final/ folder
AND
artifact body equals exact approved publishable post text and contains no non-publishable metadata
AND
provider identity/reference persisted/re-read
```

If final text artifact creation, placement, or exact-text verification fails, report the post as finalization-incomplete rather than silently proceeding to scheduling readiness.

## Relationship to other contracts

Read together with:

- `docs/architecture/runtime-compatibility-matrix.md`
- `docs/architecture/google-drive-workspace.md`
- `docs/architecture/dropbox-workspace.md`
- `docs/architecture/social-workflow.md`
- `docs/architecture/social-execution-checklist.md`
- `docs/architecture/social-post-review-loop.md`
- `docs/architecture/capabilities/social-create-post.md`
- `docs/architecture/capabilities/social-create-visual.md`

This contract does not change scheduling or publication authorization gates.
