# Internal capability - seo-update-article

Date: 2026-09-01
Status: architecture contract

## Purpose

`seo-update-article` is a core internal capability of the single installable Content / Marketing skill.

It turns human review feedback on an article and its image proposals into durable, targeted corrections on the existing production branch and Pull Request.

It is not a separately installable skill.

Read this contract together with `docs/architecture/github-transparency.md`: after onboarding, normal GitHub mechanics are internal and must not create separate user approval gates.

## Contract

```yaml
name: seo-update-article
purpose: Persist review decisions and apply targeted corrections to an article already under production/review.
availability: core
feature_gate: null
mode: mutating

prerequisites:
  - Work Item exists
  - dedicated task prompt exists
  - production branch exists
  - Pull Request exists
  - current article/review state is identifiable

mandatory_context:
  - AGENTS.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/github-transparency.md
  - docs/architecture/capability-contract-template.md
  - docs/architecture/prompt-as-contract.md
  - Work Item state
  - dedicated task prompt
  - current production branch/PR
  - current article
  - relevant authoritative directives

optional_context:
  - Human Item
  - current review-round state
  - Drive proposal references
  - selected image bytes/files
  - PR discussion/reviews

reads:
  - current article and task prompt
  - existing branch/PR state
  - review feedback
  - current Drive visual proposals when relevant

writes:
  - task-specific prompt/context for durable task feedback
  - authoritative global files for durable global rules
  - current article on existing branch
  - Work Item tracking/review state
  - selected media through asset-ingest when available
  - regenerated visual proposals in the same Drive article workspace

persists:
  - article-specific requested corrections
  - validated/frozen article components
  - selected/rejected visual decisions
  - regeneration requirements
  - durable review constraints
  - exact current review version/state
  - global rules in their authoritative files

external_side_effects:
  - GitHub updates on the existing branch/PR
  - automatic branch/PR synchronization and merge when all required content/media gates are satisfied
  - image regeneration when required
  - asset ingestion after explicit human selection when implemented/available

human_approval:
  - complete editorial validation
  - final image selection
  - replacing an already-final media asset
  - downstream externally visible publication

validation:
  - feedback classified before persistence/execution
  - existing branch and PR reused
  - only requested/necessarily impacted components changed
  - validated components remain frozen unless an explicit dependency requires change
  - selected/rejected image state is truthful
  - resulting GitHub state verified
  - no downstream publication gate inferred from partial approval

completion_conditions:
  - all supplied durable review decisions persisted correctly
  - requested corrections applied and committed on existing branch
  - affected image series regenerated only when required
  - validated/frozen components preserved
  - review state synchronized
  - exact new review version identifiable
  - user receives the appropriate targeted or final review projection
  - when the complete article and all required media are explicitly validated, the skill automatically performs and verifies the ordinary GitHub integration/merge without asking for a separate merge authorization

next_actions:
  - repeat seo-update-article while corrections remain
  - asset-ingest when an image is explicitly selected
  - automatic GitHub integration once complete final content/media validation is satisfied
  - WordPress/social downstream capabilities only after their own prerequisites/gates
```

## Feedback classification

For each user comment, classify it before or as part of execution:

1. task-specific durable feedback;
2. global durable rule;
3. site/business durable fact;
4. transient discussion/comment;
5. secret/credential material.

The user must not decide where a decision belongs.

Examples of task-specific feedback:

- rewrite one section;
- remove one example from this article;
- choose proposal B for image 1;
- reject image 2 and regenerate it more soberly;
- preserve a specific article-specific wording.

Examples of global feedback:

- apply this editorial rule to all future articles;
- always store proposals in a new canonical location;
- change the permanent image review method.

Task-specific feedback belongs in the active task prompt/context/review state. Global feedback belongs in the authoritative global file.

## Version safety

Every review round must be bound internally to the exact persisted source version used for the displayed review.

At minimum track:

```text
article_path
article_commit_sha
review_round
current review state
relevant Drive proposal references
```

Before applying feedback, verify/reload the current persisted article.

If the source changed since the reviewed version, reconcile the difference before applying potentially conflicting feedback.

## Review states

Use conceptually distinct editorial states:

```text
review_ready
awaiting_human_validation
corrections_requested
human_validated
```

Media selection has its own independent lifecycle and must not be collapsed into the editorial state.

After a correction pass, return to `awaiting_human_validation` for the corrected version unless the user has clearly and explicitly validated the complete final version being reviewed.

## What counts as validation

Validation is intent-based and must be unambiguous in context.

Do not infer complete article validation from:

- silence;
- `merci`;
- approval of one paragraph/image/metadata field;
- `c'est mieux` or another ambiguous positive reaction;
- a message that still requests changes.

If a message both praises the result and asks for changes, treat it as `corrections_requested` unless the whole article is clearly approved after the changes have actually been applied and presented.

## Targeted correction rule

The current batch-review model is authoritative.

After feedback:

1. identify every component explicitly affected;
2. identify unavoidable dependency impacts;
3. freeze all components already validated or explicitly left unchanged;
4. change only the affected article sections/metadata/image series;
5. do not rewrite the whole article merely because one section changed;
6. do not regenerate all visual proposals because one image was rejected;
7. if a validated element must change due to dependency, state the reason and minimize the change.

This rule reduces review effort while preserving coherence.

## Intermediate review projection

During correction rounds, the normal user-facing projection may show only:

- changed article passages with enough surrounding context;
- regenerated/replaced image series;
- compact status of preserved/frozen components;
- remaining unresolved decisions.

Do not force the user to reread the complete article after every minor change.

However, before automatic GitHub integration and WordPress preparation, present a complete coherent final snapshot of:

- the full article;
- final SEO metadata useful to review;
- all selected/final media and their placement;
- any remaining independent **business/content/publication** gates.

That final complete snapshot must be bound to the exact persisted version.

The snapshot is a content-review gate, not a request to approve GitHub mechanics.

## Image review and regeneration

For each image, keep truthful state such as:

```text
proposed
selected
normalized
committed
verified
```

Record selected/rejected candidates and regeneration instructions when they must survive a new session.

A selected image is not automatically committed.

When actual selected bytes/files are available and `asset-ingest` is implemented/available, invoke it according to its own contract.

Regenerated proposals remain in the same canonical Drive article workspace under a new review round or otherwise unambiguous subfolder.

## Same branch and PR

All review corrections for one active Work Item use the existing production branch and PR.

Do not create:

- a new branch for a correction pass;
- a media-specific branch;
- a replacement PR because a new review round started.

After writes, verify the actual PR head and tracking state.

The user is not asked to approve branch/commit/PR/merge operations. Once complete editorial validation, final required media selection/finalization and the required final snapshot are satisfied, merge the PR automatically and verify the result according to `docs/architecture/github-transparency.md`.

## Downstream gates

Complete editorial validation does not imply:

- all media are selected/final;
- WordPress publication approval;
- social publication approval.

GitHub merge is not a separate downstream user gate; it is an internal operation automatically performed after the required article/media validations.

WordPress preparation may proceed automatically after merge when the configured workflow says so, but WordPress publication remains governed by its own explicit publication contract. Social publication remains governed by its own applicable human gates.

## Failure and resume behavior

If execution is interrupted or a write fails:

- inspect current GitHub/Drive state first;
- retain valid persisted decisions;
- do not duplicate branches/PRs/proposals;
- report the exact incomplete step when it materially blocks user progress;
- repair tracking inconsistencies automatically when safe;
- never shift normal Git/file persistence work back to the user merely because one automated step failed.

A correction pass is complete only when the requested durable changes are actually persisted and verified.