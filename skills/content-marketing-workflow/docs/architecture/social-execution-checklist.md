# Social post execution checklist

Date: 2026-09-04
Status: architecture contract

## Purpose

Every social production execution makes source-series planning state observable before individual post production. Every durable post maintains a Markdown checklist distinguishing concept/ID selection, **pre-draft visual-source intake**, master text, combined review, media finalization, scheduling, exact publication authorization, provider creation evidence, post-publication verification and optional notifications.

A task is checked only when its expected result is actually observable and verified.

Read together with:

```text
docs/architecture/user-provided-images.md
docs/architecture/capabilities/visual-source-resolve.md
docs/architecture/social-workflow.md
docs/architecture/social-post-review-loop.md
```

## Series-level prerequisite

Before creating a new article-derived post, source folder contains validated:

```text
social/<scope>/<source-or-series>/series-plan.md
```

showing exact source article, inventory/deduplication, complete materially distinct candidate series, strategic functions/roles/order, persistence/re-read, human validation and accepted concept state.

Inventory/candidate generation are automatic; first post drafting waits for exact new/materially revised series validation, then continues without another generic `go` to ID/source-policy resolution.

## Canonical per-post file

For:

```text
social/<scope>/<source-or-series>/post-XX.md
```

maintain:

```text
social/<scope>/<source-or-series>/post-XX.checklist.md
```

with immutable `post_id`, exact provenance and stable `series_concept` key when article-derived.

## Required task groups

### Source and concept

- exact validated source/context identified;
- series-plan read where applicable;
- concept accepted before consuming new ID;
- immutable `post_id` allocated/reused exactly once and verified in registry;
- durable post carries proper source/article/series/function fields;
- series plan updated with post identity/path/state.

### Pre-draft visual-source resolution

Before master text drafting:

- active profile `visual_preferences` loaded;
- effective `project default -> social override -> post-local override` resolved by `visual-source-resolve`;
- local override persisted only on this content item when applicable;
- if user source is required/prioritized, exact source candidates are located/uploaded or missing-source behavior applied;
- Drive `social/<post-name>/source-user/` created/reused when needed;
- when user placement is required, exact canonical path + verified direct Drive folder link were actually displayed;
- claimed source file/bytes actually verified;
- relevant source image actually inspected before visible facts are used in master text;
- source role/fidelity/treatment/provenance persisted;
- user original remains unchanged;
- one truthful state recorded: `source_ready`, `ai_generation_allowed`, `continue_without_visuals` or `awaiting_user_images`.

If `awaiting_user_images`, master-text drafting remains unchecked/blocked until source intake completes or explicit compatible local override is persisted.

### Master text

After source gate permits drafting:

- complete publishable master text drafted from accepted concept/source;
- verified user-image facts only when image informed copy;
- writing/style rules pass;
- no production notes/forbidden Markdown inside publishable text;
- text status persisted as `in_review` before presentation;
- targeted feedback applied;
- explicit human text validation before `approved`.

Drafting/persistence does not count as presenting/validating.

### Visual workspace and review package

When visual required:

- private provider-backed `source-user/`, `proposals/`, `final/` exist/reused as applicable;
- official logo source available when required;
- visual brief tied to exact current text/concept/source policy;
- visual mode matches source role/fidelity/treatment;
- generated/materially transformed workflow creates exactly three genuinely distinct A/B/C through assistant image generation/editing;
- A/B/C stored/recoverable before review;
- exact `use_as_is` + no-material-treatment workflow preserves original and prepares exact review/final candidate **without fake A/B/C**;
- exact candidate/proposal identities persisted for active review round;
- visual status is review state, never selected/final automatically.

No silent ephemeral fallback. Canva/Work is not normal generator.

### Mandatory combined post review

First normal review presents in one response:

- exact post ID/concept/function;
- complete publishable master text;
- A/B/C when alternatives were generated/materially transformed;
- or exact user source/final candidate when `use_as_is` applies;
- explicit guidance telling user what may be approved/revised, including changing source/treatment where relevant.

Track at least:

```yaml
text_status: drafting|in_review|approved
visual_status: not_started|source_ready|proposals_generated|in_review|selected|verified_final
combined_review_status: awaiting_combined_review|revision_requested|text_approved_visual_pending|visual_approved_text_pending|fully_approved
review_round: <positive integer>
```

