# Business model extensibility contract

Date: 2026-09-01
Status: recovered architecture decision

## Purpose

The single installable Content / Marketing skill is first validated on the current service-business pilot, but its generic model must not encode assumptions that would require a structural rewrite for another profession, e-commerce, SaaS or a mixed business.

This contract selectively recovers the still-valid business-model decisions from the historical `feature/ai-skills-architecture` branch. It replaces the old broad `AI Content Platform` framing with a narrow architecture rule for the current single-skill product.

## Generic `service`

`service` is a profession-neutral concept.

A service may represent, for example:

- psycho-energetic practice;
- website creation or hosting;
- consulting;
- personal assistance;
- repair;
- plumbing or masonry;
- training;
- maintenance/support;
- local or remote professional services;
- SaaS-related implementation/support services.

Generic workflows reason from site configuration and durable strategy using concepts such as:

```text
offer
audience
problem / need
service area
local vs remote delivery
conversion goal
landing page
proof / trust elements
call to action
```

Profession-specific vocabulary, regulatory constraints, positioning and conversion choices belong to site-specific configuration/strategy, never to the universal meaning of `service`.

## No rigid `service OR product` architecture

The product must not depend on one mutually exclusive site-type switch.

A business can expose several offer kinds at the same time. Examples include:

```text
service
physical product
digital product
hosted service / SaaS
self-hosted software
subscription
licence
support / maintenance
training
installation
```

A Nalyvo-like business may combine hosted SaaS, self-hosted installation, a professional licence and support without becoming a different product architecture.

The exact future configuration schema is intentionally not frozen yet. The invariant is composability: adding a new offer kind must not require reorganizing the repository or replacing the core capability contracts.

## E-commerce and mixed sites

E-commerce is a planned extension of the same core, not a separate unrelated system.

Future capabilities may add WooCommerce/product/category semantics, for example:

```text
woocommerce-connect
seo-create-product
seo-update-product
seo-optimize-category
product-social-extract
catalog-audit
```

They must reuse the same cross-cutting contracts for persistence, context loading, human gates, asset handling, publication verification and generic-vs-site-specific separation.

A mixed site may expose both services and products. Content planning must therefore derive relevant context from the active offer/content type rather than from one permanent global site mode.

## Narrow implementation, extensible contracts

The current implementation remains intentionally focused:

1. service-business pilot;
2. SEO article workflow;
3. visual asset workflow;
4. WordPress preparation/publication;
5. social extraction, visuals and publication state.

Do not implement every future business model prematurely.

However, naming, capability contracts, onboarding data and persistence boundaries must stay compatible with later offer types.

## Generic vs site-specific boundary

Generic capability code/contracts may contain concepts such as:

```text
site
business
offer
audience
intent
conversion goal
service area
content item
product/category when enabled
target platform
publication state
```

They must not hardcode pilot-specific values such as:

- the pilot author's identity as a universal author;
- psycho-energetic terminology;
- one CTA URL;
- one business offer;
- one WordPress topology;
- one social account;
- one builder/theme;
- pilot-specific brand assets.

Those values are loaded from the site's durable configuration and strategy.

## Onboarding consequence

The `start` capability must collect business information as composable offers/capabilities rather than forcing the user into a permanent `service` versus `product` binary.

For the pilot, existing authoritative strategy remains valid and must be reused rather than duplicated into a speculative new schema.

In the canonical distribution source, site/business profile schemas may continue to evolve through versioned contracts as broader business models are validated.

## Architecture test

For every new generic capability, ask:

> Could this capability operate on an unrelated site if the site-specific configuration and strategy were replaced?

If not, move the profession/site-specific assumption out of the generic capability and into durable configuration or strategy.