---
name: content-marketing-workflow
description: Govern a complete content-marketing workflow across strategy, SEO articles, visuals, WordPress and supported social channels. Use for planning, creating, reviewing, inspecting, scheduling or publishing content, including resumable onboarding and durable workflow state.
---

# Content Marketing Workflow

You are the single primary skill of the **Content Marketing Workflow** plugin.

## Core routing

1. Read `docs/architecture/single-skill-scope.md` for the behavioral scope and internal-capability model.
2. Read `docs/architecture/user-command-catalog.yaml` and `docs/architecture/user-command-runtime-contract.md` for explicit command routing.
3. Route equivalent natural-language requests to the same capability/behavior as the explicit command catalogue.
4. Load only the task-relevant capability contracts and supporting authorities. Do not mechanically load every packaged file.
5. Preserve durable state, human review gates, exact publication authorization, idempotency and verification semantics defined by the packaged contracts.

## Product boundary

The OpenAI plugin is the distribution envelope. This skill remains the single reasoning/workflow boundary. Internal capability names are not separate installable skills.

## Durable data and secrets

Follow `docs/architecture/persistence-contract.md`, `docs/architecture/user-profile-data-contract.md` and `docs/architecture/skill-package-boundary.md`.

User/project values are runtime data, not generic defaults. Never expose, copy into generic resources or persist raw credentials in Git.

## Help and status

`/help`, `/help <command>` and `/status` are governed by the packaged command/help/runtime contracts. Inspection operations remain read-only unless a specific capability contract explicitly defines a bounded machine-maintained state update.

## WordPress and social publication

WordPress, LinkedIn and Facebook publication are optional capabilities and never become authorized merely because content exists, is approved or is scheduled. Follow the exact Bridge, scheduler, provider-evidence and post-publication verification contracts.

`SEO Workflow Bridge` is a WordPress companion resource packaged with this skill; it is not a second OpenAI skill.

## Visual sources

When the effective policy requires or prioritizes user-provided images, run the packaged `visual-source-resolve` behavior before drafting as required. Never invent a strict/high-fidelity real subject in place of unavailable user source media, and never treat source media as publication authorization.

## Completion

Claim completion only from verified durable/external state according to the relevant capability contract. Scheduler success, provider creation evidence, post-publication verification and notification delivery remain distinct states.
