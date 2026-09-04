# ChatGPT Web marketplace import

Status: current distribution guide

## Purpose

This repository is already structured as a supported GitHub plugin marketplace for both Codex marketplace discovery and eligible ChatGPT workspace import.

The canonical manifest is:

```text
.agents/plugins/marketplace.json
```

The canonical plugin source is:

```text
plugins/content-marketing-workflow/
```

A separate Apps SDK application, MCP server or second Web-specific plugin copy is not required merely to make this skill-only plugin available in ChatGPT Web.

## ChatGPT Web import procedure

An eligible ChatGPT workspace administrator imports the marketplace from the repository root:

1. Open `Workspace settings > Plugins`.
2. Select `Add > Import marketplace`.
3. Set `Source` to the repository URL.
4. Leave `Path` empty because the marketplace manifest is at repository root.
5. Use `main` when the workspace should follow approved future updates, or pin a tag/commit when an immutable revision is required.
6. Authorize a GitHub account that can read the repository.
7. Import the marketplace.
8. Review the import result and open the imported `Content Marketing Workflow` plugin.
9. Configure the workspace installation policy for the intended users/roles.

GitHub marketplace import is a workspace-admin operation. The GitHub repository supplies plugin content; ChatGPT workspace settings remain authoritative for installation and authentication policies.

## Synchronization

When the marketplace is imported from a branch, ChatGPT can keep it synchronized with GitHub. An administrator can also request a manual `Sync now` from the marketplace entry in workspace plugin settings.

Repository changes should therefore continue to follow the normal branch/PR/CI/merge process before they are allowed onto the branch synchronized by a workspace.

## Skill-only boundary

Content Marketing Workflow currently contains one primary skill and no mandatory app component.

Do not introduce an Apps SDK wrapper, MCP server or remote application solely to enable Web distribution. Add an app/MCP capability only when the product actually needs a connected external tool or data/action surface that cannot be provided by the installed skill and already available ChatGPT capabilities.

Importing the marketplace does not itself grant access to external services. Optional integrations remain subject to the tools, connected apps, workspace permissions and provider authorizations available to the active user.

## Validation

Repository CI must continue to verify:

- `.agents/plugins/marketplace.json` exists at repository root;
- it exposes exactly the canonical plugin;
- the local marketplace path resolves to `plugins/content-marketing-workflow/`;
- the plugin manifest and primary skill exist there;
- the standalone release builder reads from that same source;
- the Codex marketplace smoke test remains green.

There is no separate ChatGPT Web source tree to validate. The Web workspace importer consumes the same GitHub marketplace structure.
