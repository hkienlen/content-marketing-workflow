# Social post combined review loop

Date: 2026-09-04
Status: current architecture contract

## Purpose

This contract defines the mandatory human-review loop for a social post produced by `/social create` or `/social create free`.

It supports two valid visual review shapes after `visual-source-resolve` and `social-create-visual`:

```text
A) generated/materially transformed
write post -> visual brief -> A/B/C -> combined review

B) verified exact user source (`use_as_is`)
write post -> exact source/final candidate -> combined review
```

A visual package displayed without the post text and explicit guidance is incomplete.

## Precondition: visual source already resolved

Before master-text drafting and this review loop, `visual-source-resolve` must have produced a truthful allowed state.

If state remains `awaiting_user_images`, this review loop has not begun.

Source verification/inspection is not final visual approval.

## First review package

The first normal review contains in the same response:

1. exact `post_id` and concept/function;
2. complete publishable master text;
3. visual package appropriate to effective source role;
4. concise visual role/difference notes when useful;
5. explicit instructions telling user what can be validated/revised.

### Generated/materially transformed package

Must show:

```text
Visual A
Visual B
Visual C
```

with exactly three persisted/recoverable identities.

### Exact `use_as_is` package

When verified user source is intended as exact visual with no material AI treatment, it **does not require** fake A/B/C generation and must not create synthetic alternatives merely to satisfy a historical proposal count.

Show:

```text
exact source/final visual candidate
source role: use_as_is
relevant normalization/crop constraint if any
```

The source original remains preserved; any normalized final is a separate object/file.

## Mandatory user guidance

For A/B/C mode, explicitly offer equivalents of:

```text
- validate text and choose A/B/C;
- text-only changes;
- visual-only changes to one/more proposals;
- both text and visual changes;
- new complete A/B/C round while keeping approved text;
- when user source is involved, change source/treatment within fidelity rules.
```

For `use_as_is`, explicitly offer equivalents of:

```text
- validate text + exact visual;
- text-only changes while keeping visual;
- change/replace source visual;
- request allowed retouching/treatment;
- request a generated alternative only if compatible with active fidelity policy or explicit local override.
```

Examples the workflow understands naturally:

```text
"Texte OK, je choisis B"
"Le texte est trop long"
"Texte OK, garde exactement cette photo"
"Garde le produit tel quel, change seulement le fond"
"Utilise plutôt la deuxième photo"
"Texte OK, refais les trois images"
```

## Component freeze rule

Review decisions are component-scoped.

- approved text freezes during visual-only iterations unless reopened;
- selected/approved visual or exact user source freezes during text-only iterations unless materially invalidated;
- criticizing only A does not alter B/C;
- changing only background under strict/high subject fidelity never authorizes changing subject;
- changing text does not regenerate visuals unless materially needed;
- changing source reopens only dependent visual/final state, and text only if source facts materially affected copy;
- user source original is never overwritten during review iterations;
- a new A/B/C round preserves approved text and source policy unless explicitly changed.

## Durable review state

Post/checklist represents at least:

```yaml
text_status: drafting|in_review|approved
visual_status: not_started|source_ready|proposals_generated|in_review|selected|verified_final
combined_review_status: awaiting_combined_review|revision_requested|text_approved_visual_pending|visual_approved_text_pending|fully_approved
review_round: <positive integer>
```

Every review round binds exact durable post revision and exact visual source/proposal identity set.

For user-source workflows, bind source provenance identity/hash when available plus treatment/fidelity role. For A/B/C, bind exact proposal identities.

## Completion condition

A social post leaves combined review only when:

```text
text_status = approved
AND
one exact visual/source final basis = human selected/validated
```

After selection, `asset-ingest` normalizes/verifies final according to media architecture while preserving any user source original/provenance.

Combined approval is not scheduling authorization and never publication authorization.

## Relationship to article workflow

Interaction principle remains:

```text
resolve any required user source before drafting
-> produce all reviewable components that policy actually requires
-> show them together
-> ask for consolidated human review
-> revise only requested/affected elements
-> loop until approved
```

The implementation must not split text and visual review into unnecessary start/stop interactions and must not create unnecessary synthetic variants for an exact real source.
