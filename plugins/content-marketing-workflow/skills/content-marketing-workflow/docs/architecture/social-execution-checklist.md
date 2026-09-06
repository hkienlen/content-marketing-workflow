# Social post execution checklist

Date: 2026-09-06
Status: architecture contract

## Purpose

Every social production execution makes source-series planning state observable before individual post production. Every durable post maintains a Markdown checklist distinguishing concept/ID selection, **pre-draft visual-source/brand resolution**, master text, combined review, media finalization, final cloud package, scheduling, exact publication authorization, provider creation evidence, post-publication verification and optional notifications.

A task is checked only when its expected result is actually observable and verified.

Read together with:

```text
docs/architecture/runtime-compatibility-matrix.md
docs/architecture/user-provided-images.md
docs/architecture/visual-generation-contract.md
docs/architecture/brand-assets-contract.md
docs/architecture/google-drive-workspace.md
docs/architecture/dropbox-workspace.md
docs/architecture/capabilities/visual-source-resolve.md
docs/architecture/social-workflow.md
docs/architecture/social-final-drive-package.md
docs/architecture/social-post-review-loop.md
```

## Series-level prerequisite

Before creating a new article-derived post, source folder contains validated `series-plan.md` with exact source article, inventory/deduplication, complete materially distinct candidate series, strategic functions/roles/order, persistence/re-read, human validation and accepted concept state.

## Required task groups

### Source and concept

- exact validated source/context identified;
- series-plan read where applicable;
- concept accepted before consuming new ID;
- immutable `post_id` allocated/reused exactly once and verified in registry;
- durable post carries proper source/article/series/function fields;
- series plan updated with post identity/path/state.

### Pre-draft visual-source/brand resolution

Before master text drafting:

- active profile `visual_preferences` and `visual_identity` loaded when present;
- selected `cloud_media_storage` provider resolved from durable project state;
- selected provider is `google_drive` or `dropbox` and operational before provider-backed source intake;
- effective `project default -> social override -> post-local source override` resolved by `visual-source-resolve`;
- effective social logo application resolved from `visual_identity.logo_policy.social` plus any post-local override; article logo policy is not used;
- referenced user-owned `strategy/visual-guidelines.md` read when present;
- project-global, social-specific and post-local user visual directives identified with correct precedence;
- local source/visual/logo override persisted only on this content item when applicable;
- if user source is required/prioritized, exact source candidates are located/uploaded or missing-source behavior applied;
- selected-provider `social/<post-name>/source-user/` created/reused when needed;
- when user placement is required, exact canonical provider path + verified direct folder link are displayed when the active adapter exposes one;
- claimed source file/bytes actually verified;
- relevant source image actually inspected before visible facts are used in master text;
- source provider/role/fidelity/treatment/provenance persisted;
- user original remains unchanged;
- one truthful source state recorded: `source_ready`, `ai_generation_allowed`, `continue_without_visuals` or `awaiting_user_images`;
- one truthful brand state recorded/recoverable: `ready` or `awaiting_brand_asset` when applicable.

If `awaiting_user_images`, master-text drafting remains blocked until source intake completes or explicit compatible local override is persisted.

`awaiting_brand_asset` may allow text/base-image work but blocks `verified_final` when effective social logo application is `always`.

### Master text

After source gate permits drafting:

- complete publishable master text drafted from accepted concept/source;
- verified user-image facts only when image informed copy;
- writing/style rules pass;
- no production notes/forbidden Markdown inside publishable text;
- text status persisted as `in_review` before presentation;
- targeted feedback applied;
- explicit human text validation before `approved`.

### Visual workspace and review package

When visual required:

- private selected-provider `source-user/`, `proposals/`, `final/` exist/reused as applicable;
- official project logo, when required/allowed, is read from private provider brand workspace rather than content source folder;
- complete effective social visual contract resolved from workflow invariants + post-local user directives + social directives + global user directives + generic CMW defaults;
- visual brief tied to exact current text/concept/source/visual/brand policy;
- visual mode matches source role/fidelity/treatment;
- generic CMW social creative defaults fill only unspecified dimensions and do not override user directives;
- candidate diversity is real unless deliberate short-series coherence is documented;
- for generated work, derive a **brand-isolated base-generation brief** before invoking the image model; do not pass the complete effective contract, official-logo identity, provider IDs/hashes or logo-placement instruction to the generator;
- translate final logo-placement preferences only into neutral reserved composition space for base generation;
- generated outputs are **base drafts, not A/B/C review candidates** until every pre-review invariant is satisfied;
- base-generation brief explicitly excludes project logos, pseudo-logos, brand signatures and watermarks;
- for a disposable pure-AI base, accidental/generated project branding causes reject/regenerate by default rather than a normal logo-removal edit cycle;
- targeted repair is reserved for source-dependent/user-owned/recovery cases where preserving existing pixels materially matters;
- retain three genuinely distinct clean bases when generated/materially transformed alternatives are required;
- with `logo_application=always`, deterministically compose the exact official logo on each retained clean base before assigning durable A/B/C review identities;
- validate branded A/B/C with `visual-review-gate.py` or equivalent before presentation;
- manual/external generation uses the same brand-isolated base brief and may reserve composition space but never asks a model to recreate an official logo;
- exactly three branded review-ready A/B/C are stored/recoverable in selected provider before review when generated/materially transformed alternatives are required;
- `always` uses exact official verified logo bytes, not AI recreation;
- `never` keeps project logo absent;
- `auto` may include only an official verified logo;
- exact `use_as_is` + no-material-treatment workflow preserves original and prepares exact review/final candidate without fake A/B/C;
- exact candidate/proposal identities are provider-qualified and persisted for active review round;
- effective visual-contract/logo evidence is tied to the active review round;
- visual status is review state, never selected/final automatically.

