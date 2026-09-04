# ChatGPT Web plugin marketplace import

Status: secondary distribution guide

## Preferred ChatGPT path

For ChatGPT users who can upload/install Skills but cannot administer plugin marketplaces, use the direct Skill distribution documented in `docs/chatgpt-direct-skill.md`.

The direct Skill and the Skill embedded in the Codex plugin are generated from the same canonical source and are required to remain byte-for-byte equivalent.

This document applies only to workspaces that expose plugin-marketplace administration to the current administrator role.

## Purpose

This repository remains structured as a GitHub plugin marketplace for Codex marketplace discovery and for eligible ChatGPT workspace plugin import where that administrative surface is available.

The marketplace manifest is:

```text
.agents/plugins/marketplace.json
```

The plugin source is:

```text
plugins/content-marketing-workflow/
```

A separate Apps SDK application, MCP server or second Web-specific plugin implementation is not required merely to distribute the same workflow.

## ChatGPT workspace import procedure

When plugin-marketplace administration is available, an eligible workspace administrator can import the marketplace from the repository root:

1. Open the workspace plugin settings.
2. Select the marketplace import action.
3. Set the source to the repository URL.
4. Leave the path empty because the marketplace manifest is at repository root.
5. Use `main` when the workspace should follow approved future updates, or pin a tag/commit when an immutable revision is required.
6. Authorize repository access when prompted.
7. Import the marketplace.
8. Review the imported `Content Marketing Workflow` plugin.
9. Configure the workspace installation policy for the intended users/roles.

If the current ChatGPT plan/workspace exposes Skills upload but does not expose marketplace import, do not treat that as a product failure and do not route the user to Codex unnecessarily. Install the direct `.skill` artifact instead.

## Synchronization

For marketplace installations that follow a branch, synchronization is managed by the ChatGPT workspace/plugin administration surface. Repository changes still follow branch/PR/CI/merge before reaching the synchronized branch.

Direct Skill installations are updated by uploading/installing the new Skill release artifact.

## Skill boundary

Content Marketing Workflow contains one canonical Skill and no mandatory app component.

Do not introduce an Apps SDK wrapper, MCP server or remote application solely to enable Web distribution. Add an app/MCP capability only when the product genuinely needs a connected external tool or data/action surface that cannot be supplied by available ChatGPT connections.

Neither plugin import nor direct Skill installation grants external-service access. Optional integrations remain subject to the tools, connected apps, workspace permissions and provider authorizations available to the active user.

## Validation

Repository CI verifies both distribution paths:

- canonical direct Skill exists under `skills/content-marketing-workflow/`;
- direct `.skill` and Skill ZIP artifacts can be built and opened;
- plugin Skill mirror is byte-for-byte identical to the canonical Skill;
- `.agents/plugins/marketplace.json` resolves the Codex plugin source;
- the standalone plugin release can be built;
- the Codex marketplace smoke test remains green.
