# WordPress adapter architecture

Date: 2026-08-31
Status: architecture decision

## Principle

The generic WordPress capability layer must remain provider-neutral while still supporting exact site-specific presentation and content models.

Use this layering:

```text
generic WordPress capability
        ↓
semantic content/preparation contract
        ↓
optional adapter + durable profile
        ↓
SEO Workflow Bridge bounded adapter/transform operation when needed
        ↓
provider/theme/plugin-specific representation
        ↓
WordPress
```

The core owns identity, authorization, source provenance, draft/publication safety, persistence and verification gates.

Adapters own provider-specific representation only.

## Two adapter families

### Presentation adapters

Examples:

- Divi;
- Elementor;
- Bricks;
- Gutenberg patterns;
- theme-specific article layouts.

They answer:

> How must ordinary semantic article text/media be serialized so this site's editor/theme recognizes and renders it correctly?

### Content-model adapters

Examples:

- WooCommerce products/variations;
- ACF field models;
- event plugins;
- LMS course objects.

They answer:

> What additional semantic entities/fields/operations exist beyond an ordinary WordPress article/page?

Do not force content-model semantics into a presentation-only abstraction.

## Presentation precedence

Use this order.

### 1. Native mode

Default when ordinary WordPress/Gutenberg/HTML representation is sufficient.

No provider adapter is required.

### 2. Reference-derived presentation profile

Preferred when exact editor/theme compatibility is required.

The user selects one known-good existing WordPress reference article/template. The workflow reads only the reusable structure/provider metadata required to derive the presentation contract.

Persist profiles under:

```text
wordpress/presentation/profiles/<connection_id>/<profile-id>.json
```

The profile contains reusable structure/configuration, not the reference article's editorial content.

### 3. Adapter-specific overrides

A profile may contain provider-specific presets/styles/IDs as opaque configuration.

The generic core does not interpret those values.

For example, Divi preset IDs belong in the Divi profile for one connection, not in the generic capability contract.

## Why reference-derived profiles

Style aliases alone may be insufficient because page builders can depend on:

- wrapper/module hierarchy;
- hidden post meta;
- provider version markers;
- grid/column information;
- preset IDs;
- provider serialization;
- editor caches/derived state.

A known-good reference proves that a complete representation is accepted by the site's real editor.

Therefore:

```text
reference-derived structure = primary compatibility source
explicit style/preset mappings = optional override
```

## Profile onboarding

When exact presentation compatibility is required and no verified profile exists:

1. identify exact connection/site;
2. select a known-good reference article/template;
3. use bounded read-only Bridge operations such as `reference_read` to obtain required content/meta only;
4. derive a reusable semantic-slot profile;
5. persist it in GitHub;
6. run read-only/probe validation when supported;
7. prepare one real draft when a legitimate pilot/content workflow reaches that step;
8. verify the actual editor/preview with a human;
9. mark the profile reusable only after human verification.

Do not create synthetic durable content solely to test the adapter if an existing legitimate pilot draft/reference can prove it.

## Profile lifecycle

Suggested states:

```text
captured
probe_verified
prepared
human_verified
invalidated
```

Only `human_verified` permits automatic reuse when the profile claims visual/editor fidelity.

A provider/theme/plugin material version change may invalidate the profile and require renewed verification.

## Adapter protocol

An adapter/profile implementation may expose bounded operations such as:

```text
detect
capture_reference
probe
render_or_transform
prepare_extra_fields
verify_machine
verify_human_checkpoint
```

Minimum durable contract:

- adapter ID/version;
- profile schema version;
- connection scope;
- provider/version compatibility when known;
- required Bridge/WordPress capabilities;
- required allowlisted meta/taxonomies;
- input semantic slots;
- output representation;
- machine verification rules;
- whether human verification is mandatory.

## SEO Workflow Bridge extension boundary

Provider-specific transforms should be bounded operations/modules in or behind SEO Workflow Bridge rather than arbitrary execution.

Allowed extension patterns include:

- bounded Bridge controller/adapter operation;
- WordPress hook/filter owned by a reviewed adapter;
- repository-side deterministic renderer;
- durable profile containing opaque provider configuration.

Never add a generic endpoint for:

- arbitrary PHP;
- arbitrary shell;
- arbitrary filesystem access;
- arbitrary database queries.

## Current pilot: Divi

Current durable profile:

```text
wordpress/presentation/profiles/<presentation-profile-id>/blog-article.json
```

It uses adapter:

```text
divi_shortcode_v1
```

The current relay compatibility entrypoint ultimately uses `scripts/wordpress-relay-prepare-v5.py`, which resolves the pinned presentation profile and serializes the semantic article into bounded Divi shortcode modules.

The pilot profile contains site-specific preset/module IDs and reference observations. Those remain pilot configuration, not generic skill behavior.

The optional Bridge `/divi-convert` endpoint is a bounded transform-only adapter for official Divi D4 -> D5 conversion. It is not required by the generic article contract and does not write posts directly.

## Generic manifest direction

Article manifests should describe semantics and reference a profile rather than duplicate provider internals per article.

Conceptually:

```yaml
wordpress:
  post_type: post
  title: ...
  slug: ...
  content:
    mode: repository_file
    presentation_profile_path: wordpress/presentation/profiles/<connection>/<profile>.json
  media: ...
  taxonomies: ...
  post_meta: ...
```

The generic workflow does not need to know what a Divi preset ID means.

## Human verification invariant

For presentation adapters claiming editor fidelity:

```text
machine verification
AND
human editor/preview verification
```

A stored `post_content` value that is technically readable is insufficient if the actual builder/editor opens an empty layout, onboarding screen, broken hierarchy or materially wrong presentation.