No silent provider fallback. Canva/Work is not normal generator merely because one runtime lacks image generation.

### Mandatory combined post review

First normal review presents in one response:

- exact post ID/concept/function;
- complete publishable master text;
- A/B/C when alternatives were generated/materially transformed;
- or exact user source/final candidate when `use_as_is` applies;
- the actual official-logo composition when effective `always` policy requires branded final;
- explicit guidance telling user what may be approved/revised, including changing source/treatment/local visual rule where relevant.

Track at least:

```yaml
text_status: drafting|in_review|approved
visual_status: not_started|source_ready|proposals_generated|in_review|selected|verified_final
combined_review_status: awaiting_combined_review|revision_requested|text_approved_visual_pending|visual_approved_text_pending|fully_approved
review_round: <positive integer>
```

Every review round binds exact text revision + exact source/proposal identities + effective visual/logo contract revision/evidence.

### Targeted revisions / freeze

- approved text remains frozen during visual-only revisions unless reopened;
- selected/approved visual/source remains frozen during text-only revisions unless materially invalidated;
- criticizing only A does not alter B/C;
- requested new A/B/C round preserves approved text/source/effective user directives/logo policy unless explicitly reopened;
- strict/high source fidelity preserves real subject exactly where required;
- user source and official logo originals are never overwritten;
- only materially affected dependencies reopen.

### Final visual

- one exact proposal/source is explicitly human selected/validated;
- full-quality bytes resolved;
- final normalized to current social dimensions/format policy without overwriting source original;
- effective `logo_policy.social` plus any post-local override rechecked;
- `logo_application=always` -> official verified logo visibly present, legible and integrity-preserving;
- `logo_application=never` -> project logo absent;
- `logo_application=auto` -> any included project logo maps to official verified asset;
- official logo is not distorted/recolored/recreated and original asset remains unchanged;
- ALT written from actual final;
- final stored/reused in selected provider private `final/`;
- provider + final identity/reference + SHA-256 verified;
- source provenance retained when applicable;
- brand/effective-contract evidence retained when applicable;
- GitHub stores provider-qualified final identity/filename/hash/MIME/dimensions/ALT/status and source/brand relationship;
- GitHub state re-read and matches provider assets.

### Final cloud package

Before scheduling readiness:

```text
text_status = approved
AND
visual_status = verified_final
AND
combined_review_status = fully_approved
AND
provider-appropriate final text artifact = verified_final
```

Provider-specific final text artifact:

```text
google_drive -> native Google Doc containing only exact approved publishable text
dropbox      -> UTF-8 plain-text .txt containing only exact approved publishable text
```

- text artifact is stored in same private `final/` folder as selected visual;
- body is exact publishable copy only, without workflow metadata;
- provider + artifact identity/reference + folder reference + body policy + format persisted/re-read;
- revised approved text updates/reuses canonical artifact instead of creating duplicates.

Combined approval/final package is not scheduling or publication authorization.

### GitHub integration

Persist series/post/checklist/review/media/source/brand/effective-contract/final-package state; synchronize branch/PR automatically when used; verify mutations; no GitHub-only approval prompt.

### Scheduling

When in scope:

- platforms known;
- exact timezone-aware `planned_at` approved;
- schedule persisted/re-read;
- global CTA/calendar adjacency checked;
- publication-consent policy resolved;
- exact `authorized_for_scheduled_publication` exists before unattended execution;
- authorization binds target/time/text/ALT/final media hash/delivery identity;
- source-user/brand asset is never publication object unless incorporated into selected verified final under media contract;
- bound change, including logo-policy/logo-asset change that changes final bytes, invalidates/replaces exact authorization only after revised final state validation.

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

### Post-publication verification

Platform-specific verification remains independent from cloud-media provider selection. A cloud provider stores/transports media; it never proves social publication.

### Optional Telegram report

When verified/enabled: send only after durable publication/verification reconciliation; notification failure never changes publication state/retries publication.

## Observable-result invariant

```text
candidate extracted != series persisted != concept accepted
concept accepted != visual source policy resolved
visual source policy resolved != source verified != source inspected
social logo policy resolved != logo asset available != logo composed != logo verified in final
article logo policy != social logo policy
user directive persisted != applied to active review round
source inspected != post drafted
post drafted != presented != text approved
visual base generated != review-ready A/B/C != stored != presented != selected != verified_final
use_as_is source != generated proposal
combined review shown != fully approved
verified_final visual != complete final cloud package
schedule planned != exact publication authorization != scheduler dispatch
scheduler success != provider creation evidence
provider creation evidence != post-publication verification
social publication state != Telegram notification delivery
```

## Resume behavior

On resume read exact source article/series-plan/post/checklist/ID registry/visual preference+override/visual_identity/social logo policy/referenced user visual guidelines/source provenance/selected-provider media/brand/effective-contract/final-package/review/schedule/authorization/publication/verification/notification state.

Continue from first incomplete task whose prerequisites are satisfied. Do not infer completion from conversation memory or scheduler color.

Do not call an `always`-branded post visual `verified_final` while brand state is `awaiting_brand_asset`.

A provider change requires explicit migration/rebinding before old provider identities are treated as current. Controlled editorial reset keeps immutable ID, resets only affected review/media states, and preserves user source/official logo originals.
