# Detailed user help - social commands

Date: 2026-09-04
Status: user-help contract for future skill

## Purpose

Defines user-facing explanation for social creation, source images, review, scheduling, connection health, publication, post-publication verification and optional publication notifications. Natural-language equivalents route to same capabilities.

Read product behavior from:

```text
docs/architecture/social-workflow.md
docs/architecture/user-provided-images.md
```

## `/social create`

### What it does

Creates or resumes the next eligible social post from durable validated queue.

For an already validated series:

```text
resume incomplete post if any
-> otherwise take next accepted concept in validated order
-> resolve visual source policy
-> draft/review post when source gate permits
```

When current series is exhausted:

```text
next eligible validated article
-> inventory/deduplicate
-> generate complete materially distinct series
-> classify strategic functions
-> propose balanced order
-> persist/re-read
-> present full detailed series
-> user validates/corrects
-> persist exact validated revision
-> start first eligible post automatically
```

No second generic `go` is required after list validation.

### Strategic functions

Every retained article-derived concept is classified as one of:

- **Identification** - helps target recognize situation/problem;
- **Expertise / compréhension** - explains useful mechanism/distinction;
- **Méthode / positionnement** - clarifies approach, boundaries or way of working;
- **Offre / conversion** - connects to an actual supported offer/next step.

The mix is guidance, not quota. Unsupported commercial claims are never invented. Order avoids unnecessary consecutive commercial/strong-CTA posts by default.

### New: your own photos before writing

Before the post master text is drafted, the skill resolves active `visual_preferences`:

```text
project default
-> social override
-> this-post override
```

Possible source preference:

```text
ai_first
user_images_first
strict_user_images
hybrid_best_fit
```

If policy requires or prioritizes your images and a relevant source is missing with `ask_before_drafting`, the post pauses **before writing** and asks for the real image.

With Google Drive it creates/reuses:

```text
<drive-root>/<site-domain>/social/<post-name>/source-user/
```

and tells you both:

- the exact folder path;
- a direct clickable Google Drive link to that verified folder.

You can also upload a real image directly in chat when supported. The skill verifies and inspects the actual image before using visible details as writing/visual context.

Your original file is never overwritten.

### One-post override

You can naturally say:

```text
"Pour ce post seulement, génère l'image entièrement avec l'IA."
"Utilise cette photo telle quelle, sans retouche."
"Garde le produit exactement identique, change seulement le fond."
```

That changes only this post unless you explicitly ask to change durable preference.

To change future default, use normal language or:

```text
/strategy update <request>
```

### Visual roles

A supplied image may be used as:

```text
use_as_is
enhance
subject_reference
inspiration_reference
composition_input
```

If role is already clear from your instruction, no extra question is required.

`strict`/`high` fidelity protects appearance of real subject; the skill must not silently invent a different product/work/person/place.

### A/B/C or exact photo?

If visual is generated from scratch or materially transformed, the normal review presents exactly three genuine alternatives A/B/C.

If your exact photo is `use_as_is` with no material AI treatment, the skill does **not** invent two synthetic alternatives just to make A/B/C. It presents the exact photo/final candidate for review.

### Combined review

The first normal post review shows complete publishable text together with appropriate visual package.

You may:

- approve text + choose A/B/C;
- approve text + validate exact supplied photo;
- request text-only changes;
- request visual-only changes;
- request both;
- ask for a new A/B/C round when applicable;
- replace supplied source or change allowed treatment.

Approved components stay frozen unless explicitly reopened or another requested change materially requires it.

### What it never does implicitly

`/social create` does not schedule and does not publish. Uploading/selecting a photo is not publication authorization.

## `/social create free <topic>`

Creates a standalone post deliberately unrelated to article series.

It skips only whole-series validation. It still uses:

- global deduplication;
- immutable post ID;
- optional strategic function for calendar balance;
- same visual-source preference/intake behavior before writing;
- same combined text/media review;
- same final Drive package;
- same scheduling and publication safety gates.