Every review round binds exact text revision + exact source/proposal identities.

### Targeted revisions / freeze

- approved text remains frozen during visual-only revisions unless reopened;
- selected/approved visual/source remains frozen during text-only revisions unless materially invalidated;
- criticizing only A does not alter B/C;
- requested new A/B/C round preserves approved text/source policy;
- request such as `change only background` under strict/high source fidelity preserves real subject exactly;
- user source original is never overwritten;
- only materially affected dependencies reopen.

### Final visual

- one exact proposal/source is explicitly human selected/validated;
- full-quality bytes resolved;
- final normalized to current social dimensions/format policy without overwriting source original;
- official logo verified when required;
- ALT written from actual final;
- final stored/reused in private provider `final/`;
- final provider identity/SHA-256 verified;
- source provenance retained when applicable;
- GitHub stores provider, final asset_id/filename/hash/MIME/dimensions/ALT/status and source relationship;
- GitHub state re-read and matches provider assets.

### Combined approval completion

Before scheduling readiness:

```text
text_status = approved
AND
visual_status = verified_final
AND
combined_review_status = fully_approved
```

Then retain coherent final snapshot containing exact master text, final visual, source provenance where relevant, ALT, target platforms, article-link decision and unresolved decisions.

Combined approval is not scheduling or publication authorization.

### GitHub integration

Persist series/post/checklist/review/media/source state; synchronize branch/PR automatically when used; verify mutations; no GitHub-only approval prompt.

### Scheduling

When in scope:

- platforms known;
- exact timezone-aware `planned_at` approved;
- schedule persisted/re-read;
- profile default time applied only when appropriate;
- global CTA/calendar adjacency checked;
- publication-consent policy resolved;
- exact `authorized_for_scheduled_publication` exists before unattended execution;
- authorization binds target/time/text/ALT/final media hash/delivery identity;
- source-user asset is never the publication object unless explicitly selected/finalized under media contract;
- bound change invalidates/replaces exact authorization only after revised final state validation.

Scheduling != publication. Scheduler success means due-record/relay dispatch only.

### Publication

When in scope:

- exact post/platform/text/final-visual/time state verified immediately before mutation;
- connection/identity/token prerequisites rechecked;
- required exact authorization exists;
- provider result classified definitive success/deterministic failure/uncertain external result;
- success evidence bound to exact current authorization/revision/schedule/target/content/final media intent;
- historical/mismatched replay never projected as current success;
- definitive evidence persisted;
- uncertain result blocks blind retry;
- no duplicate publication.

Current provider proof:

```text
LinkedIn -> HTTP 201 + x-restli-id
Facebook -> definitive remote post/media IDs + HTTP success evidence + exact-current-authorization binding
```

### Post-publication verification

Facebook current supported Bridge: read exact remote post/media, verify Page/IDs/message hash, persist `remote_verified` on success; if readback fails after definitive creation keep `published`, do not republish.

LinkedIn current member access: persist creation evidence + `provider_acknowledged`, `readback_available: false`; never call it `remote_verified` without independent supported readback.

### Optional Telegram report

When verified/enabled: send only after durable publication/verification reconciliation; use `TELEGRAM_BOT_TOKEN` from Repository Secrets only; persist non-secret report delivery state where useful; suppress duplicates. Notification failure never changes publication state/retries publication.

## Observable-result invariant

```text
candidate extracted != series persisted != concept accepted
concept accepted != visual policy resolved
visual policy resolved != source verified != source inspected
source inspected != post drafted
post drafted != presented != text approved
visual generated != stored != presented != selected != verified_final
use_as_is source != generated proposal
combined review shown != fully approved
schedule planned != exact publication authorization != scheduler dispatch
scheduler success != provider creation evidence
provider creation evidence != post-publication verification
Facebook published != Facebook remote_verified
LinkedIn provider_acknowledged != independent remote read-back
social publication state != Telegram notification delivery
```

## Resume behavior

On resume read exact source article/series-plan/post/checklist/ID registry/visual preference+override/source provenance/provider media/review/schedule/authorization/publication/verification/notification state.

Continue from first incomplete task whose prerequisites are satisfied. Do not infer completion from conversation memory or scheduler color.

Controlled editorial reset keeps immutable ID, resets only affected review/media states, and preserves user source originals. Once provider creation is definitive, editorial reset/republication is not retry mechanism.
