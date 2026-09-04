# WordPress workflow authority

Date: 2026-09-02
Status: architecture decision

## Decision

For the current pilot and the future single installable Content / Marketing skill, the canonical mechanism for preparing/placing SEO articles in WordPress is the WordPress extension **SEO Workflow Bridge**.

The Bridge is also the canonical mainstream host for LinkedIn OAuth callback/credential storage/direct-publication support when the user has a WordPress site. The normal skill onboarding must not require server administration outside WordPress.

The skill must not treat historical direct-import scripts or a separately deployed Python/WSGI callback as the normal end-user workflow.

Canonical article direction:

```text
validated GitHub article + committed/verified assets
-> WordPress preparation capability
-> SEO Workflow Bridge
-> bridge-managed WordPress draft
-> technical/readback verification
-> human presentation/editor validation
-> optional publication capability
-> immutable publication candidate
-> explicit runtime publish_now gate
-> SEO Workflow Bridge publication operation
-> published readback verification
```

Canonical mainstream LinkedIn direction:

```text
LinkedIn Developer app
-> exact callback exposed by SEO Workflow Bridge on the user's WordPress site
-> OAuth tokens retained by the Bridge, never GitHub/chat
-> authenticated skill/repository request
-> SEO Workflow Bridge LinkedIn adapter
-> LinkedIn API
```

## Companion-plugin onboarding

`docs/architecture/seo-workflow-bridge-onboarding.md` is authoritative for distribution, installation, activation, compatibility checks and resumable onboarding of the companion plugin.

The future skill must include or provide a stable compatible installable ZIP and guide a normal WordPress administrator through:

```text
WordPress administration
-> Extensions / Plugins
-> Ajouter une extension / Add Plugin
-> Téléverser une extension / Upload Plugin
-> install SEO Workflow Bridge ZIP
-> Activer / Activate
-> Réglages / Settings
-> SEO Workflow Bridge
```

The Bridge must be offered:

- during initial onboarding when WordPress support or direct LinkedIn publication is selected;
- later when WordPress article preparation/publication is enabled;
- later when direct LinkedIn publication is enabled.

The user may postpone installation without blocking GitHub article drafting, social creation, visuals, scheduling metadata or manual publishing.

## No server-administration requirement

The mainstream skill must not require the user to configure:

- Python/WSGI/Gunicorn;
- systemd;
- Docker/container hosting;
- Nginx/Apache/HAProxy callback routes;
- shell access;
- custom server-side PHP files outside the plugin;
- a separately hosted OAuth service.

Such mechanisms may exist only as advanced/development adapters. They are not normal onboarding dependencies.

## What becomes legacy or advanced-only

Historical scripts whose principal purpose is to directly construct/import/inject article content into WordPress are retained only as:

- development history;
- troubleshooting/reference material;
- possible controlled fallback for pilot maintenance when explicitly chosen.

They are **not** the canonical implementation of `wordpress-prepare-article` and must not be invoked automatically by the skill merely because they remain in the repository.

The standalone Python/WSGI LinkedIn OAuth runtime may remain as a tested protocol/reference implementation or advanced adapter, but it must not be presented as the mainstream configuration path.

Keeping a legacy or advanced implementation in Git does not make it an active workflow dependency.

## Relay/transport scripts are different

Do not classify every Python file containing `wordpress` as a legacy importer.

Helpers such as `wordpress-relay-*` may implement transport, request validation, manifest preparation, GitHub Actions relay logic or calls to SEO Workflow Bridge. Their status must be assessed against the current Bridge contract.

A relay helper that remains necessary to invoke SEO Workflow Bridge can stay part of the implementation even though direct-import scripts are legacy.

## Generic architecture boundary

`SEO Workflow Bridge` is the current canonical WordPress companion implementation. The generic skill architecture must still preserve semantic boundaries:

```text
generic WordPress capability
-> semantic preparation/publication contract
-> WordPress adapter/transport
-> SEO Workflow Bridge
-> WordPress
```

and for LinkedIn:

```text
generic social-publish capability
-> LinkedIn adapter contract
-> SEO Workflow Bridge LinkedIn capability for mainstream WordPress-backed installs
-> LinkedIn API
```

The business contract must not be tied to one Divi preset, hostname or pilot environment topology.

Presentation-specific behavior (Divi, Gutenberg, Elementor, Bricks, etc.) remains an adapter/profile concern rather than generic SEO workflow logic.

## Preparation authority

When `wordpress.enabled = true`, article preparation should use SEO Workflow Bridge to create/update a managed WordPress draft and verify the resulting WordPress state.

Preparation must remain distinct from publication:

- preparation may create/update a managed draft;
- preparation never implies publication authorization;
- human presentation/editor validation remains required when machine verification is insufficient;
- final assets required by the article must already be `committed + verified` unless the active capability contract explicitly permits an earlier controlled test state.

## Publication authority

`docs/architecture/wordpress-article-publication.md` remains authoritative for publication semantics.

Its Bridge endpoints and operations are consistent with this decision. Publication remains gated by both:

```yaml
wordpress:
  enabled: true
  publish_enabled: true
```

and a separate runtime human authorization bound to the exact immutable candidate:

```text
publish_now
```

`publish_enabled` never means that an article may be published automatically.

LinkedIn connection likewise never implies LinkedIn publication authorization.

## Pilot-specific cloning/scripts

Site-specific operational scripts for cloning, post-clone maintenance, cache handling, indexing switches or other server administration may remain useful to the pilot.

They are outside the generic `wordpress-prepare-article` / `wordpress-publish-article` content contract unless a future explicit architecture decision brings them inside.

## Migration rule

1. treat SEO Workflow Bridge as the canonical current WordPress article path;
2. extend the same companion plugin for the mainstream LinkedIn OAuth/publication path;
3. integrate plugin download/install/activation into skill onboarding;
4. recover historical architecture only where it strengthens the Bridge-based model;
5. classify direct-import scripts as legacy unless a concrete current dependency proves otherwise;
6. keep standalone server-hosted OAuth implementations advanced/development-only;
7. review relay/transport helpers individually instead of deleting them by category;
8. do not revive a script-first or server-admin-first user workflow merely because old documentation/code still describes it.
