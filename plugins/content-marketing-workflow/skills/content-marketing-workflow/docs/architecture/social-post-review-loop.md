# Social post combined review loop

Date: 2026-09-06
Status: current architecture contract

## Purpose

This contract defines the mandatory human-review loop for a social post produced by `/social create` or `/social create free`.

It supports two visual review shapes after `visual-source-resolve` and `social-create-visual`:

```text
A) generated/materially transformed
write post -> review-ready A/B/C -> combined review

B) verified exact user source (`use_as_is`)
write post -> exact compliant source/final candidate -> combined review
```

A visual package displayed without the post text and explicit guidance is incomplete.

## Precondition: visual source and brand readiness already resolved

Before combined review, `visual-source-resolve` must have produced a truthful allowed state and `social-create-visual` must have produced a **review-ready** visual package.

For generated/materially transformed visuals, raw/base generator outputs are not automatically review candidates.

When effective `logo_application=always`:

- every selectable A/B/C must already contain the exact verified official logo by deterministic composition;
- its branded output hash must be bound to the frozen `contract_revision`;
- the clean base must have passed the no-generated-project-branding inspection;
- `scripts/visual-review-gate.py` or equivalent evidence validation must pass before the combined review is called durable/selectable.

An unbranded base or a visual containing generated/unverified project branding is never part of the normal **review package**. A runtime may nevertheless render a generator result transiently as an unavoidable tool-side effect. That visibility is not a review presentation: do not label the base A/B/C, do not ask the user to validate/choose it, and do not attach durable selection or combined approval to it. Continue automatically until the branded review-ready package exists. Explicit debug inspection remains allowed, with the same no-approval semantics.

## First review package

The first normal review contains in the same response:

1. exact `post_id` and concept/function;
2. complete publishable master text;
3. compliant visual package;
4. concise visual role/difference notes when useful;
5. explicit guidance telling the user what can be validated/revised.

### Transient tool output is not a review gate

A conversational surface may display raw generated bases before CMW can brand/package them. Those displays are implementation/tool output only. They do not count toward the “exactly three review-ready A/B/C” requirement and must not create an extra human interaction. The first requested visual decision remains the branded A/B/C package.

### Generated/materially transformed package

Must show exactly three persisted/recoverable **review-ready** identities:

```text
Visual A
Visual B
Visual C
```

For `logo_application=always`, these are the officially branded derivatives, not their clean bases.

### Single human visual approval gate

For generated/materially transformed social posts, the normal user journey has **one visual approval gate**. The user reviews the actual publishable-basis A/B/C visuals, including the exact official logo when required, and selection of one compliant candidate is the visual approval for that revision.

Non-material finalization after selection is automatic. Resizing/normalization that preserves composition, format encoding, quality optimization without perceptible design change, canonical naming, hashing, provider storage, ALT/metadata persistence and other technical packaging must not trigger a second visual approval request.

If finalization requires a material visible change relative to the selected candidate, such as meaningful crop/reframe, logo move/resize/variant change, visible-text alteration, creative retouch or another perceptible composition change, only that changed visual is reopened for targeted re-confirmation. A full A/B/C restart is not required unless the concept materially changes or the user requests it.

### Exact `use_as_is` package

A verified exact user source with no material AI treatment does not require fake A/B/C generation. Apply any required official branding without overwriting the source original before calling the visual selectable/final-basis compliant.

## Mandatory user guidance

For A/B/C mode, offer equivalents of:

```text
- validate text and choose A/B/C;
- text-only changes;
- visual-only changes to one/more proposals;
- both text and visual changes;
- new complete A/B/C round while keeping approved text.
```

For `use_as_is`, offer validation/replacement/treatment options compatible with source fidelity.

## Component freeze rule

Review decisions are component-scoped.

- approved text freezes during visual-only iterations unless reopened;
- a compliant selected visual freezes during text-only iterations unless materially invalidated;
- criticizing only A does not alter B/C;
- changing text does not regenerate visuals unless materially needed;
- source originals are never overwritten;
- a new A/B/C round preserves approved text and source policy unless explicitly changed.

A visual that is later discovered not to have been review-ready is **technically invalidated without invalidating unrelated approved text**.

## Durable review state

Post/checklist represents at least:

```yaml
text_status: drafting|in_review|approved
visual_status: not_started|source_ready|proposals_generated|in_review|selected|verified_final
combined_review_status: awaiting_combined_review|revision_requested|text_approved_visual_pending|visual_approved_text_pending|fully_approved
review_round: <positive integer>
```

`proposals_generated` means review-ready proposals, not raw base drafts. `selected` means selection of a review-ready candidate identity/hash.

Every review round binds exact durable post revision, frozen `contract_revision`, and exact visual identity set. When branding is required, bind official-logo/composition evidence too.

## Completion condition

A social post leaves combined review only when:

```text
text_status = approved
AND
one exact review-ready visual/source final basis = human selected/validated
```

`fully_approved` must not be set merely because the user chose a visually appealing binary that still contains generated/unverified required branding.

After selection, `asset-ingest` normalizes/verifies final according to media architecture. When that finalization is non-material, it proceeds without another human visual approval and the system reports the resulting `verified_final` state. Combined approval is not scheduling or publication authorization.

## Recovery of a late branding defect

If a previously selected candidate is discovered to contain a generated/unverified logo:

1. preserve `text_status=approved` when text is unaffected;
2. preserve the user's conceptual preference as a recovery target;
3. move visual approval back to pending/revision state rather than pretending the binary remains selectable/finalizable;
4. use an exact clean base if one actually exists, otherwise perform the narrowest repair/regeneration without claiming exact pixel recovery;
5. apply the official logo deterministically;
6. present the repaired branded result for targeted confirmation because its bytes/hash changed;
7. do not require a full A/B/C restart unless the repair changes the concept materially or the user requests it.

## Relationship to article workflow

Interaction principle:

```text
resolve source/brand prerequisites
-> produce all policy-compliant reviewable components
-> show them together
-> ask for consolidated human review
-> revise only requested/affected elements
-> loop until approved
```

The implementation must not split text and visual review into unnecessary stop/start interactions, but must also never defer a known brand-integrity blocker until after human selection.
