# Direct ChatGPT Skill runtime contract

## Purpose

This document defines how Content Marketing Workflow behaves when the canonical Skill is uploaded or installed directly in ChatGPT. It also defines the boundary between direct ChatGPT execution and the optional Codex plugin distribution.

## Distribution modes

The same workflow may be used in two modes:

1. **Direct ChatGPT Skill**: the user uploads or installs the packaged Skill in ChatGPT and works conversationally.
2. **Codex plugin**: the same Skill is mirrored inside the plugin package so Codex can discover it through the repository marketplace.

The direct Skill is the preferred distribution for users who can install Skills in ChatGPT but cannot import or administer plugin marketplaces. The Codex plugin remains supported for repository-heavy Codex execution and marketplace-based installation.

## Tool availability is runtime state

The Skill is instructions plus packaged resources. It never grants a provider connection by itself.

Before any external read or write, determine whether the active ChatGPT conversation actually exposes the required connected tool. Examples include GitHub repository access, WordPress access, cloud storage and social-provider actions.

- If the tool is available, use it according to the relevant capability contract.
- If the tool is unavailable, do not claim that the external action occurred.
- Do not force Codex merely because the Skill was installed in ChatGPT. Use Codex only when the user chooses it or when the required operation is genuinely unavailable in the active ChatGPT surface.
- Do not ask the user to repeat repository information that an available connected repository tool can resolve safely.

## `/start` in direct ChatGPT

When `/start` is invoked, or the user naturally asks to initialize/resume a project:

1. Load the `start` capability contract.
2. Detect whether durable project configuration already exists in the target project repository or other authoritative project state.
3. If a target repository is identified and GitHub/repository tools are available, inspect it before asking onboarding questions.
4. Resume from verified existing configuration rather than restarting onboarding blindly.
5. Ask only for unresolved values required by the active capability contract.
6. Persist project-specific configuration only in the project repository/state location defined by the persistence contracts, never in this generic Skill package.
7. Keep credentials and raw provider secrets outside Git.

## Initializing a new project repository

When the user wants a fresh project repository for editorial work:

1. Confirm or resolve the target repository.
2. Inspect the repository before writing when repository tools are available.
3. Initialize only the project-specific content/state structure required by the current contracts.
4. Do not copy this product repository, its CI/release machinery, generic plugin source, package manifests or product tests into the project repository.
5. Record environment/site/channel choices as project data, not generic Skill defaults.
6. Run `/status` semantics after initialization and report what is configured, what remains optional and what is blocked by unavailable connections.

## Migrating from an existing project repository

Migration is selective, not a repository clone.

When the user names an old repository and specifies content classes to reuse:

1. Inspect both source and target repositories when tools permit.
2. Inventory candidate files by semantic role, not merely by directory name.
3. Copy only the classes explicitly requested by the user, such as article content, social-post content, related approved media, or research context that remains authoritative.
4. Exclude unrelated product development, generic skill/plugin source, CI/release tooling, credentials, tokens, obsolete integration state and historical implementation experiments unless the user explicitly requests them for reference.
5. Preserve provenance where the persistence contracts require it.
6. Do not treat historical approval/publication evidence as authorization for a new target environment.
7. Present the migration plan or bounded changes for review when a human review gate applies.

## ChatGPT conversational workflow

Direct ChatGPT use is intended to support the full conversational loop when the necessary tools are present:

- onboarding and configuration;
- content inventory and status;
- article planning, drafting and revision;
- social-series planning, post creation and review;
- visual-source handling according to policy;
- repository writes and GitHub workflow operations when connected GitHub tools expose them;
- WordPress/social preparation or publication only through the explicit provider gates.

A repository-heavy task does not automatically require Codex. Prefer the active surface that can complete the task safely with the available tools and the user's requested interaction style.

## Installation artifact behavior

The canonical direct-install source is `skills/content-marketing-workflow/` in the product repository. Release automation packages that folder as a Skill bundle. The bundle contains `SKILL.md` plus all supporting resources required by the workflow.

Uploading only `SKILL.md` can install the core playbook, but supporting contracts/scripts are then unavailable. For this workflow, use the complete packaged Skill whenever possible.

## Consistency requirement

The direct Skill source and the copy embedded in the Codex plugin must remain byte-for-byte equivalent. Repository tests enforce this invariant so fixes made for ChatGPT and fixes made for Codex cannot silently diverge.
