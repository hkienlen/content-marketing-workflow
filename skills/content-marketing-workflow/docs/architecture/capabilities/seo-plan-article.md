# Internal capability - seo-plan-article

Date: 2026-08-31
Status: architecture contract

## Purpose

`seo-plan-article` is a core internal capability of the single installable Content / Marketing skill.

It turns a selected topic, search opportunity, user problem or requested article into a durable and restartable planning package without relying on conversation memory.

It is not a separately installable skill.

## Contract

```yaml
name: seo-plan-article
purpose: Select and frame an SEO article, prevent duplication/cannibalization, gather missing original input, and persist the planning package.
availability: core
feature_gate: null
mode: mutating

prerequisites:
  - project onboarding completed
  - GitHub repository readable/writable
  - site strategy and prompt conventions available

mandatory_context:
  - AGENTS.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/capability-contract-template.md
  - docs/architecture/prompt-as-contract.md
  - prompts/README.md
  - prompts/work-items/README.md
  - prompts/work-article-template.md
  - relevant strategy files

optional_context:
  - existing related articles
  - existing Human Items and Work Items
  - existing dedicated prompts
  - branch/PR state
  - Search Console / Ads data
  - current SERP/source research
  - site offers/profile configuration

reads:
  - authoritative planning/editorial strategy
  - relevant existing/planned content
  - relevant GitHub issue and branch/PR state

writes:
  - Human Item when needed
  - Work Item when needed
  - prompts/work-items/article-<N>-<slug>.md
  - existing matching planning artifacts when resuming

persists:
  - validated opportunity
  - audience and search intent
  - primary/secondary queries
  - strategic rationale and conversion destination
  - article-specific angle and boundaries
  - user-provided original/field material
  - task-specific safeguards and claims to avoid
  - cannibalization boundaries
  - image-specific constraints when already known
  - Human Item -> Work Item -> task-prompt relationship

external_side_effects:
  - GitHub issue/file creation or update
  - current web/SERP research when required

human_approval:
  - selection when several materially different opportunities are proposed
  - material change to an already validated strategic direction

validation:
  - duplicate/cannibalization check completed
  - primary query has one intended destination
  - task-specific prompt is complete enough for a fresh execution
  - no invented personal experience, case, statistic or source
  - GitHub state verified after writes

completion_conditions:
  - article direction explicitly requested or validated
  - Human Item exists or is correctly reused
  - Work Item exists or is correctly reused
  - dedicated task prompt exists or is correctly reused
  - Work Item points to the dedicated prompt
  - Parent relation is correct
  - durable task-specific material is persisted
  - no unnecessary duplicate branch/PR/prompt was created

next_actions:
  - seo-create-article
  - strategy-update when a separate global durable rule was discovered
```

## Durable planning chain

The canonical article planning chain is:

```text
SEO opportunity / user need
        ↓
Human Item - strategic opportunity
        ↓
Work Item - tracking/state/pointers
        ↓
prompts/work-items/article-<N>-<slug>.md - task-specific execution contract
        ↓
seo-create-article
```

Permanent/global rules remain in `strategy/**`, `docs/architecture/**` and shared prompt/template files.

## Human Item role

The Human Item represents the strategic opportunity, not a full execution prompt.

It should capture, as relevant:

- target audience;
- reader/search problem;
- search intent;
- candidate queries;
- strategic rationale;
- conversion destination;
- cluster relationship;
- cannibalization justification;
- validation/planning state.

Reuse an existing matching Human Item instead of creating a wording-level duplicate.

## Work Item role

The Work Item is tracking/state, not a second independently maintained full prompt.

It should identify at minimum:

```text
Parent: #N
expected article path
authoritative task-prompt path
planning state
production branch when known
PR when known
remaining gates / blockers
```

Historical detailed issue content may remain. Do not destructively rewrite history merely for architectural neatness.

## Dedicated task prompt role

The authoritative article-specific execution brief is:

```text
prompts/work-items/article-<work-item-number>-<slug>.md
```

It contains only task-specific material and references permanent directives instead of copying them wholesale.

Typical task-specific information:

- Human Item / Work Item identity;
- target article path;
- intended or existing branch/PR behavior;
- primary/secondary queries and intent;
- differentiated editorial territory;
- user-provided observations/experience/cases;
- task-specific claims to avoid;
- internal-link and publication-state boundaries;
- image constraints;
- deliverables and human gates.

If a global rule changes, persist the global rule in its authoritative file and keep only the consequence for this article in the task prompt.

## Duplicate and cannibalization checks

Before creating anything, search by:

- topic/title;
- primary query and equivalent intent;
- target slug/path;
- cluster;
- related Human/Work Items;
- dedicated prompts;
- active branches/PRs.

Possible outcomes include reuse, update of an existing article, distinct satellite article, or abandonment of the new page.

Closely related keyword variants do not automatically justify separate pages.

## Human input

Ask only for information that materially improves originality, accuracy, positioning or safety and cannot be derived reliably from durable project state or external research.

Examples:

- authentic phrases;
- field observations;
- practitioner/business point of view;
- anonymized case material;
- method wording;
- article-specific claims or framings to avoid.

The user does not choose where this information is stored. Persistence is automatic according to the persistence contract.

## Branch and PR behavior

Planning must inspect existing branch/PR state when relevant.

Do not create a production branch or PR merely because planning ran, unless the project convention explicitly assigns that responsibility to planning.

If an article is already in production/review, reuse its current state and route to the appropriate active capability instead of restarting planning.

## Idempotency

A rerun must reuse valid existing planning state.

Never create a second Human Item, Work Item, prompt, branch or PR for the same intended article simply because the capability was invoked again.

## SEO first, social later

Planning preserves the project rule:

```text
search intent -> useful SEO article -> human validation -> social derivation later
```

Do not distort the SEO structure merely to create future social hooks/posts.

## User-facing completion

After successful planning, report briefly what was created/reused/updated and the next action.

A fresh executor should be launchable with a short instruction pointing to the dedicated task prompt. The executor can be the main ChatGPT conversation or an authorized alternative; OpenAI Work is never mandatory.