# WordPress connection transports

Date: 2026-08-31
Status: architecture decision

## Principle

WordPress business capabilities are defined against bounded **SEO Workflow Bridge** operations. Transport is a separate implementation concern.

```text
wordpress-* capability
-> semantic Bridge operation
-> secure transport
-> SEO Workflow Bridge
-> WordPress
```

Changing transport must not change the safety semantics of `wordpress-connect`, `wordpress-prepare-article` or `wordpress-publish-article`.

## Current pilot transport

The current pilot uses:

```text
github_actions_oidc_relay
```

with:

- GitHub-hosted Actions runners;
- `.github/workflows/wordpress-relay.yml`;
- short-lived GitHub Actions OIDC tokens;
- exact trust policy in SEO Workflow Bridge;
- private relay issues/comments as internal machine envelopes;
- no WordPress password or shared relay secret in GitHub.

This transport is operationally validated in the pilot and is the current default there. It is not a universal product requirement.

## Transport resolver

A future installable skill should select among secure transports based on runtime capabilities and the user's environment.

Potential implementations include:

```text
github_actions_oidc_relay
OAuth/MCP or another authenticated application transport
secure direct REST transport to bounded Bridge operations
controlled local integration when explicitly selected
```

The resolver must prefer narrow application-level abilities over broad remote command execution.

Do not permanently pin a third-party connector, ChatGPT plan or client version into the generic contract.

## Required invariants for every transport

Every transport must preserve:

- exact connection/site identity;
- bounded operation names and schemas;
- authenticated caller identity/trust;
- replay/staleness protections where applicable;
- least privilege;
- no secret persistence in GitHub/conversation;
- machine-readable response correlation;
- verification of resulting WordPress state;
- human approval gates owned by the calling capability.

A transport must not expose a generic arbitrary-command path merely to simplify orchestration.

## GitHub Actions OIDC relay

### Architecture

```text
ChatGPT / skill
-> private GitHub relay request
-> GitHub-hosted Actions workflow
-> short-lived GitHub OIDC token
-> SEO Workflow Bridge endpoint
-> bounded WordPress operation
-> machine-readable response
-> GitHub relay response
-> skill verifies/persists result
```

The relay issue/workflow is implementation plumbing, not the human review interface.

### Trust policy

SEO Workflow Bridge must verify the current configured policy, including as applicable:

- JWT signature against GitHub OIDC keys;
- issuer `https://token.actions.githubusercontent.com`;
- exact audience;
- token time validity;
- stable numeric repository ID;
- stable numeric repository owner ID when configured;
- repository name as an additional check when configured;
- expected event;
- exact workflow ref;
- private repository requirement when configured.

### Audience

The current deterministic convention is:

```text
wordpress-relay:<connection_id>
```

It is non-secret and must match both the durable connection profile and Bridge configuration.

### Current relay endpoints

The pilot profile may define:

```text
execute  -> /wp-json/seo-workflow-bridge/v1/execute
prepare  -> /wp-json/seo-workflow-bridge/v1/prepare
publish  -> /wp-json/seo-workflow-bridge/v1/publish
optional adapter transform -> /wp-json/seo-workflow-bridge/v1/divi-convert
```

Endpoint URLs are transport/configuration details. Business capabilities use semantic operations rather than constructing arbitrary WordPress requests.

### Current relay entrypoints

The canonical workflow file is:

```text
.github/workflows/wordpress-relay.yml
```

For preparation, the workflow retains the compatibility entrypoint:

```text
scripts/wordpress-relay-prepare-v3.py
```

That entrypoint deliberately delegates to the current provider-profile implementation in:

```text
scripts/wordpress-relay-prepare-v5.py
```

The numbered names are implementation history and must not be exposed as product-level capability names.

Publication currently uses:

```text
scripts/wordpress-relay-publish-v1.py
```

These relay/orchestration scripts remain active implementation components because they invoke and verify SEO Workflow Bridge. They are not historical direct-import scripts.

## OAuth/MCP or other application transports

An OAuth/MCP-style transport may be used when the runtime actually exposes the bounded abilities required by the workflow and when it can preserve the same Bridge/business safety contract.

Do not assume current product/client support from historical observations. Re-check capabilities when onboarding or reconfiguring such a transport.

A connector that exposes broad WordPress modification but cannot enforce the preparation/publication gates is not automatically equivalent to SEO Workflow Bridge.

## Direct REST/secret-based transport

A direct REST transport is acceptable only when:

- credentials/tokens can be held in a proper runtime secret store;
- a dedicated least-privilege integration identity is used;
- the same bounded Bridge operations are invoked;
- credentials never enter GitHub, prompts, issues or durable content state.

Do not ask the normal end user to paste long-lived WordPress credentials into conversation as the canonical workflow.

## Controlled local execution

A local/server-side integration may be appropriate for a tightly controlled deployment, but it remains a transport implementation.

It must not turn the generic skill into a shell/WP-CLI automation contract and must not bypass SEO Workflow Bridge's managed-content and publication boundaries without a separate explicit architecture decision.

## Transport persistence

Persist only non-secret routing/trust facts needed to resume, for example:

```text
selected_transport
Bridge endpoint URLs
expected site URL
OIDC audience
repository/workflow IDs
capability verification state
last verified timestamp
```

Do not persist bearer tokens, passwords, OAuth tokens, cookies or private keys.

## Failure behavior

A transport failure must be reported as a transport/connection blocker, not silently worked around by switching to historical direct-import scripts.

If another secure transport is available, switching transport is a configuration decision and must preserve the same bounded Bridge capability contract.