No fake article provenance is created.

## `/social plan`

Inventories/rebuilds article's complete deduplicated series plan without requiring post creation.

Help explains four functions, coverage rationale and order. Planning itself does not need/source a post image because no specific post is yet entering production.

## `/social visual`

Creates/reviews visual for an already resolved accepted post.

It uses effective source policy and any already verified user source:

- generated/materially transformed -> exactly A/B/C;
- `use_as_is` -> exact photo/final candidate, no fake A/B/C;
- enhancement/reference/composition -> compliant alternatives only within fidelity/treatment limits.

It never overwrites source original, schedules or publishes.

## `/social list` and `/social details`

Read-only projections showing durable reserve/post state, provenance, strategic function, source article/free origin, review/schedule/publication/verification state and visual/source state when persisted.

They do not repair or mutate data.

## `/social schedule`

Schedules an already fully approved post.

Before final time it checks neighbouring global calendar entries and avoids consecutive conversion/strong-CTA posts by default. It proposes an alternative instead of silently moving an explicit user-selected time.

Scheduling remains distinct from publication authorization.

A platform may have publication-consent policy:

```text
one_off_exact_confirmation
standing_auto_publish_scheduled
```

Standing scheduled policy can eliminate repetitive confirmations only after final text/visual/ALT/time approval and by materializing an exact per-post authorization. Any bound change invalidates applicable exact authorization.

Important:

```text
scheduled
!= published
scheduler success
!= provider publication evidence
```

## `/social check`

Read-only fail-closed readiness check. Verifies exact state required for publication without publishing.

## `/social health`

Read-only social connection health.

Reports live credential/identity probe when available, known token/data-access expiry horizons, J-30/J-14/J-7 warnings and scheduled posts/authorizations beyond known validity.

It guides renewal but never exposes credentials or claims provider credential can always be renewed automatically.

## `/social publish`

Publishes only through supported connected adapter and exact runtime authorization.

If adapter setup is missing/postponed/incomplete, it resumes platform-specific onboarding rather than treating setup as provider publication failure.

Current targets:

```text
LinkedIn member profile
Facebook Page
```

Facebook personal/professional profiles are not automated API targets.

### Exact execution binding

Runtime publication checks exact:

- post/platform target;
- approved master text/hash;
- ALT;
- verified final media identity/hash;
- schedule/time;
- authorization identity/revision;
- connection/account identity.

A source-user photo that has not been explicitly selected/finalized is not a publication object.

### Provider evidence

Current definitive creation evidence:

```text
LinkedIn -> HTTP 201 + x-restli-id
Facebook -> definitive remote post/media IDs + HTTP success evidence + exact authorization binding
```

Uncertain external creation blocks blind retry.

## Post-publication verification

### Facebook

After definitive creation, current supported Bridge reads back exact remote post/media and verifies expected Page/IDs/message hash. Success becomes:

```text
status: published
verification_state: remote_verified
```

If creation was definite but readback fails, do not republish merely because verification failed.

### LinkedIn

Current member permission scope gives definitive creation acknowledgement but not independent post readback. Durable state:

```text
status: published
verification_state: provider_acknowledged
readback_available: false
```

`provider_acknowledged` is not claimed as remote verification.

## `/social notifications telegram`

Optional publication reports.

Existing profile state is inspected first so verified setup can be reused. Missing setup guides user through BotFather `/newbot`, stores bot token only as GitHub Actions Repository Secret `TELEGRAM_BOT_TOKEN`, guides sending `/start`/message, discovery of `chat_id`, exact destination verification and one explicit test message before `enabled=true`.

Supports disable/re-enable/destination change/token rotation. Success/failure/uncertain preferences are independent.

Telegram delivery failure never changes social publication state and never causes republication.

## Visual preference summary in `/status`

`/status` can show configured project/article/social visual preference and an active `awaiting_user_images` blocker. It is read-only.

Changing default uses natural language or `/strategy update`, not `/status`.
